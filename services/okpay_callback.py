import hashlib
import hmac
import json
import os

from core.config import bot_config
from public.logger import LoggerConfig


okpay_logs = LoggerConfig("okpay", "logs/okpay.log").get_logger()


def _compact_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return value


def _okpay_md5(data: dict, merchant_id: str, token: str) -> str:
    """计算 OkPay MD5 签名，在副本上操作，不修改调用方的 dict。"""
    d = {k: v for k, v in data.items() if v is not None and k not in ("sign", "id")}
    d["id"] = merchant_id
    d = dict(sorted(d.items()))
    sign_str = "&".join(f"{k}={v}" for k, v in d.items()) + f"&token={token}"
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()


def _okpay_sign(data, token):
    return _okpay_md5(data, bot_config["OkPay_id"], token)


def verify_okpay_signature(post_json):
    token = bot_config.get("OkPay_token")
    if not token:
        okpay_logs.error("OkPay回调验证失败: OKPAY_TOKEN未配置")
        return False

    signature = post_json.get("sign")
    payload_candidates = [{key: _compact_value(value) for key, value in post_json.items() if key != "sign"}]

    data = post_json.get("data")
    if isinstance(data, dict):
        signature = signature or data.get("sign")
        payload_candidates.append({key: _compact_value(value) for key, value in data.items() if key != "sign"})
        payload_candidates.append(
            {
                key: _compact_value(value)
                for key, value in {**post_json, **data}.items()
                if key not in ("sign", "data")
            }
        )

    if not signature:
        return False

    signature = str(signature).upper()
    return any(hmac.compare_digest(_okpay_sign(payload, token), signature) for payload in payload_candidates)


def verify_callback_token(request):
    callback_token = os.getenv("OKPAY_CALLBACK_TOKEN", "")
    if not callback_token:
        return False
    header_token = request.headers.get("X-OkPay-Token") or request.headers.get("X-Callback-Token")
    return bool(header_token) and hmac.compare_digest(callback_token, header_token)
