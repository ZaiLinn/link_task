from data.data import ChatUser, db


def _in_clause(value, allowed):
    values = allowed.get(value, allowed[-1])
    placeholders = ",".join(["%s"] * len(values))
    return placeholders, values


PAY_STATES = {
    -1: (0, 1),
    0: (0,),
    1: (1,),
}

ORDER_TYPES = {
    -1: (0, 1),
    0: (0,),
    1: (1,),
}


class AdminWalletDate:
    async def get_pay_list(self,**kwargs):
        LIMIT, OFFSET, state = kwargs.get('LIMIT'),kwargs.get('OFFSET'),kwargs.get('state')
        state_sql, state_params = _in_clause(state, PAY_STATES)
        pay_list = await db.aselect(f"SELECT order_pay.id,order_pay.price,order_pay.pyt_type,order_pay.state,order_pay.creation_time,chat_user.full_name "
                             f"FROM order_pay LEFT JOIN chat_user ON chat_user.id=order_pay.user_id "
                  f"WHERE order_pay.state in ({state_sql}) ORDER BY order_pay.id DESC LIMIT %s OFFSET %s",
                  (*state_params,LIMIT,OFFSET))
        if pay_list:
            return pay_list
        return []
    async def get_pay_count(self,**kwargs):
        state=kwargs.get('state')
        state_sql, state_params = _in_clause(state, PAY_STATES)
        pay_count = await db.aselect(f"SELECT COALESCE(COUNT(CASE WHEN order_pay.state in ({state_sql}) THEN order_pay.id END), 0) as wait_count,"
                              "COALESCE(SUM(order_pay.price), 0) as total_count,"
                              "COALESCE(SUM(CASE WHEN order_pay.state=1 THEN order_pay.price END), 0) as secc_count,"
                              "COALESCE(SUM(CASE WHEN order_pay.state=0 THEN order_pay.price END), 0) as fail_count "
                              "FROM order_pay", state_params)
        return pay_count[0]
    async def get_pay_info(self,id):
        info = await db.aselect("SELECT order_pay.*,chat_user.chat_id,chat_user.username,chat_user.full_name,order_m_list.order_id,order_m_list.price,order_m_list.balance FROM order_pay "
                         "LEFT JOIN chat_user ON chat_user.id=order_pay.user_id LEFT JOIN order_m_list ON order_m_list.link_id=order_pay.order_id AND order_pay.user_id=order_m_list.user_id "
                         "WHERE order_pay.id=%s",(id,))
        if info:
            return info[0]
        return []
    async def get_order_m_list(self,**kwargs):
        LIMIT, OFFSET,order_type = kwargs.get('LIMIT'), kwargs.get('OFFSET'),kwargs.get('order_type')
        order_type_sql, order_type_params = _in_clause(order_type, ORDER_TYPES)
        order = await db.aselect(f"SELECT order_m_list.id,order_m_list.price,order_m_list.order_type,order_m_list.label,chat_user.full_name FROM order_m_list "
                          f"LEFT JOIN chat_user ON chat_user.id = order_m_list.user_id "
                          f"WHERE order_m_list.order_type in ({order_type_sql}) ORDER BY order_m_list.id DESC LIMIT %s  OFFSET %s",
                          (*order_type_params,LIMIT,OFFSET))
        if order:
            return order
        return []
    async def get_order_m_count(self, **kwargs):
        order_type = kwargs.get('order_type')
        order_type_sql, order_type_params = _in_clause(order_type, ORDER_TYPES)
        count = await db.aselect(f"SELECT IFNULL((SELECT COUNT(id) FROM order_m_list WHERE order_type in ({order_type_sql})),0) AS a_count,"
                          "IFNULL((SELECT SUM(post_balance) FROM chat_user),0) AS s_count",
                          order_type_params)
        return count[0]
    async def get_order_m_info(self,id):
        info = await db.aselect("SELECT order_m_list.id,order_m_list.order_id,order_m_list.price,order_m_list.order_type,order_m_list.balance,"
                         "order_m_list.user_id,order_m_list.link_id,order_m_list.label,order_m_list.creation_time,"
                         "chat_user.chat_id,chat_user.username,chat_user.full_name FROM order_m_list LEFT JOIN chat_user ON chat_user.id=order_m_list.user_id "
                         "WHERE order_m_list.id=%s",(id,))
        if info:
            return info[0]
        return []
    async def get_order_m_pay_info(self,order_id,user):
        info = await db.aselect("SELECT id,user_id,order_id,price,transaction_id,pyt_type,state,creation_time,pay_time "
                         "FROM order_pay WHERE order_id=%s AND user_id=%s",(order_id,user))
        if info:
            return info[0]
        return []
    async def get_order_m_jie_info(self,order_id):
        jie_info =await db.aselect("SELECT task_settlement.id,task_settlement.income_order,task_settlement.settlement_time,task_list.title,task_list.unit_price,task_receive.link_url,chat_user.full_name FROM task_settlement "
                            "LEFT JOIN task_receive ON task_receive.id=task_settlement.receive_id LEFT JOIN chat_user ON chat_user.id=task_receive.user_id "
                            "LEFT JOIN task_list ON task_list.id=task_receive.task_id WHERE task_settlement.pay_order=%s",(order_id,))
        if jie_info:
            return jie_info[0]
        return []
    async def get_order_u_list(self,**kwargs):
        LIMIT, OFFSET,order_type = kwargs.get('LIMIT'), kwargs.get('OFFSET'),kwargs.get('order_type')
        order_type_sql, order_type_params = _in_clause(order_type, ORDER_TYPES)
        order = await db.aselect(f"SELECT order_u_list.id,order_u_list.price,order_u_list.order_type,order_u_list.label,chat_user.full_name FROM order_u_list "
                          f"LEFT JOIN chat_user ON chat_user.id = order_u_list.user_id "
                          f"WHERE order_u_list.order_type in ({order_type_sql}) ORDER BY order_u_list.id DESC LIMIT %s  OFFSET %s",
                          (*order_type_params,LIMIT,OFFSET))
        if order:
            return order
        return []
    async def get_order_u_count(self, **kwargs):
        order_type = kwargs.get('order_type')
        order_type_sql, order_type_params = _in_clause(order_type, ORDER_TYPES)
        count = await db.aselect(f"SELECT IFNULL((SELECT COUNT(id) FROM order_u_list WHERE order_type in ({order_type_sql})),0) AS a_count,"
                          "IFNULL((SELECT SUM(task_balance) FROM chat_user),0) AS s_count",
                          order_type_params)
        return count[0]
    async def get_order_u_info(self,id):
        info = await db.aselect("SELECT order_u_list.id,order_u_list.order_id,order_u_list.price,order_u_list.order_type,order_u_list.balance,"
                         "order_u_list.user_id,order_u_list.link_id,order_u_list.label,order_u_list.creation_time,"
                         "chat_user.chat_id,chat_user.username,chat_user.full_name FROM order_u_list LEFT JOIN chat_user ON chat_user.id=order_u_list.user_id "
                         "WHERE order_u_list.id=%s",(id,))
        if info:
            return info[0]
        return []
    async def get_order_u_jie_info(self,order_id):
        jie_info =await db.aselect("SELECT task_settlement.id,task_settlement.pay_order,task_settlement.settlement_time,task_list.title,task_list.unit_price,task_receive.link_url,chat_user.full_name FROM task_settlement "
                            "LEFT JOIN task_receive ON task_receive.id=task_settlement.receive_id LEFT JOIN chat_user ON chat_user.id=task_receive.user_id "
                            "LEFT JOIN task_list ON task_list.id=task_receive.task_id WHERE task_settlement.income_order=%s",(order_id,))
        if jie_info:
            return jie_info[0]
        return []
    async def get_order_u_withdraw_info(self,order_id):
        ti_info =await db.aselect("SELECT id,user_id,price,state,u_order,label,handling_fee,creation_time,pay_time,out_order,pyt_type "
                           "FROM withdraw_list WHERE u_order=%s",(order_id,))
        if ti_info:
            return ti_info[0]
        return []
