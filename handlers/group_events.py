from handlers.command_deps import ChatJoinRequest, ChatMemberUpdated, Client, LoggerConfig, Message, RPCError, bot_config
from services.group_membership import BorInGroup


com_log = LoggerConfig("com", "logs/main.log").get_logger()


async def join_request(client: Client, message: ChatJoinRequest):
    try:
        if message.invite_link:
            com_log.critical("有私密申请")
            await client.approve_chat_join_request(chat_id=message.chat.id, user_id=message.from_user.id)
    except (RPCError, Exception) as err:
        com_log.exception("加入申请批准错误:%s", err)


async def server_chat_member_update(client: Client, update: ChatMemberUpdated):
    group_handler = BorInGroup(Client=client, Updata=update)
    bot_name = bot_config["botUserName"].replace("@", "")
    if update.invite_link and update.invite_link.creator.username == bot_name:
        await group_handler.invite_group()
    elif update.new_chat_member and update.new_chat_member.user.username == bot_name:
        await group_handler.input_group()
    elif update.old_chat_member and update.old_chat_member.user.username == bot_name:
        await group_handler.out_group()
    elif not update.new_chat_member and update.old_chat_member:
        await group_handler.user_exit_group()


async def GroupMsg(client: Client, update: ChatMemberUpdated):
    com_log.debug("group message event ignored: %s", update)


async def delete_message(client, message):
    com_log.info("删除了消息: %s", message)


async def edited_message(client: Client, edited_message: Message):
    com_log.info("修改了消息: %s", edited_message)


async def disconnect(client: Client):
    com_log.error("客户端断开了链接")
