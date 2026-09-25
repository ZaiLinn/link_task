from data.data import ChatUser, db

class SettlementDate:
    async def get_settlement_list(self,state,OFFSET, LIMIT):
        data = await db.aselect("SELECT task_settlement.id,task_settlement.settlement_time,task_list.title,chat_user.full_name,SUM(task_log.price) AS t_price FROM task_settlement "
                         "LEFT JOIN task_receive ON task_receive.id = task_settlement.receive_id "
                         "LEFT JOIN task_list ON task_list.id=task_receive.task_id "
                         "LEFT JOIN chat_user ON chat_user.id=task_receive.user_id "
                         "LEFT JOIN task_log ON task_log.settlement_id=task_settlement.id "
                         "WHERE task_settlement.state=%s AND appeal=%s  AND task_log.state=0  "
                         "GROUP BY task_settlement.id ORDER BY task_settlement.id DESC "
                         "LIMIT %s  OFFSET %s",
                         (state,(1 if state==5 else 0),LIMIT,OFFSET))
        if data:
            return data
        return []
    async def get_settlement_count(self):
        DB = await db.aselect("SELECT COALESCE(COUNT(DISTINCT ts.id), 0) as all_count,"
                       "COALESCE(SUM(tl.price), 0) as all_price_count,"
                       "COALESCE(COUNT(DISTINCT CASE WHEN ts.state = 6 THEN ts.id END), 0) as ban_count,"
                       "COALESCE(SUM(CASE WHEN ts.state = 6 THEN tl.price ELSE 0 END), 0) as ban_price_count,"
                       "COALESCE(COUNT(DISTINCT CASE WHEN ts.state = 1 THEN ts.id END), 0) as pass_count,"
                       "COALESCE(SUM(CASE WHEN ts.state = 1 THEN tl.price ELSE 0 END), 0) as pass_price_count,"
                       "COALESCE(COUNT(DISTINCT CASE WHEN ts.state = 5 AND appeal=1 THEN ts.id END), 0) as wait_count,"
                       "COALESCE(SUM(CASE WHEN ts.state = 5 AND appeal=1 THEN tl.price ELSE 0 END), 0) as wait_price_count,"
                       "COALESCE(COUNT(DISTINCT CASE WHEN ts.state = 0 THEN ts.id END), 0) as pass_count,"
                       "COALESCE(SUM(CASE WHEN ts.state = 0 THEN tl.price END), 0) as pass_price_count "
                       "FROM task_settlement ts LEFT JOIN task_log tl ON ts.id = tl.settlement_id AND tl.state = 0")
        return DB[0]
    async def get_settlement_info(self,settlement):
        DB = await db.aselect("SELECT task_settlement.*,task_list.title,task_list.unit_price,group_list.title,group_list.url,chat_user.chat_id,chat_user.full_name,"
                       "COALESCE(COUNT(DISTINCT CASE WHEN task_log.state = 0 THEN task_log.id END), 0) as _count ,"
                       "COALESCE(SUM(CASE WHEN task_log.state = 0 THEN task_log.price ELSE 0 END), 0) as price_count ,"
                       "COALESCE(COUNT(DISTINCT CASE WHEN task_log.state = 1 THEN task_log.id END), 0) as _count ,"
                       "COALESCE(SUM(CASE WHEN task_log.state = 1 THEN task_log.price ELSE 0 END), 0) as price_count,"
                       "chat_user.id "
                       "FROM task_settlement LEFT JOIN task_receive ON task_receive.id=task_settlement.receive_id "
                       "LEFT JOIN task_list ON task_list.id=task_receive.task_id LEFT JOIN group_list ON task_list.group_id=group_list.id "
                       "LEFT JOIN chat_user ON chat_user.id = task_receive.user_id LEFT JOIN task_log ON task_log.settlement_id=task_settlement.id "
                       "WHERE task_settlement.id=%s GROUP BY task_settlement.id",(settlement,))
        return DB[0]
    async def get_settlement_log_list(self,settlement,state,OFFSET, LIMIT):
        DB = await db.aselect("SELECT task_log.id,task_log.price,task_log.state,task_log.label,task_log.creation_time,task_user.id,"
                       "task_user.last_name,task_user.first_name,task_user.username FROM task_log "
                       "LEFT JOIN task_user ON task_user.id = task_log.in_user "
                       "WHERE task_log.settlement_id=%s AND task_log.state=%s ORDER BY task_log.id DESC LIMIT %s  OFFSET %s",
                       (settlement,state,LIMIT,OFFSET))
        if DB:
            return DB
        return []
    async def get_task_log_user_count(self,t_user):
        date = await db.aselect("SELECT COUNT(id) FROM task_log WHERE in_user=%s", (t_user,))
        return date[0]
    async def get_confirm_info(self,settlement):
        date = await db.aselect("SELECT  task_settlement.id,task_settlement.settlement_time,task_settlement.user_id,uu.id,uu.chat_id,"
                         "COALESCE(SUM(CASE WHEN task_log.state = 0 THEN task_log.price END), 0) as price_count,task_list.title,wu.chat_id "
                         "FROM task_settlement "
                         "LEFT JOIN task_receive ON task_receive.id=task_settlement.receive_id "
                         "LEFT JOIN chat_user as uu ON task_receive.user_id = uu.id "
                         "LEFT JOIN chat_user as wu ON task_settlement.user_id = wu.id "
                         "LEFT JOIN task_log ON task_log.settlement_id=task_settlement.id "
                         "LEFT JOIN task_list ON task_list.id=task_receive.task_id "
                         "WHERE task_settlement.id=%s",(settlement,))
        if date:
            return date[0]
        return []
    async def get_order_m_balance(self,user_id):
        # 商户订单表获取最后订单
        order = await db.aselect("SELECT balance FROM order_m_list WHERE user_id=%s ORDER BY id DESC LIMIT 1",(user_id,))
        if order:
            return order[0]
        return []

    async def get_order_u_balance(self, user_id):
        # 用户订单表获取最后订单
        order = await db.aselect("SELECT balance FROM order_u_list WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,))
        if order:
            return order[0]
        return []
    async def post_create__order_m(self,**kwargs):
        # 创建商户订单表
        order_id, price, order_type, balance, user_id, link_id, label=\
            kwargs.get('order_id'),kwargs.get('price'),kwargs.get('order_type'),kwargs.get('balance'),kwargs.get('user_id'),kwargs.get('link_id'),kwargs.get('label')
        order_tab = await db.ainsert("INSERT INTO order_m_list (order_id,price,order_type,balance,user_id,link_id,label) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                              (order_id, price, order_type, balance, user_id, link_id, label))
        await ChatUser().put_user_m_balance(user=user_id, balance=balance)
        return order_tab
    async def post_create__order_u(self,**kwargs):
        # 创建用户订单表
        order_id,price,order_type,balance,user_id,link_id,label=\
            kwargs.get('order_id'), kwargs.get('price'), kwargs.get('order_type'), kwargs.get('balance'), \
                kwargs.get('user_id'), kwargs.get('link_id'), kwargs.get('label')
        order_tab = await db.ainsert("INSERT INTO order_u_list (order_id,price,order_type,balance,user_id,link_id,label) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                              (order_id,price,order_type,balance,user_id,link_id,label))
        await ChatUser().put_user_u_balance(user=user_id, balance=balance)
        return order_tab
    async def put_settlement_info(self,**kwargs):
        # 修改审核状态信息
        settlement = kwargs.get("settlement")
        pay_order = kwargs.get("pay_order")
        income_order = kwargs.get("income_order")
        label = kwargs.get("label")
        date =await db.aupdate("UPDATE task_settlement SET state=1,appeal=0,pay_order=%s,income_order=%s,label=%s "
                        "WHERE id=%s",(pay_order,income_order,label,settlement))
        return date
    async def put_reject_settlement_info(self,**kwargs):
        # 拒绝申诉
        settlement = kwargs.get("settlement")
        label = kwargs.get("label")
        date =await db.aupdate("UPDATE task_settlement SET state=6,appeal=0,label=%s "
                        "WHERE id=%s",(label,settlement))
        return date
