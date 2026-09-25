import decimal
import unittest
from unittest.mock import patch

from services.topup_order import TopUpOrder


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        self.connection.queries.append((query, params))
        if "FROM order_pay" in query and "FOR UPDATE" in query:
            self.connection.next_fetch = self.connection.order
        elif "FROM order_m_list" in query and "FOR UPDATE" in query:
            self.connection.next_fetch = self.connection.balance_row
        elif query.startswith("UPDATE order_pay"):
            self.rowcount = self.connection.update_rowcount
        else:
            self.rowcount = 1

    def fetchone(self):
        return self.connection.next_fetch


class FakeConnection:
    def __init__(self, order, balance_row=None, update_rowcount=1):
        self.order = order
        self.balance_row = balance_row
        self.update_rowcount = update_rowcount
        self.next_fetch = None
        self.queries = []
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, dictionary=False):
        self.dictionary = dictionary
        return FakeCursor(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class FakeDb:
    def __init__(self, connection):
        self.connect = connection

    def get_connection(self):
        return True


class TopUpOrderTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirm_okpay_order_commits_ledger_and_balance(self):
        connection = FakeConnection(
            order={"id": 1, "state": 0, "price": decimal.Decimal("12.5"), "user_id": 7},
            balance_row={"balance": decimal.Decimal("2.5")},
        )
        with patch("services.topup_order.db", FakeDb(connection)):
            result = await TopUpOrder().confirm_okpay_order(
                order_id="pay-100",
                transaction_id="tx-200",
                amount="12.5",
                pay_time="now",
                ledger_order_id="ledger-1",
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["before_balance"], decimal.Decimal("2.5"))
        self.assertEqual(result["balance"], decimal.Decimal("15.0"))
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        self.assertTrue(connection.closed)

    async def test_confirm_okpay_order_rejects_amount_mismatch(self):
        connection = FakeConnection(
            order={"id": 1, "state": 0, "price": decimal.Decimal("12.5"), "user_id": 7},
            balance_row={"balance": decimal.Decimal("2.5")},
        )
        with patch("services.topup_order.db", FakeDb(connection)):
            result = await TopUpOrder().confirm_okpay_order(
                order_id="pay-100",
                transaction_id="tx-200",
                amount="10.0",
                pay_time="now",
                ledger_order_id="ledger-1",
            )

        self.assertEqual(result["status"], "amount_mismatch")
        self.assertEqual(result["order_price"], decimal.Decimal("12.5"))
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)

    async def test_confirm_okpay_order_treats_processed_order_as_duplicate(self):
        connection = FakeConnection(
            order={"id": 1, "state": 1, "price": decimal.Decimal("12.5"), "user_id": 7},
            balance_row={"balance": decimal.Decimal("2.5")},
        )
        with patch("services.topup_order.db", FakeDb(connection)):
            result = await TopUpOrder().confirm_okpay_order(
                order_id="pay-100",
                transaction_id="tx-200",
                amount="12.5",
                pay_time="now",
                ledger_order_id="ledger-1",
            )

        self.assertEqual(result["status"], "duplicate")
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)
