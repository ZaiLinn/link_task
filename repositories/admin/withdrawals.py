from data.data import ChatUser, db

class Withdraw:
    async def get_user(self, id):
        user = await db.aselect("SELECT id,chat_id,username,full_name,state,admin,NULL,post_balance,task_balance,creation_time "
                         "FROM chat_user WHERE id=%s", (id,))
        if user:
            return user[0]
        return []

    async def set_user_state(self, id, state):
        return await db.aupdate("UPDATE chat_user SET state=%s WHERE id=%s", (state, id))

    async def get_withdraw_list(self,**kwargs):
        LIMIT = kwargs.get("LIMIT")
        OFFSET = kwargs.get("OFFSET")
        state = kwargs.get("state")
        date = await db.aselect("SELECT wl.id,wl.price,wl.state,wl.creation_time,cu.id,cu.full_name FROM withdraw_list as wl "
                         "LEFT JOIN chat_user cu ON cu.id=wl.user_id "
                         "WHERE wl.state=%s ORDER BY wl.id DESC LIMIT %s OFFSET %s",
                         (state,LIMIT,OFFSET))
        if date:
            return date
        return []
    async def get_withdraw_count(self,**kwargs):
        count = await db.aselect(f"SELECT COALESCE(COUNT(CASE WHEN wl.state = 0 THEN wl.id END), 0) as wait_count,"
                          f"COALESCE(SUM(CASE WHEN wl.state = 0 THEN wl.price END), 0) as wait_price,"
                          f"COALESCE(COUNT(CASE WHEN wl.state = 1 THEN wl.id END), 0) as ok_count,"
                          f"COALESCE(SUM(CASE WHEN wl.state = 1 THEN wl.price  END), 0) as ok_price,"
                          f"COALESCE(COUNT(CASE WHEN wl.state = 2 THEN wl.id END), 0) as reject_count,"
                          f"COALESCE(SUM(CASE WHEN wl.state = 2 THEN wl.price END), 0) as reject_price "
                          f"FROM withdraw_list as wl")
        return count[0]
    async def get_withdraw_info(self,id):
        date = await db.aselect("SELECT withdraw_list.id,withdraw_list.user_id,withdraw_list.price,withdraw_list.state,withdraw_list.u_order,"
                         "withdraw_list.label,withdraw_list.handling_fee,withdraw_list.creation_time,withdraw_list.pay_time,"
                         "withdraw_list.out_order,withdraw_list.pyt_type,chat_user.id,chat_user.chat_id,chat_user.username,"
                         "chat_user.full_name,chat_user.state,chat_user.admin,NULL,chat_user.post_balance,chat_user.task_balance "
                         "FROM withdraw_list LEFT JOIN chat_user ON chat_user.id = withdraw_list.user_id "
                         "WHERE withdraw_list.id=%s",(id,))
        if date:
            return date[0]
        return []
    # 自己流水
    async def get_order_out_list(self, **kwargs):
        LIMIT, OFFSET, user = kwargs.get('LIMIT'), kwargs.get('OFFSET'), kwargs.get('user')
        order = await db.aselect("SELECT id,order_id,price,order_type,balance,user_id,link_id,label,creation_time "
                          "FROM order_u_list WHERE user_id=%s ORDER BY id DESC LIMIT %s  OFFSET %s",
                          (user, LIMIT, OFFSET))
        if order:
            return order
        return []
    async def get_order_out_count(self,**kwargs):
        user = kwargs.get('user')
        my_=await db.aselect(f"SELECT COALESCE((SELECT COUNT(id) FROM order_u_list WHERE user_id=%s),0) AS a_count,"
                      f"COALESCE((SELECT balance FROM order_u_list WHERE user_id=%s ORDER BY id DESC LIMIT 1),0) AS balance_count "
                      ,(user,user))
        return my_[0]
    # 结算记录
    async def get_settlement_list(self, user, OFFSET, LIMIT):
        date = await db.aselect("SELECT task_settlement.id,task_settlement.state,task_settlement.label,task_settlement.pay_order,task_settlement.income_order,task_settlement.settlement_time,"
                         "chat_user.chat_id,chat_user.username,chat_user.full_name,task_list.title,group_list.title,group_list.url,SUM(task_log.price) AS log_price FROM task_settlement "
                         "LEFT JOIN task_receive ON task_receive.id = task_settlement.receive_id LEFT JOIN chat_user ON chat_user.id=task_settlement.user_id "
                         "LEFT JOIN task_list ON task_list.id=task_receive.task_id LEFT JOIN group_list ON group_list.id=task_list.group_id "
                         "LEFT JOIN task_log ON task_log.settlement_id=task_settlement.id WHERE task_receive.user_id=%s  AND task_log.state=0  "
                         "GROUP BY task_settlement.id ORDER BY task_settlement.id DESC LIMIT %s  OFFSET %s",
                            (user, LIMIT, OFFSET))
        if date:
            return date
        return []
    async def get_settlement_count(self,user):
        date = await db.aselect("SELECT COALESCE(COUNT(DISTINCT CASE WHEN ts.state = 6 THEN ts.id END), 0) as ban_count,"
                         "COALESCE(SUM(CASE WHEN ts.state = 6 THEN tl.price ELSE 0 END), 0) as ban_price_count,"
                         "COALESCE(COUNT(DISTINCT CASE WHEN ts.state = 1 THEN ts.id END), 0) as pass_count,"
                         "COALESCE(SUM(CASE WHEN ts.state = 1 THEN tl.price ELSE 0 END), 0) as pass_price_count,"
                         "COALESCE(COUNT(DISTINCT CASE WHEN ts.state = 0 THEN ts.id END), 0) as wait_count,"
                         "COALESCE(SUM(CASE WHEN ts.state = 0 THEN tl.price ELSE 0 END), 0) as wait_price_count,"
                         "COALESCE(COUNT(ts.id), 0) as c_count "
                         "FROM task_settlement ts LEFT JOIN task_log tl ON ts.id = tl.settlement_id AND tl.state = 0 "
                         "LEFT JOIN task_receive ON task_receive.id=ts.receive_id WHERE task_receive.user_id = %s"
                         ,(user,))
        return date[0]
    # 任务记录
    async def get_taskHistory_list(self, user, OFFSET, LIMIT):
        date = await db.aselect("SELECT task_receive.id,task_receive.creation_time,task_list.title,group_list.title,group_list.url,"
                         "COALESCE(COUNT(CASE WHEN task_log.state = 0 THEN task_log.id  END), 0) as c_count,"
                         "COALESCE(COUNT(CASE WHEN task_log.state = 1 THEN task_log.id  END), 0) as s_count"
                         " FROM task_receive LEFT JOIN task_list ON task_list.id = task_receive.task_id "
                         "LEFT JOIN group_list ON group_list.id= task_list.group_id LEFT JOIN task_log ON task_log.receive_id=task_receive.id "
                         "WHERE task_receive.user_id=%s GROUP BY task_receive.id ORDER BY task_receive.id DESC LIMIT %s  OFFSET %s",
                            (user, LIMIT, OFFSET))
        if date:
            return date
        return []
    async def get_taskHistory_count(self,user):
        date = await db.aselect("SELECT COALESCE(COUNT(task_receive.id), 0) as task_count,"
                         "COALESCE(COUNT(DISTINCT CASE WHEN task_log.state = 0 THEN task_log.id END), 0) as pass_count,"
                         "COALESCE(SUM(CASE WHEN task_log.state = 0 THEN task_log.price ELSE 0 END), 0) as pass_price_count,"
                         "COALESCE(COUNT(DISTINCT CASE WHEN task_log.state = 1 THEN task_log.id END), 0) as wait_count,"
                         "COALESCE(SUM(CASE WHEN task_log.state = 1 THEN task_log.price ELSE 0 END), 0) as wait_price_count "
                         "FROM task_receive LEFT JOIN task_log ON task_log.receive_id=task_receive.id "
                         "WHERE task_receive.user_id = %s"
                         ,(user,))
        return date[0]
    async def put_withdraw_consent(self,**kwargs):
        wid,pay_time,pay_type,pay_order,label=kwargs.get('wid'),kwargs.get('pay_time'),kwargs.get('pay_type'),kwargs.get('pay_order'),kwargs.get('label')
        return await db.aupdate("UPDATE withdraw_list SET state=1,payment_time=%s,pay_type=%s,pay_order=%s,label=%s WHERE id=%s",
                         (pay_time,pay_type,pay_order,label,wid))
    # 拒绝
    async def put_withdraw_reject(self,**kwargs):
        wid, pay_time, return_order, label = kwargs.get('wid'), kwargs.get('pay_time'), kwargs.get('return_order'),kwargs.get('label')
        return await db.aupdate("UPDATE withdraw_list SET state=2,payment_time=%s,return_order=%s,label=%s WHERE id=%s",
            (pay_time, return_order, label, wid))
    async def post_create__order_u(self,**kwargs):
        # 用户订单表
        order_id,price,order_type,balance,user_id,link_id,label=\
            kwargs.get('order_id'), kwargs.get('price'), kwargs.get('order_type'), kwargs.get('balance'), \
                kwargs.get('user_id'), kwargs.get('link_id'), kwargs.get('label')
        order_tab = await db.ainsert("INSERT INTO order_u_list (order_id,price,order_type,balance,user_id,link_id,label) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                              (order_id,price,order_type,balance,user_id,link_id,label))
        await ChatUser().put_user_u_balance(user=user_id,balance=balance)
        return order_tab
    async def get_order_u_balance(self,user_id):
        # 用户订单表获取最后订单
        order = await db.aselect("SELECT balance FROM order_u_list WHERE user_id=%s ORDER BY id DESC LIMIT 1",(user_id,))
        if order:
            return order[0]
        return []
