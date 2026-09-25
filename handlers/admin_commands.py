from handlers.command_deps import CallbackQuery, Client, LoggerConfig, Message, RPCError, UserAuth, datetime, db, msgNotify, redis_client, router
from services.settlement import AutomaticDettlementTime, SettlementTime
from views.admin.index import Admin


com_log = LoggerConfig("com", "logs/main.log").get_logger()


async def admin_callback_query_router(client: Client, query: CallbackQuery):
    user = await UserAuth(Msg=query.message).auth(FromUser=query.from_user)
    if user and user[5] in [1, 2]:
        try:
            com_log.critical(query.data)
            await router.route(query.data, client, query, Data={"user": user})
        except ValueError as err:
            com_log.error(f"错误:{err}")
    else:
        await query.message.reply_text("⚠️权限不足,需要管理员权限")


async def admii_command(client: Client, message: Message):
    name = f"user{message.from_user.id}"
    redis_client.delete(name)
    user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
    if user[5] in [1, 2]:
        try:
            admin = Admin(Client=client, Msg=message, Data={"user": user})
            await admin.index()
        except (RPCError, Exception) as err:
            com_log.error(f"后台管理错误:{err}")
    else:
        await message.reply_text("⚠️权限不足,需要管理员权限")


async def admii_addDate(client: Client, message: Message):
    com_log.critical("添加数据")
    name = f"user{message.from_user.id}"
    redis_client.delete(name)
    user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
    if user[5] in [1, 2]:
        try:
            com_log.info("add data command: %s", message.command)
            where_str = " "
            where_params = []
            if len(message.command) == 1:
                return await msgNotify(msg=message, text="参数错误")
            elif len(message.command) > 2:
                hours = [int(hour) for hour in message.command[2].split("-")]
                if any(hour < 0 or hour > 24 for hour in hours):
                    return await msgNotify(msg=message, text="小时参数错误")
                if len(hours) > 1:
                    where_str = " AND HOUR(creation_time) >= %s AND HOUR(creation_time) < %s"
                    where_params.extend([hours[0], hours[1]])
                else:
                    where_str = " AND HOUR(creation_time) = %s "
                    where_params.append(hours[0])

            success = int(message.command[1])
            if success <= 0 or success > 10000:
                return await msgNotify(msg=message, text="数量参数错误")
            fail = int(success / 0.4) - success
            com_log.critical(f"{success}-{fail}")
            add_logs = db.select(
                "SELECT * FROM (SELECT * FROM (SELECT * FROM task_log "
                f"WHERE DATE(creation_time) = DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND state=0 {where_str} "
                "ORDER BY RAND() LIMIT %s) subquery1 "
                "UNION ALL SELECT * FROM (SELECT * FROM task_log "
                f"WHERE DATE(creation_time) = DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND state=1 {where_str} "
                "ORDER BY RAND() LIMIT %s) subquery2) final_result "
                "ORDER BY creation_time",
                tuple(where_params + [success] + where_params + [fail]),
            )
            com_log.critical(len(add_logs))
            if add_logs:
                for add_log in add_logs:
                    c_time = add_log[8] + datetime.timedelta(days=1)
                    db.insert(
                        "INSERT INTO task_log (in_user,receive_id,task_id,price,state,label,creation_time) "
                        "VALUES(%s,%s,%s,%s,%s,%s,%s)",
                        (add_log[1], 834, 170, add_log[4], add_log[5], add_log[6], c_time),
                    )
            com_log.critical("加数据结束")
        except (RPCError, Exception) as err:
            com_log.exception("后台结算错误:%s", err)
    else:
        await message.reply_text("⚠️权限不足,需要管理员权限")


async def admii_js(client: Client, message: Message):
    name = f"user{message.from_user.id}"
    redis_client.delete(name)
    user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
    if user[5] in [1, 2]:
        try:
            await SettlementTime()
        except (RPCError, Exception) as err:
            com_log.error(f"后台结算错误:{err}")
    else:
        await message.reply_text("⚠️权限不足,需要管理员权限")


async def admii_csjs(client: Client, message: Message):
    name = f"user{message.from_user.id}"
    redis_client.delete(name)
    user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
    if user[5] in [1, 2]:
        try:
            await AutomaticDettlementTime()
        except (RPCError, Exception) as err:
            com_log.error(f"后台结算错误:{err}")
    else:
        await message.reply_text("⚠️权限不足,需要管理员权限")
