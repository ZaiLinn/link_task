import os


def _load_env_file(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _env(name, default=""):
    return os.getenv(name, default)


def _env_int(name, default=0):
    try:
        return int(_env(name, default))
    except (TypeError, ValueError):
        return default


def _env_bool(name, default=False):
    return _env(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


_load_env_file()

mysql_config = {
    'pool_name': 'my_task',
    'pool_size': _env_int('MYSQL_POOL_SIZE', 10),
    'user': _env('MYSQL_USER'),
    'password': _env('MYSQL_PASSWORD'),
    'host': _env('MYSQL_HOST', '127.0.0.1'),
    'port': _env_int('MYSQL_PORT', 3306),
    'database': _env('MYSQL_DATABASE'),
}

redis_config = {
    'host': _env('REDIS_HOST', '127.0.0.1'),
    'port': _env_int('REDIS_PORT', 6379),
    'db': _env_int('REDIS_DB', 0),
    'password': _env('REDIS_PASSWORD') or None,
}

bot_config = {
    "botName": "未配置机器人",
    "botUserName": "未配置Bot",
    "indexTxt": "未配置欢迎文案",
    "video": "未设置",
    "adminGroup": "未设置",
    "msgGroup": "未设置",
    "publicGroup": "未配置",
    "restrict_limit": '60',
    "restrict_time": '5',
    "user_alarm": '5',
    "WithdrawalRate": '0',
    "MerchantRate": '0',
    "lowest_balance": '0.01',
    "post_amount": '100',
    "stop_balance": '10',
    "remind_balance": '20',
    "lowest_withdraw": '0.01',
    "OkPay_id": _env('OKPAY_ID'),
    "OkPay_token": _env('OKPAY_TOKEN'),
    "callback_address": _env('CALLBACK_ADDRESS'),
    "notifyType": '1',
}

cli_obj = {
    "name": _env("BOT_NAME", "LinkTaskBot"),
    "api_id": _env_int("BOT_API_ID"),
    "api_hash": _env("BOT_API_HASH"),
    "bot_token": _env("BOT_TOKEN"),
    "proxy": _env_bool("BOT_PROXY", False),
    "proxyDict": dict(
        scheme=_env("BOT_PROXY_SCHEME", "socks5"),
        hostname=_env("BOT_PROXY_HOST", "127.0.0.1"),
        port=_env_int("BOT_PROXY_PORT", 1080),
    ),
    "session": _env_bool("BOT_SESSION", False),
    "sessionTxt": _env("BOT_SESSION_FILE", "session.txt"),
}


def refresh_secret_config_from_env():
    bot_config["OkPay_id"] = _env("OKPAY_ID")
    bot_config["OkPay_token"] = _env("OKPAY_TOKEN")
    bot_config["callback_address"] = _env("CALLBACK_ADDRESS", bot_config.get("callback_address", ""))
    return bot_config
