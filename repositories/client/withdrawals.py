from data.data import ChatUser, db

class MyWithdrawDate:
    async def get_u_balance(self,user):
        bala = await db.aselect("SELECT COALESCE(balance,0) FROM order_u_list WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user,))
        if bala:
            return bala[0][0]
        return []
    async def get_withdraw_user_list(self,**kwargs):
        LIMIT = kwargs.get("LIMIT")
        OFFSET = kwargs.get("OFFSET")
        user = kwargs.get("user")
        state = kwargs.get("state")
        date = await db.aselect("SELECT id,user_id,price,state,u_order,label,handling_fee,creation_time,pay_time,out_order,pyt_type "
                         "FROM withdraw_list WHERE user_id=%s AND state=%s ORDER BY id DESC LIMIT %s OFFSET %s",
                     (user,state,LIMIT,OFFSET))
        if date:
            return date
        return []
    async def get_withdraw_user_count(self,**kwargs):
        user, state = kwargs.get('user'), kwargs.get('state')
        count = await db.aselect("SELECT IFNULL((SELECT balance FROM order_u_list WHERE user_id = %s ORDER BY id DESC LIMIT 1),0) AS a_count,"
                          "IFNULL((SELECT COUNT(id) FROM withdraw_list WHERE user_id=%s AND state=%s),0) AS b_count,"
                          "IFNULL((SELECT SUM(price) FROM withdraw_list WHERE user_id=%s AND state=%s),0) AS b_sum",
                          (user, user, state, user, state))
        return count[0]
    async def post_create_order_u_list(self,**kwargs):
        # 用户订单表
        order_tab = await db.ainsert("INSERT INTO order_u_list (order_id,price,order_type,balance,user_id,link_id,label) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                              (kwargs.get('order_id'),kwargs.get('price'),kwargs.get('order_type'),
                               kwargs.get('balance'),kwargs.get('user_id'),kwargs.get('link_id'),kwargs.get('label')))
        await ChatUser().put_user_u_balance(user=kwargs.get('user_id'),balance=kwargs.get('balance'))
        return order_tab
    async def post_withdraw_list_u(self,**kwargs):
        user_id = kwargs.get("user_id")
        price = kwargs.get("price")
        state = kwargs.get("state")
        link_id = kwargs.get("link_id")
        label = kwargs.get("label")
        handling_fee = kwargs.get("handling_fee")
        withdraw = await db.ainsert("INSERT INTO withdraw_list (user_id,price,state,u_order,label,handling_fee) VALUES(%s,%s,%s,%s,%s,%s)",
                             (user_id,price,state,link_id,label,handling_fee))
        return withdraw
    async def get_withdraw_info(self,id):
        date = await db.aselect("SELECT withdraw_list.id,withdraw_list.user_id,withdraw_list.price,withdraw_list.state,withdraw_list.u_order,"
                         "withdraw_list.label,withdraw_list.handling_fee,withdraw_list.creation_time,withdraw_list.pay_time,"
                         "withdraw_list.out_order,withdraw_list.pyt_type,chat_user.chat_id,chat_user.username,chat_user.full_name,"
                         "order_u_list.id,order_u_list.balance FROM withdraw_list LEFT JOIN chat_user ON chat_user.id = withdraw_list.user_id "
                         "LEFT JOIN order_u_list ON order_u_list.order_id=withdraw_list.u_order "
                         "WHERE withdraw_list.id=%s",(id,))
        if date:
            return date[0]
        return []
