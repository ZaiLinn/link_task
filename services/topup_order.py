import asyncio
import decimal

from data.data import Card, ChatUser, db


class TopUpOrder:
    async def confirm_okpay_order(self, **kwargs):
        return await asyncio.to_thread(self._confirm_sync, **kwargs)

    def _confirm_sync(self, **kwargs):
        order_id = kwargs.get("order_id")
        transaction_id = kwargs.get("transaction_id")
        callback_amount = kwargs.get("amount")
        pay_time = kwargs.get("pay_time")
        ledger_order_id = kwargs.get("ledger_order_id")
        connection = None
        card = Card()
        try:
            if not card.get_connection():
                return {"status": "error", "error": "database connection unavailable"}
            connection = card.connect
            card.connect = None
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT id,state,price,user_id FROM order_pay WHERE order_id=%s AND transaction_id=%s FOR UPDATE",
                    (order_id, transaction_id),
                )
                order_info = cursor.fetchone()
                if not order_info:
                    connection.rollback()
                    return {"status": "missing"}
                if int(order_info.get("state") or 0) != 0:
                    connection.rollback()
                    return {"status": "duplicate"}

                order_price = decimal.Decimal(str(order_info["price"]))
                if callback_amount is not None and decimal.Decimal(str(callback_amount)) != order_price:
                    connection.rollback()
                    return {"status": "amount_mismatch", "order_price": order_price}

                user_id = order_info["user_id"]
                cursor.execute(
                    "SELECT balance FROM order_m_list WHERE user_id=%s ORDER BY id DESC LIMIT 1 FOR UPDATE",
                    (user_id,),
                )
                balance_row = cursor.fetchone()
                before_balance = decimal.Decimal(str(balance_row["balance"])) if balance_row else decimal.Decimal("0")
                balance = before_balance + order_price

                cursor.execute(
                    "UPDATE order_pay SET state=1,pay_time=%s WHERE order_id=%s AND transaction_id=%s AND state=0",
                    (pay_time, order_id, transaction_id),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    return {"status": "duplicate"}

                cursor.execute(
                    "INSERT INTO order_m_list (order_id,price,order_type,balance,user_id,link_id,label) "
                    "VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (ledger_order_id, order_price, 0, balance, user_id, order_id, "okPay充值"),
                )
                cursor.execute(
                    "UPDATE chat_user SET post_balance=%s WHERE id=%s",
                    (balance, user_id),
                )
                connection.commit()
                return {
                    "status": "success",
                    "user_id": user_id,
                    "price": order_price,
                    "before_balance": before_balance,
                    "balance": balance,
                }
        except Exception as err:
            if connection:
                connection.rollback()
            return {"status": "error", "error": str(err)}
        finally:
            if connection:
                connection.close()

    async def get_pay_order_info(self, **kwargs):
        order_id = kwargs.get("order_id")
        transaction_id = kwargs.get("transaction_id")
        order_info = await db.aselect(
            "SELECT id,user_id,order_id,price,transaction_id,pyt_type,state,creation_time,pay_time "
            "FROM order_pay WHERE order_id=%s AND transaction_id=%s AND state=0",
            (order_id, transaction_id),
        )
        return order_info[0] if order_info else []

    async def put_pay_order_state(self, **kwargs):
        pay_time = kwargs.get("pay_time")
        order_id = kwargs.get("order_id")
        transaction_id = kwargs.get("transaction_id")
        return await db.aupdate(
            "UPDATE order_pay SET state=1,pay_time=%s WHERE order_id=%s AND transaction_id=%s AND state=0",
            (pay_time, order_id, transaction_id),
        )

    async def get_order_m_balance(self, user_id):
        order = await db.aselect(
            "SELECT balance FROM order_m_list WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,)
        )
        return order[0][0] if order else []

    async def post_order_m_info(self, **kwargs):
        order_id = kwargs.get("order_id")
        price = kwargs.get("price")
        order_type = kwargs.get("order_type")
        balance = kwargs.get("balance")
        user_id = kwargs.get("user_id")
        link_id = kwargs.get("link_id")
        label = kwargs.get("label")
        await ChatUser().put_user_m_balance(user=user_id, balance=balance)
        return await db.ainsert(
            "INSERT INTO order_m_list (order_id,price,order_type,balance,user_id,link_id,label) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (order_id, price, order_type, balance, user_id, link_id, label),
        )
