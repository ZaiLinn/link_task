import unittest
from unittest.mock import AsyncMock, patch

from services import okpay_callback
from public import web as pay_web


class FakeRequest:
    def __init__(self, headers):
        self.headers = headers


class FakeRedis:
    def __init__(self, lock_result=True):
        self.lock_result = lock_result
        self.deleted = []
        self.set_calls = []

    def set(self, key, value, ex=None, nx=False):
        self.set_calls.append((key, value, ex, nx))
        return self.lock_result

    def delete(self, key):
        self.deleted.append(key)


class OkPayCallbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot_config_patch = patch.dict(
            okpay_callback.bot_config,
            {"OkPay_id": "merchant-1", "OkPay_token": "secret-token"},
            clear=False,
        )
        self.bot_config_patch.start()

    def tearDown(self):
        self.bot_config_patch.stop()

    def test_verify_okpay_signature_accepts_signed_nested_data(self):
        payload = {
            "code": 200,
            "status": "success",
            "data": {
                "unique_id": "pay-100",
                "order_id": "tx-200",
                "amount": "12.5",
            },
        }
        payload["data"]["sign"] = okpay_callback._okpay_sign(payload["data"], "secret-token")

        self.assertTrue(okpay_callback.verify_okpay_signature(payload))

    def test_verify_okpay_signature_rejects_tampered_payload(self):
        data = {"unique_id": "pay-100", "order_id": "tx-200", "amount": "12.5"}
        payload = {"code": 200, "status": "success", "data": {**data, "sign": okpay_callback._okpay_sign(data, "secret-token")}}
        payload["data"]["amount"] = "13.5"

        self.assertFalse(okpay_callback.verify_okpay_signature(payload))

    def test_verify_callback_token_uses_constant_time_header_match(self):
        with patch.dict(okpay_callback.os.environ, {"OKPAY_CALLBACK_TOKEN": "callback-secret"}, clear=False):
            self.assertTrue(okpay_callback.verify_callback_token(FakeRequest({"X-OkPay-Token": "callback-secret"})))
            self.assertFalse(okpay_callback.verify_callback_token(FakeRequest({"X-OkPay-Token": "wrong"})))

    async def test_okpay_order_ignores_duplicate_callback_before_db_write(self):
        fake_redis = FakeRedis(lock_result=False)
        fake_topup = AsyncMock()
        payload = {
            "code": 200,
            "status": "success",
            "data": {
                "unique_id": "pay-100",
                "order_id": "tx-200",
                "amount": "12.5",
                "pay_user_id": 12345,
            },
        }

        with patch.object(pay_web, "redis_client", fake_redis), patch.object(pay_web, "TopUpOrder", return_value=fake_topup):
            await pay_web.okPay_order(payload)

        self.assertEqual(fake_redis.set_calls, [("okpay:callback:pay-100:tx-200", "1", 300, True)])
        fake_topup.confirm_okpay_order.assert_not_called()
