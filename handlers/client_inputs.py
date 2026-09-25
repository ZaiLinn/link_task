from handlers.input_deps import Client, LoggerConfig, Message, MyWithdraw, RPCError, Settlement, TaskIndex, UserAuth, bot_config, decimal, msgNotify, re


input_logs = LoggerConfig("input", "logs/main.log").get_logger()


async def _delete_prompt_messages(client, message, message_ids):
    try:
        await client.delete_messages(message.chat.id, message_ids=message_ids)
    except RPCError as err:
        input_logs.debug("delete prompt messages failed chat_id=%s ids=%s err=%s", message.chat.id, message_ids, err)


async def user_task_input(client: Client, message: Message):
    try:
        user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
        if user[4] == 0:
            reply_text = message.reply_to_message.text.split(":")
            task_obj = TaskIndex(Client=client, Msg=message, Data={"user": user})
            msg_id = [message.id, message.reply_to_message_id, message.reply_to_message.reply_to_message_id]
            if "请输入任务标题" in reply_text[0]:
                await _delete_prompt_messages(client, message, msg_id)
                await task_obj.index(search=[message.text])
            elif "请输入提现金额" in reply_text[0]:
                try:
                    pattern = r"^\d+(\.\d+)?$"
                    if re.match(pattern, message.text):
                        if decimal.Decimal(message.text) >= decimal.Decimal(bot_config["lowest_withdraw"]):
                            price_input = decimal.Decimal(message.text)
                            withdraw_obj = MyWithdraw(Client=client, Msg=message, Data={"user": user})
                            await _delete_prompt_messages(client, message, msg_id)
                            await withdraw_obj.withdrawApply(price_input=price_input)
                        else:
                            await msgNotify(msg=message, text=f"最低提现金额必须大于{bot_config['lowest_withdraw']}")
                    else:
                        await msgNotify(msg=message, text="格式错误:请输入数字")
                except Exception as err:
                    await msgNotify(msg=message, text=f"输入格式错误{err}")
        else:
            await message.reply_text("⚠️用户不存在或已被管理员封号")
    except (RPCError, Exception) as err:
        input_logs.exception("user_task_input failed: %s", err)
        await msgNotify(msg=message, text="输入错误:请运行 /start 后重试")


async def close_an_account_input(client: Client, message: Message):
    try:
        user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
        if user[4] == 0:
            reply_text = message.reply_to_message.text.split(":")
            close = Settlement(Client=client, Msg=message, Data={"user": user})
            msg_id = [message.id, message.reply_to_message_id, message.reply_to_message.reply_to_message_id]
            if "请输入拒绝原因" in reply_text[0]:
                await _delete_prompt_messages(client, message, msg_id)
                await close.reject(cause=message.text, receive=reply_text[1])
        else:
            await message.reply_text("⚠️用户不存在或已被管理员封号")
    except (RPCError, Exception) as err:
        input_logs.exception("close_an_account_input failed: %s", err)
        await msgNotify(msg=message, text="输入错误:请运行 /start 后重试")


async def close_merchant_wallet_input(client: Client, message: Message):
    try:
        user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
        if user[4] == 0:
            reply_text = message.reply_to_message.text.split(":")
            wallet = MerchantWallet(Client=client, Msg=message, Data={"user": user})
            msg_id = [message.id, message.reply_to_message_id, message.reply_to_message.reply_to_message_id]
            if "请输入OkPay充值金额" in reply_text[0]:
                pattern = r"^\d+(\.\d+)?$"
                if re.match(pattern, message.text):
                    if decimal.Decimal(message.text) >= decimal.Decimal(bot_config["lowest_balance"]):
                        await wallet.okpay_pay(msg=message.text)
                        await _delete_prompt_messages(client, message, msg_id)
                    else:
                        await msgNotify(msg=message, text=f"充值金额必须大于{bot_config['lowest_balance']}")
                else:
                    await msgNotify(msg=message, text="格式错误:请输入数字")
        else:
            await message.reply_text("⚠️用户不存在或已被管理员封号")
    except (RPCError, Exception) as err:
        input_logs.exception("close_merchant_wallet_input failed: %s", err)
        await msgNotify(msg=message, text="输入错误:请运行 /start 后重试")
