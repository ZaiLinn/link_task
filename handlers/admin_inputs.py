import logging
from handlers.input_deps import Admin, AdminWithdraw, Client, ConfigData, Message, RPCError, User, UserAuth, decimal, msgNotify, re

logs = logging.getLogger(__name__)


async def _delete_prompt_messages(client, message, msg_id):
    await client.delete_messages(message.chat.id, message_ids=msg_id)


async def _save_config_and_refresh(client, message, admin, config, msg_id, name, value, success_text=None, failure_text="修改失败"):
    if await config.put_config(comm=value, name=name):
        if success_text:
            await msgNotify(msg=message, text=success_text)
        await _delete_prompt_messages(client, message, msg_id)
        await admin.config()
    else:
        await msgNotify(msg=message, text=failure_text)


def _is_integer(text):
    return bool(re.match(r"^[0-9]+$", text))


def _is_decimal(text):
    return bool(re.match(r"^\d+(\.\d+)?$", text))


async def admin_config_reply_input(client: Client, message: Message):
    try:
        user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
        if user[5] not in [1, 2]:
            await message.reply_text("⚠️权限不足,需要管理员权限")
            return

        reply_text = message.reply_to_message.text.split(":")
        prompt = reply_text[0]
        config = ConfigData()
        admin = Admin(Client=client, Msg=message)
        msg_id = [message.id, message.reply_to_message_id, message.reply_to_message.reply_to_message_id]

        text_settings = {
            "请输入机器人名": ("botName", "修改机器人名成功", "修改机器人名失败"),
            "请输入机器人账号": ("botUserName", "修改机器人账号成功", "修改机器人账号失败"),
            "请输入首页欢迎词": ("indexTxt", "修改首页欢迎词成功", "修改首页欢迎词失败"),
            "请输入管理群组": ("adminGroup", "修改管理群组成功", "修改管理群组失败"),
            "请输入客服群组": ("msgGroup", "修改消息群组成功", "修改消息群组失败"),
            "请输入教程频道": ("publicGroup", "修改交流群组成功", "修改交流群组失败"),
        }
        for marker, (name, success_text, failure_text) in text_settings.items():
            if marker in prompt:
                await _save_config_and_refresh(client, message, admin, config, msg_id, name, message.text, success_text, failure_text)
                return

        if "请上传视频介绍" in prompt:
            if message.video:
                if await config.put_config(comm=message.video.file_id, name="video"):
                    await msgNotify(msg=message, text="请上传视频成功")
                    await client.delete_messages(
                        message.chat.id,
                        message_ids=[message.reply_to_message.reply_to_message_id],
                    )
                await admin.config()
            else:
                await msgNotify(msg=message, text="请上传视频")
            return

        integer_settings = {
            "请输入访问限制": ("restrict_limit", 60, "百分比不能大于60秒", "修改访问限制成功", "修改访问限制失败"),
            "请输入用户预警数": ("user_alarm", None, None, "修改用户预警数成功", "修改用户预警数失败"),
            "请输入提现费率": ("WithdrawalRate", 100, "百分比不能大于100", None, "修改费率失败"),
            "请输入商家费率": ("MerchantRate", 100, "百分比不能大于100", None, "修改费率失败"),
        }
        for marker, (name, max_value, max_error, success_text, failure_text) in integer_settings.items():
            if marker in prompt:
                if not _is_integer(message.text):
                    await msgNotify(msg=message, text="格式错误:请输入整数")
                    return
                if max_value is not None and int(message.text) > max_value:
                    await msgNotify(msg=message, text=max_error)
                    return
                await _save_config_and_refresh(client, message, admin, config, msg_id, name, message.text, success_text, failure_text)
                return

        amount_settings = {
            "请输入最低充值金额": ("lowest_balance", "修改最低充值金额失败"),
            "请输入最低发布金额": ("post_amount", "修改最低发布金额失败"),
            "请输入停止推广余额": ("stop_balance", "修改停止推广余额失败"),
            "请输入提醒充值余额": ("remind_balance", "修改提醒充值余额失败"),
            "请输入最低提现金额": ("lowest_withdraw", "修改最低提现金额失败"),
        }
        for marker, (name, failure_text) in amount_settings.items():
            if marker in prompt:
                if not _is_decimal(message.text):
                    await msgNotify(msg=message, text="格式错误:请输入数字")
                    return
                if decimal.Decimal(message.text) < 0:
                    await msgNotify(msg=message, text="金额必须大于0")
                    return
                await _save_config_and_refresh(client, message, admin, config, msg_id, name, message.text, None, failure_text)
                return

        if "请输入商户ID" in prompt:
            if not _is_integer(message.text):
                await msgNotify(msg=message, text="格式错误:请输入整数")
                return
            if len(message.text) < 3:
                await msgNotify(msg=message, text="ID格式不正确")
                return
            await _save_config_and_refresh(client, message, admin, config, msg_id, "OkPay_id", message.text)
            return

        if "请输入商户Token" in prompt:
            if len(message.text) < 10:
                await msgNotify(msg=message, text="token格式不正确")
                return
            await _save_config_and_refresh(client, message, admin, config, msg_id, "OkPay_token", message.text)
    except (RPCError, Exception) as err:
        logs.info(" ".join(str(value) for value in (f"修改错误 {err}",)))


async def admin_withdraw_input(client: Client, message: Message):
    user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
    if user[5] in [1, 2]:
        reply_text = message.reply_to_message.text.split(":")
        withdraw = AdminWithdraw(Client=client, Msg=message)
        msg_id = [message.id, message.reply_to_message_id, message.reply_to_message.reply_to_message_id]
        if "请输入拒绝原因" in reply_text[0]:
            await client.delete_messages(message.chat.id, message_ids=msg_id)
            await withdraw.rejectWithdraw(text=message.text, wid=reply_text[1])
    else:
        await message.reply_text("⚠️权限不足,需要管理群权限")


async def admin_user_input(client: Client, message: Message):
    admin_user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
    if admin_user[5] in [1, 2]:
        reply_text = message.reply_to_message.text.split(":")
        user_view = User(Client=client, Msg=message)
        msg_id = [message.id, message.reply_to_message_id, message.reply_to_message.reply_to_message_id]
        if "请输入用户名或者昵称" in reply_text[0]:
            await client.delete_messages(message.chat.id, message_ids=msg_id)
            await user_view.getUser(search=message.text)
        elif "请输入充值金额" in reply_text[0]:
            try:
                if _is_decimal(message.text):
                    if decimal.Decimal(message.text) > decimal.Decimal(0):
                        price_input = decimal.Decimal(message.text)
                        await client.delete_messages(message.chat.id, message_ids=msg_id)
                        await user_view.pay_user(price=price_input, user_id=reply_text[1])
                    else:
                        await msgNotify(msg=message, text="最低金额必须大于0")
                else:
                    await msgNotify(msg=message, text="格式错误:请输入数字")
            except Exception as err:
                await msgNotify(msg=message, text=f"输入格式错误:{err}")
    else:
        await message.reply_text("⚠️权限不足,需要管理员权限")
