from pyrogram import enums

from handlers.command_deps import CallbackQuery, Client, LoggerConfig, Message, RPCError, RestrictAccess, UserAuth, router
from views.client.index import Index
from views.client.publish_index import PublishIndex
from views.client.task_index import TaskIndex


com_log = LoggerConfig("com", "logs/main.log").get_logger()


async def test_handler(client: Client, message: Message):
    com_log.info("test_handler invoked by chat_id=%s", message.chat.id)


async def test_message(client: Client, message: Message):
    try:
        stickers = await client.get_custom_emoji_stickers(custom_emoji_ids=[5328138210381933279])
        com_log.info("test_message chat_id=%s stickers=%s", message.chat.id, stickers)
        _ = enums.ParseMode.HTML
    except Exception as err:
        com_log.exception("test_message failed: %s", err)


async def id_handler(client: Client, message: Message):
    try:
        title = message.chat.title if message.chat.title else f"{message.chat.last_name}{message.chat.first_name}"
        await message.reply_text(text=f"{title}\n您的ID是:{message.chat.id}")
    except Exception as err:
        com_log.exception("id_handler failed: %s", err)


async def start_handler(client: Client, message: Message):
    if await RestrictAccess(Msg=message).limit_check():
        user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
        if user:
            try:
                index = Index(Client=client, Msg=message, Data={"user": user})
                await index.ifRole()
            except (RPCError, Exception) as err:
                com_log.error(f"用户命令错误：{err}")


async def role_handler(client: Client, message: Message):
    if await RestrictAccess(Msg=message).limit_check():
        user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
        if user:
            try:
                task = Index(Client=client, Msg=message, Data={"user": user})
                await task.index()
            except (RPCError, Exception) as err:
                com_log.error(f"用户命令错误：{err}")


async def task_handler(client: Client, message: Message):
    if await RestrictAccess(Msg=message).limit_check():
        user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
        if user:
            try:
                task = TaskIndex(Client=client, Msg=message, Data={"user": user})
                await task.index()
            except (RPCError, Exception) as err:
                com_log.error(f"用户命令错误：{err}")


async def mc_handler(client: Client, message: Message):
    if await RestrictAccess(Msg=message).limit_check():
        user = await UserAuth(Msg=message).auth(FromUser=message.from_user)
        if user:
            try:
                publish = PublishIndex(Client=client, Msg=message, Data={"user": user})
                await publish.index()
            except (RPCError, Exception) as err:
                com_log.error(f"用户命令错误：{err}")


async def callback_query_router(client: Client, query: CallbackQuery):
    if await RestrictAccess(Msg=query.message).limit_check():
        user = await UserAuth(Msg=query.message).auth(FromUser=query.from_user)
        if user:
            try:
                com_log.critical(query.data)
                await router.route(query.data, client, query, Data={"user": user})
            except ValueError as err:
                com_log.error(f"普通路由错误:{err}")
