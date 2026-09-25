import asyncio
import decimal
import logging
import datetime

from data.data import Card, CHAT_USER_COLUMNS, CHAT_USER_TABLE_COLUMNS, ChatUser, db

logs = logging.getLogger(__name__)

#群操作监控
class BorInGroupData:
    async def getUser(self,id=None,chat_id=None):
        if id:
            user = await db.aselect(f"SELECT {CHAT_USER_COLUMNS} FROM chat_user WHERE id=%s", (id,))
            if user:
                return user[0]
        elif chat_id:
            user = await db.aselect(f"SELECT {CHAT_USER_COLUMNS} FROM chat_user WHERE chat_id=%s", (chat_id,))
            if user:
                return user[0]
        return []
    async def getGroup(self,group_id=None,id=None):
        if group_id:
            group = await db.aselect("SELECT * FROM group_list WHERE group_id=%s", (group_id,))
        else:
            group = await db.aselect("SELECT * FROM group_list WHERE id=%s", (id,))
        if group:
            return group[0]
        return []
    async def get_Group_task(self,id):
        task = await db.aselect(f"SELECT * FROM task_list WHERE group_id=%s", (id,))
        if task:
            return task[0]
        return []
    async def get_Group_task_list(self,id):
        task = await db.aselect(f"SELECT * FROM task_list LEFT JOIN group_list ON group_list.id = task_list.group_id "
                         f"WHERE group_list.group_id=%s AND task_list.state=1 "
                         f"ORDER BY task_list.is_cn, task_list.is_username,task_list.unit_price DESC", (id,))
        if task:
            return task[0]
        return []
    async def postGroup(self,group=None,user=None):
        groupD =await db.ainsert("INSERT INTO group_list (group_id,username,title,type,total_people,url,user_id) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                         (group.id, group.username or "", group.title, group.type.name, group.members_count,group.invite_link, user))
        return groupD
    async def putGroup(self,group,id,user=None):
        groupD= await db.aupdate("UPDATE group_list SET title=%s,username=%s,total_people=%s,url=%s,state=%s,user_id=%s WHERE id=%s",
                          (group.title,group.username or "",group.members_count,group.invite_link,0,user,id))
        return groupD
    async def putGroupState(self,group_id,state):
        groupD = await db.aupdate("UPDATE group_list SET state=%s WHERE group_id=%s",(state, group_id))
        return groupD
    async def get_task(self,id):
        task = await db.aselect(f"SELECT * FROM task_list WHERE id=%s", (id,))
        if task:
            return task[0]
        return []
    async def put_offline_task(self,id,state,label):
        task = await db.aupdate(f"UPDATE task_list SET state=%s,label=%s WHERE id=%s",(state,label,id))
        return task
    async def get_task_receive_link(self,link):
        receive = await db.aselect(f"SELECT task_receive.id,task_list.id,task_list.user_id,chat_user.chat_id,task_list.unit_price,task_list.deduct,task_list.is_username,"
                            f"task_list.is_cn,task_list.is_en,task_list.is_ru,task_list.is_ar,task_list.is_ja,task_list.is_ko,task_list.is_fa,task_list.state,"
                            f"group_list.title,group_list.group_id "
                            f"FROM task_receive LEFT JOIN task_list ON task_list.id=task_receive.task_id "
                            f"LEFT JOIN chat_user ON chat_user.id= task_list.user_id "
                            f"LEFT JOIN group_list ON group_list.id=task_list.group_id "
                            f"WHERE task_receive.link_url=%s AND task_receive.state=0", (link,))
        if receive:
            return receive[0]
        return []
    async def get_task_receive_task(self,task,url,user):
        receive = await db.aselect(f"SELECT task_receive.id,task_list.id,task_list.user_id,chat_user.chat_id,task_list.unit_price,task_list.deduct,task_list.is_username,"
                            f"task_list.is_cn,task_list.is_en,task_list.is_ru,task_list.is_ar,task_list.is_ja,task_list.is_ko,task_list.is_fa,task_list.state,"
                            f"group_list.title,group_list.group_id "
                            f"FROM task_receive LEFT JOIN task_list ON task_list.id=task_receive.task_id "
                            f"LEFT JOIN chat_user ON chat_user.id= task_list.user_id "
                            f"LEFT JOIN group_list ON group_list.id=task_list.group_id "
                            f"WHERE task_receive.task_id=%s AND task_receive.user_id=%s", (task[0],user))
        if receive:
            return receive[0]
        else:
            if await db.ainsert("INSERT INTO task_receive (task_id,user_id,link_url) VALUES(%s,%s,%s)", (task[0], user, url)):
                return await self.get_task_receive_task(task,url,user)
            else:
                return []
    async def get_tinvite_task_user(self,new):
        get_task_user= await db.aselect(f"SELECT * FROM task_user WHERE chat_id=%s" ,(new.user.id,))
        if get_task_user:
            return get_task_user[0]
        else:
            await self.post_invite_task_user(new=new)
            return await self.get_tinvite_task_user(new=new)
    async def post_invite_task_user(self,new):
            invite = await db.ainsert("INSERT INTO task_user (chat_id,username,first_name,last_name,language_code,join_date,photo) "
                               "VALUES(%s,%s,%s,%s,%s,%s,%s)",
                               (new.user.id,new.user.username or '', new.user.first_name or '',new.user.last_name or '',
                                new.user.language_code or '', new.joined_date,'1' if new.user.photo else '0'))
            return invite
    async def put_invite_task_user(self,id,key,value):
        log = await db.aupdate("UPDATE task_user SET state=%s WHERE id=%s", (value, id))
        return log
    async def get_task_log(self,in_id,task):
        date = await db.aselect("SELECT  COALESCE(COUNT(CASE WHEN task_id = %s THEN id END),0) as o_count,"
                         "COALESCE(COUNT(id),0) as a_count FROM task_log WHERE in_user=%s"
                         ,(task,in_id))
        return date[0]
    async def post_task_log(self,in_user,recieve,task,price,state,label):
        invite = await db.ainsert(
            "INSERT INTO task_log (in_user,receive_id,task_id,price,state,label) "
            "VALUES(%s,%s,%s,%s,%s,%s)",
            (in_user,recieve,task,price,state,label))
        return invite
    async def get_task_log_pass(self,receive):
        one_day = datetime.datetime.now().strftime('%Y-%m-%d')
        date = await db.aselect("SELECT COALESCE(COUNT(DISTINCT CASE WHEN task_log.state = 0 THEN task_log.id END), 0) as ban_count,"
                         "COALESCE(COUNT(DISTINCT CASE WHEN task_log.state = 10 THEN task_log.id END), 0) as ban_count "
                         "FROM task_log WHERE task_log.receive_id=%s AND DATE(task_log.creation_time)=%s",(receive,one_day))
        return date[0]
    async def get_user_link_receive(self,in_user):
        date = await db.aselect("SELECT task_log.receive_id,COUNT(task_log.id),chat_user.id,chat_user.chat_id,chat_user.username,chat_user.full_name  FROM task_log "
                         "LEFT JOIN task_receive ON task_receive.id =task_log.receive_id "
                         "LEFT JOIN chat_user ON chat_user.id = task_receive.user_id "
                         "WHERE task_log.in_user=%s GROUP BY task_log.receive_id",(in_user,))
        if date:
            return date
        return []
    async def get_user_link_task(self,in_user):
        date = await db.aselect("SELECT task_log.task_id,COUNT(task_log.id),task_list.title,group_list.group_id,group_list.title,group_list.url  FROM task_log "
                         "LEFT JOIN task_list ON task_list.id=task_log.task_id "
                         "LEFT JOIN group_list ON group_list.id = task_list.group_id "
                         "WHERE task_log.in_user=%s GROUP BY task_log.task_id",(in_user,))
        if date:
            return date
        return []
    async def get_user_balance(self,user):
        data=await db.aselect("SELECT (SELECT balance FROM order_m_list WHERE user_id=%s ORDER BY id DESC LIMIT 1)-COALESCE(SUM(task_log.price), 0) FROM task_log "
                       "LEFT JOIN task_list ON task_list.id = task_log.task_id "
                       "LEFT JOIN task_settlement ON task_log.settlement_id = task_settlement.id "
                       "WHERE task_list.user_id = %s AND task_log.state = 0 "
                       "AND (task_settlement.id IS NULL OR task_settlement.state IN (0,5))",(user,user))
        return data[0][0]
    async def get_task_receive_list(self,task_id):
        list = await db.aselect("SELECT tr.id,tr.state,tr.link_url,cu.chat_id FROM task_receive as tr "
                         "LEFT JOIN chat_user as cu ON cu.id=tr.user_id WHERE tr.task_id=%s",
                         (task_id,))
        if list:
            return list
        return []
    async def get_exit_user_group_info(self,chatid,groupId):
        exit_user = await db.aselect("SELECT task_log.id,task_receive.user_id,task_receive.id FROM task_log "
                              "LEFT JOIN task_user ON task_user.id=task_log.in_user "
                              "LEFT JOIN task_settlement ON task_settlement.id=task_log.settlement_id "
                              "LEFT JOIN task_receive ON task_receive.id=task_log.receive_id "
                              "LEFT JOIN task_list ON task_list.id=task_log.task_id "
                              "WHERE task_user.chat_id=%s AND task_log.state = 0 AND task_list.group_id=%s AND "
                              "(task_settlement.id IS NULL OR task_settlement.state IN (0))",(chatid,groupId))
        if exit_user:
            return exit_user[0]
        return []
    async def get_exit_user_receive_log_rate(self,receive_id):
        rate = await db.aselect(f"SELECT COALESCE(COUNT(CASE WHEN task_log.state = 0 THEN task_log.id END),0)/COALESCE(COUNT(task_log.id),0) FROM task_log "
                         f"LEFT JOIN task_settlement ON task_settlement.id=task_log.settlement_id "
                         f"WHERE task_log.receive_id=%s AND task_settlement.id IS NULL",(receive_id,))
        if rate:
            return rate[0]
        return []
    async def put_exit_user_group_info(self,**kwargs):
        id = kwargs.get("id")
        state = kwargs.get("state")
        label = kwargs.get("label")
        return await db.aupdate("UPDATE task_log SET state=%s,label=%s WHERE id=%s",(state,label,id))
# 结算定时器
class SettlementTimeDate:
    async def get_settlenment_list(self,time):
        date = await db.aselect("SELECT DISTINCT task_receive.id,task_receive.task_id,task_receive.user_id,task_receive.state,task_list.user_id "
                         "FROM task_receive LEFT JOIN task_log ON task_log.receive_id=task_receive.id "
                         "LEFT JOIN task_settlement ON task_log.settlement_id=task_settlement.id LEFT JOIN task_list ON task_list.id = task_receive.task_id "
                         "WHERE DATE(task_log.creation_time)<=%s AND task_settlement.id IS NULL "
                         "GROUP BY task_receive.id,task_list.state HAVING (COUNT(task_log.id) >= 10 OR task_list.state=2) "
                         "AND COUNT(CASE WHEN task_log.state = 0 THEN task_log.id END) >0",
                         (time,))
        if date:
            return date
        return []
    async def post_settlenment_info(self,**kwargs):
        r_id = kwargs.get("r_id")
        m_id = kwargs.get("m_id")
        time_d = kwargs.get("time_d")
        date = await db.ainsert("INSERT INTO task_settlement (receive_id,user_id,settlement_time,label) "
                         "VALUES(%s,%s,%s,'等待结算')",(r_id, m_id, time_d ))
        logs.info(" ".join(str(value) for value in ('创建',date,)))
        return date
    async def get_settlenment_info(self,**kwargs):
        r_id = kwargs.get("r_id")
        m_id = kwargs.get("m_id")
        time_d = kwargs.get("time_d")
        try:
            info = await db.aselect("SELECT * FROM task_settlement WHERE receive_id=%s AND user_id=%s "
                             "AND DATE(settlement_time)=%s",(r_id, m_id, time_d))
            logs.info(" ".join(str(value) for value in ('查询',info,)))
            if info:
                return info[0]
            else:
                if await self.post_settlenment_info(r_id=r_id,m_id=m_id,time_d=time_d):
                    return await self.get_settlenment_info(r_id=r_id,m_id=m_id,time_d=time_d)
                return []
        except Exception as e:
            logs.info(" ".join(str(value) for value in ('结算定时器get_settlenment_info错误',e,)))
    async def put_settlenment_info(self,**kwargs):
        s_id = kwargs.get("s_id")
        r_id = kwargs.get("r_id")
        time_d = kwargs.get("time_d")
        putInfo = await db.aupdate("UPDATE task_log SET settlement_id=%s WHERE receive_id=%s AND settlement_id IS NULL AND DATE(creation_time) <= %s"
                            ,(s_id, r_id , time_d))
        return putInfo
# 超时自动结定时器
class AutomaticDettlementTimeDate:
    async def get_settlenment_list(self,time):
        settList = await db.aselect("SELECT task_settlement.id,task_settlement.receive_id,task_settlement.settlement_time,task_settlement.user_id,"
                             "chat_user.id,chat_user.chat_id,task_list.id,task_list.is_username,task_list.is_cn,group_list.id,group_list.group_id,group_list.title,group_list.type "
                             "FROM task_settlement LEFT JOIN task_receive ON task_receive.id = task_settlement.receive_id "
                             "LEFT JOIN chat_user ON chat_user.id = task_receive.user_id LEFT JOIN task_list ON task_list.id=task_receive.task_id "
                             "LEFT JOIN group_list ON task_list.group_id=group_list.id LEFT JOIN task_log ON task_log.settlement_id=task_settlement.id "
                             "WHERE task_settlement.state=0 AND DATE(task_settlement.settlement_time)<%s "
                             "GROUP BY task_settlement.id ORDER BY task_settlement.id DESC",(time,))
        if settList:
            return settList
        return []
    async def post_create__order_m(self,**kwargs):
        # 创建商户订单表
        order_id, price, order_type, balance, user_id, link_id, label=\
            kwargs.get('order_id'),kwargs.get('price'),kwargs.get('order_type'),kwargs.get('balance'),kwargs.get('user_id'),kwargs.get('link_id'),kwargs.get('label')
        order_tab = await db.ainsert("INSERT INTO order_m_list (order_id,price,order_type,balance,user_id,link_id,label) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                              (order_id, price, order_type, balance, user_id, link_id, label))
        await ChatUser().put_user_m_balance(user=user_id,balance=balance)
        return order_tab
    async def post_create__order_u(self, **kwargs):
        # 用户订单表
        order_id, price, order_type, balance, user_id, link_id, label = \
            kwargs.get('order_id'), kwargs.get('price'), kwargs.get('order_type'), kwargs.get('balance'), \
                kwargs.get('user_id'), kwargs.get('link_id'), kwargs.get('label')
        order_tab = await db.ainsert(
            "INSERT INTO order_u_list (order_id,price,order_type,balance,user_id,link_id,label) VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (order_id, price, order_type, balance, user_id, link_id, label))
        await ChatUser().put_user_u_balance(user=user_id, balance=balance)
        return order_tab
    async def put_settlement_info(self,**kwargs):
        # 修改审核状态信息
        settlement = kwargs.get('settlement')
        state = kwargs.get('state')
        pay_order = kwargs.get('pay_order')
        income_order = kwargs.get('income_order')
        label = kwargs.get('label')
        date =await db.aupdate("UPDATE task_settlement SET state=%s,pay_order=%s,income_order=%s,label=%s "
                        "WHERE id=%s",(state,pay_order,income_order,label,settlement))
        return date
    async def get_settlement_log_rate(self,id):
        rate = await db.aselect("SELECT COALESCE(COUNT(id),0),COALESCE(COUNT(CASE WHEN state = 0 THEN id END),0)/COALESCE(COUNT(id),0) FROM task_log WHERE settlement_id =%s", (id,))
        if rate:
            return rate[0]
        return []
    async def get_log_list(self,**kwargs):
        settlement=kwargs.get('settlement')
        list=await db.aselect("SELECT task_log.id,task_log.in_user,task_user.chat_id FROM task_log "
                       "LEFT JOIN task_settlement ON task_log.settlement_id = task_settlement.id "
                       "LEFT JOIN task_user ON task_log.in_user=task_user.id "
                       "WHERE task_log.settlement_id=%s AND  task_log.state = 0",(settlement,))
        if list:
            return list
        return []
    async def put_task_log_info(self,**kwargs):
        id = kwargs.get("id")
        state = kwargs.get("state")
        label = kwargs.get("label")
        return await db.aupdate("UPDATE task_log SET state=%s,label=%s WHERE id=%s",
                         (state,label,id))
    async def get_price(self,settlement_id):
        price = await db.aselect("SELECT COALESCE(SUM(price), 0) as price_count FROM task_log "
                          "WHERE state =0 AND settlement_id = %s",(settlement_id,))
        return price[0][0]

    async def atomic_settle(self, *, settlement_id, merchant_id, user_id, order_id_m, order_id_u, price):
        """商家扣款、用户入账、结算状态更新在同一个数据库事务中完成，防止中间失败导致资金不一致。"""
        return await asyncio.to_thread(
            self._atomic_settle_sync,
            settlement_id=settlement_id,
            merchant_id=merchant_id,
            user_id=user_id,
            order_id_m=order_id_m,
            order_id_u=order_id_u,
            price=price,
        )

    def _atomic_settle_sync(self, *, settlement_id, merchant_id, user_id, order_id_m, order_id_u, price):
        connection = None
        card = Card()
        try:
            if not card.get_connection():
                logs.error("atomic_settle: 无法获取数据库连接")
                return False
            connection = card.connect
            card.connect = None
            with connection.cursor(dictionary=True) as cursor:
                # 锁定商家最新余额
                cursor.execute(
                    "SELECT balance FROM order_m_list WHERE user_id=%s ORDER BY id DESC LIMIT 1 FOR UPDATE",
                    (merchant_id,),
                )
                row = cursor.fetchone()
                m_balance = decimal.Decimal(str(row["balance"])) if row else decimal.Decimal("0")
                balance_m = m_balance - price

                # 商家扣款记录
                cursor.execute(
                    "INSERT INTO order_m_list (order_id,price,order_type,balance,user_id,label) VALUES(%s,%s,%s,%s,%s,%s)",
                    (order_id_m, price, 1, balance_m, merchant_id, "任务结算"),
                )
                cursor.execute("UPDATE chat_user SET post_balance=%s WHERE id=%s", (balance_m, merchant_id))

                # 锁定用户最新余额
                cursor.execute(
                    "SELECT balance FROM order_u_list WHERE user_id=%s ORDER BY id DESC LIMIT 1 FOR UPDATE",
                    (user_id,),
                )
                row = cursor.fetchone()
                u_balance = decimal.Decimal(str(row["balance"])) if row else decimal.Decimal("0")
                balance_u = u_balance + price

                # 用户入账记录
                cursor.execute(
                    "INSERT INTO order_u_list (order_id,price,order_type,balance,user_id,link_id,label) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (order_id_u, price, 0, balance_u, user_id, order_id_m, "任务结算"),
                )
                cursor.execute("UPDATE chat_user SET task_balance=%s WHERE id=%s", (balance_u, user_id))

                # 结算单标记完成
                cursor.execute(
                    "UPDATE task_settlement SET state=1,pay_order=%s,income_order=%s,label=%s WHERE id=%s",
                    (order_id_m, order_id_u, "超时自动结算成功", settlement_id),
                )
                connection.commit()
                return True
        except Exception as err:
            if connection:
                connection.rollback()
            logs.error(f"atomic_settle 事务回滚:{err}")
            return False
        finally:
            if connection:
                connection.close()

# 检查定时器
class RegularDetectionDate:
    async def get_log_list(self,**kwargs):
        receive=kwargs.get('receive')
        list=await db.aselect("SELECT task_log.id,task_log.in_user,task_user.chat_id FROM task_log "
                       "LEFT JOIN task_settlement ON task_log.settlement_id = task_settlement.id "
                       "LEFT JOIN task_user ON task_log.in_user=task_user.id "
                       "WHERE task_log.receive_id=%s AND  task_log.state = 0 AND "
                       "task_settlement.id IS NULL",(receive,))
        if list:
            return list
        return []
    async def get_task_receive_list(self):
        list = await db.aselect("SELECT task_receive.id,chat_user.username,chat_user.full_name,task_list.id,task_list.title,"
                         "group_list.title,group_list.url,group_list.group_id  "
                         "FROM task_receive LEFT JOIN task_list ON task_list.id=task_receive.task_id "
                         "LEFT JOIN chat_user ON task_receive.user_id=chat_user.id "
                         "LEFT JOIN group_list ON group_list.id=task_list.group_id "
                         "LEFT JOIN task_log ON task_log.receive_id=task_receive.id "
                         "LEFT JOIN task_settlement ON task_settlement.id=task_log.settlement_id "
                         "WHERE task_log.state = 0 AND task_settlement.id IS NULL "
                         "GROUP BY task_receive.id")
        if list:
            return list
        return []
    async def put_task_log_info(self,**kwargs):
        id = kwargs.get("id")
        state = kwargs.get("state")
        label = kwargs.get("label")
        return await db.aupdate("UPDATE task_log SET state=%s,label=%s WHERE id=%s",
                         (state,label,id))
# 任务操作
class TaskOperationDate:
    async def get_task_user_group_info(self,task_id):
        info = await db.aselect("SELECT t.id,t.title,t.state,t.need_review,cu.chat_id,gl.id,gl.group_id,gl.title,gl.state,gl.url FROM task_list as t "
                         "LEFT JOIN chat_user as cu ON cu.id=t.user_id LEFT JOIN group_list as gl ON gl.id=t.group_id "
                         "WHERE t.id=%s",(task_id,))
        if info:
            return info[0]
        return []
    async def get_task_receive_list(self,task_id):
        list = await db.aselect("SELECT tr.id,tr.state,tr.link_url,cu.chat_id FROM task_receive as tr "
                         "LEFT JOIN chat_user as cu ON cu.id=tr.user_id WHERE tr.task_id=%s",
                         (task_id,))
        if list:
            return list
        return []
    async def put_task_state_info(self,id,state,label):
        task = await db.aupdate(f"UPDATE task_list SET state=%s,label=%s WHERE id=%s",(state,label,id))
        return task
# 任务信息定时发送
class TaskSendMsgData:
    async def get_task_user_list(self):
        task_user= await db.aselect(f"SELECT DISTINCT {CHAT_USER_TABLE_COLUMNS} FROM chat_user "
                             "LEFT JOIN group_list ON group_list.user_id=chat_user.id "
                             "LEFT JOIN task_receive ON task_receive.user_id=chat_user.id "
                             "LEFT JOIN task_list ON task_list.id=task_receive.task_id "
                             "WHERE group_list.state=0 AND group_list.out_state=0 AND task_list.state=1 AND task_receive.state=0")
        if task_user:
            return task_user
        return []
    async def get_my_receive_success_list(self,user):
        # 获取用户任务群组信息
        list = await db.aselect("SELECT task_receive.id,group_list.group_id,group_list.title,task_receive.link_url,task_list.id,task_list.need_review FROM task_receive "
                         "LEFT JOIN task_list ON task_list.id=task_receive.task_id "
                         "LEFT JOIN group_list ON group_list.id=task_list.group_id "
                         "WHERE task_receive.user_id=%s AND task_list.state=1 AND task_receive.state=0", (user,))
        if list:
            return list
        return []
    async def get_my_receive_count(self,id,url):
        return await db.aselect(f"SELECT COUNT(task_log.id) FROM task_log "
                         f"LEFT JOIN task_receive ON task_receive.id=task_log.receive_id "
                         f"WHERE task_log.receive_id=%s AND task_receive.link_url=%s",(id,url))

    async def put_my_receive_url(self,id,link_url):
        return await db.aupdate("UPDATE task_receive SET link_url=%s WHERE id=%s",(link_url,id))
    async def get_task_group_list(self,userId):
        task_Group=await db.aselect("SELECT group_list.* FROM group_list WHERE state=0 AND out_state=0 AND user_id=%s",(userId,))
        if task_Group:
            return task_Group
        return []
    async def put_send_task_msgId(self,id,msgId):
        return await db.aupdate("UPDATE group_list SET send_msg=%s WHERE id=%s",(msgId,id))
    async def put_send_group_state(self,id,out_state,state):
        logs.info(" ".join(str(value) for value in (id,out_state,state,)))
        return await db.aupdate("UPDATE group_list SET out_state=%s,state=%s WHERE id=%s",(out_state,state,id))
