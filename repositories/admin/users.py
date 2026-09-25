import logging
from data.data import ChatUser, db

logs = logging.getLogger(__name__)

class UserDate:
    async def get_user_list(self, admin, search=None, limit=10, offset=0):
        where = ""
        params = []
        if search:
            search_value = f"%{search}%"
            where = "AND (BINARY full_name LIKE %s OR BINARY username LIKE %s) "
            params.extend([search_value, search_value])
        user_counts = await db.aselect(
            "SELECT (SELECT COUNT(*) FROM chat_user WHERE admin=%s) AS total_count,"
            "(SELECT COUNT(*) FROM chat_user WHERE admin=0) AS state_count,"
            "(SELECT COUNT(*) FROM chat_user WHERE admin=1) AS admin_count",
            (admin,),
        )
        users = await db.aselect(
            "SELECT id,chat_id,username,full_name,state,admin,NULL,post_balance,task_balance,creation_time "
            "FROM chat_user WHERE admin=%s " + where + "ORDER BY id DESC LIMIT %s OFFSET %s",
            tuple([admin] + params + [limit, offset]),
        )
        return (user_counts[0] if user_counts else (0, 0, 0)), users or []

    async def get_user(self,id):
        user= await db.aselect("SELECT id,chat_id,username,full_name,state,admin,NULL,post_balance,task_balance,creation_time "
                        "FROM chat_user WHERE id=%s",(id,))
        if user:
            return user[0]
        return []
    async def get_user_by_chat_id(self, chat_id):
        user = await db.aselect("SELECT id,chat_id,username,full_name,state,admin,NULL,post_balance,task_balance,creation_time "
                         "FROM chat_user WHERE chat_id=%s", (chat_id,))
        if user:
            return user[0]
        return []
    async def set_admin(self, id, admin):
        return await db.aupdate("UPDATE chat_user SET admin=%s WHERE id=%s", (admin, id))
    async def set_user_state(self, id, state):
        return await db.aupdate("UPDATE chat_user SET state=%s WHERE id=%s", (state, id))
    async def get_order_m_balance(self,user_id):
        # 商户订单表获取最后订单
        order = await db.aselect("SELECT balance FROM order_m_list WHERE user_id=%s ORDER BY id DESC LIMIT 1",(user_id,))
        if order:
            return order[0][0]
        return []
    async def post_order_m_info(self,**kwargs):
        # 创建商户订单表
        order_id, price, order_type, balance, user_id, link_id, label = kwargs.get('order_id'), kwargs.get('price'), kwargs.get('order_type'), kwargs.get(
                    'balance'), kwargs.get('user_id'), kwargs.get('link_id'), kwargs.get('label')
        await ChatUser().put_user_m_balance(user=user_id,balance=balance)
        return await db.ainsert(
                "INSERT INTO order_m_list (order_id,price,order_type,balance,user_id,link_id,label) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (order_id, price, order_type, balance, user_id, link_id, label))
    async def get_check_order_out_list(self, user):
        order = await db.aselect("SELECT id,order_id,price,order_type,balance,user_id,link_id,label,creation_time "
                          "FROM order_u_list WHERE user_id=%s",(user,))
        if order:
            return order
        return []
    async def get_check_order_info(self,order):
        orderD = await db.aselect("SELECT id,order_id,price,order_type,balance,user_id,link_id,label,creation_time "
                           "FROM order_u_list WHERE id=%s ", (order,))
        if orderD:
            return orderD[0]
        return []
    async def put_check_order(self,**kwargs):
        price,balance,label,order_id,user_id=kwargs.get("price"),kwargs.get("balance"),kwargs.get("label"),kwargs.get("order_id"),kwargs.get("user_id")
        logs.info(" ".join(str(value) for value in (label,)))
        await ChatUser().put_user_u_balance(user=user_id, balance=balance)
        return await db.aupdate("UPDATE order_u_list SET price=%s,balance=%s,label=%s WHERE id=%s"
                            ,(price,balance,label,order_id))
    async def get_check_settlenment(self,order):
        settList = await db.aselect("SELECT  task_settlement.id,task_settlement.settlement_time,task_settlement.user_id,chat_user.id,chat_user.chat_id,"
                             "COALESCE(SUM(CASE WHEN task_log.state = 0 THEN task_log.price END), 0) as price_count,"
                             "COUNT(CASE WHEN task_log.state = 1 THEN task_log.id END) AS shibai,task_list.title FROM task_settlement "
                             "LEFT JOIN task_receive ON task_receive.id=task_settlement.receive_id "
                             "LEFT JOIN chat_user ON task_receive.user_id = chat_user.id "
                             "LEFT JOIN task_log ON task_log.settlement_id=task_settlement.id "
                             "LEFT JOIN task_list ON task_list.id=task_receive.task_id "
                             "WHERE task_settlement.income_order=%s GROUP BY task_settlement.id",(order,))
        if settList:
            return settList[0]
        return []
