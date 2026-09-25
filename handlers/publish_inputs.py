from handlers.input_deps import Client, LoggerConfig, Message, PublishDate, PublishList, PublishPostTask, RPCError, UserAuth, msgNotify, re


input_logs = LoggerConfig("input", "logs/main.log").get_logger()


async def _update_publish_field(client, message, reply_text, view, return_method, key, value, error_text="修改失败请联系客服"):
    msg_id = [message.id, message.reply_to_message_id, message.reply_to_message.reply_to_message_id]
    if await PublishDate().put_task_info(id=reply_text[1], key=key, value=value):
        try:
            await client.delete_messages(message.chat.id, message_ids=msg_id)
        except RPCError as err:
            input_logs.debug("delete publish prompt failed chat_id=%s ids=%s err=%s", message.chat.id, msg_id, err)
        await getattr(view, return_method)(task=[reply_text[1]])
    else:
        await msgNotify(msg=message, text=error_text)


async def _handle_publish_input(client, message, view, return_method, min_count_allows_zero=False, min_count_inclusive=False):
    reply_text = message.reply_to_message.text.split(":")
    if "请输入任务标题" in reply_text[0]:
        await _update_publish_field(client, message, reply_text, view, return_method, "title", message.text)
    elif "请输入任务单价" in reply_text[0]:
        pattern = r"^[0-9]+(\.[0-9]+)?$"
        if re.match(pattern, message.text):
            if float(message.text) < 0.01:
                return await msgNotify(msg=message, text="金额不能小于0.01默认值")
            await _update_publish_field(client, message, reply_text, view, return_method, "unit_price", message.text)
        else:
            await msgNotify(msg=message, text="格式错误:请输入数字可以带两位小数")
    elif "请输入任务数量" in reply_text[0]:
        pattern = r"^[0-9]+$"
        if re.match(pattern, message.text):
            count_value = int(message.text)
            min_invalid = count_value <= 1000 if min_count_inclusive else count_value < 1000
            if min_count_allows_zero and count_value == 0:
                min_invalid = False
            if min_invalid:
                return await msgNotify(msg=message, text="数量不能少于默认值最低1000")
            await _update_publish_field(client, message, reply_text, view, return_method, "count", message.text)
        else:
            await msgNotify(msg=message, text="格式错误:请输入整数")
    elif "请输入百分比" in reply_text[0]:
        pattern = r"^[0-9]+$"
        if re.match(pattern, message.text):
            if int(message.text) > 100:
                return await msgNotify(msg=message, text="百分比不能大于100")
            await _update_publish_field(client, message, reply_text, view, return_method, "deduct", message.text)
        else:
            await msgNotify(msg=message, text="格式错误:请输入整数")


async def user_add_publish_input(client: Client, message: Message):
    try:
        user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
        if user[4] == 0:
            publish = PublishPostTask(Client=client, Msg=message, Data={"user": user})
            await _handle_publish_input(client, message, publish, "task_release_form", min_count_allows_zero=True)
        else:
            await message.reply_text("⚠️用户不存在或已被管理员封号")
    except (RPCError, Exception) as err:
        input_logs.exception("user_add_publish_input failed: %s", err)
        await msgNotify(msg=message, text="输入错误:请运行 /start 后重试")


async def user_edit_publish_input(client: Client, message: Message):
    try:
        user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
        if user[4] == 0:
            publish = PublishList(Client=client, Msg=message, Data={"user": user})
            await _handle_publish_input(client, message, publish, "task_info", min_count_inclusive=True)
        else:
            await message.reply_text("⚠️用户不存在或已被管理员封号")
    except (RPCError, Exception) as err:
        input_logs.exception("user_edit_publish_input failed: %s", err)
        await msgNotify(msg=message, text="输入错误:请运行 /start 后重试")
