import os

from core.asyncio_compat import ensure_event_loop

ensure_event_loop()

from pyrogram import Client, filters
from pyrogram.handlers import CallbackQueryHandler, ChatJoinRequestHandler, ChatMemberUpdatedHandler, DisconnectHandler, MessageHandler

from handlers.commands import (
    GroupMsg,
    admii_command,
    admin_callback_query_router,
    callback_query_router,
    disconnect,
    id_handler,
    join_request,
    mc_handler,
    role_handler,
    server_chat_member_update,
    start_handler,
    task_handler,
    test_handler,
)
from handlers.input import (
    admin_config_reply_input,
    admin_user_input,
    admin_withdraw_input,
    close_an_account_input,
    close_merchant_wallet_input,
    user_add_publish_input,
    user_edit_publish_input,
    user_task_input,
)


def register_client_handlers(client: Client):
    if os.getenv("ENABLE_TEST_COMMAND", "").strip().lower() in ("1", "true", "yes", "on"):
        client.add_handler(MessageHandler(test_handler, filters.command(["test"])))
    client.add_handler(MessageHandler(id_handler, filters.command(["id"])))
    client.add_handler(MessageHandler(start_handler, filters.command(["start"]) & filters.private))
    client.add_handler(MessageHandler(role_handler, filters.command(["role"]) & filters.private))
    client.add_handler(MessageHandler(task_handler, filters.command(["task"]) & filters.private))
    client.add_handler(MessageHandler(mc_handler, filters.command(["mc"]) & filters.private))

    client.add_handler(CallbackQueryHandler(callback_query_router, filters.create(
        lambda _, __, query: (query.data and query.data.startswith("r/")))))
    client.add_handler(MessageHandler(GroupMsg, filters.group | filters.channel))
    client.add_handler(ChatMemberUpdatedHandler(server_chat_member_update))
    client.add_handler(ChatJoinRequestHandler(join_request))
    client.add_handler(DisconnectHandler(disconnect))

    client.add_handler(MessageHandler(user_task_input, filters.private & filters.reply & filters.create(
        lambda _, __, query: (
                query.reply_to_message.text and query.reply_to_message.text.startswith("🧧")
        )
    )))
    client.add_handler(MessageHandler(user_add_publish_input, filters.private & filters.reply & filters.create(
        lambda _, __, query: (
                query.reply_to_message.text and query.reply_to_message.text.startswith("➕")
        )
    )))
    client.add_handler(MessageHandler(user_edit_publish_input, filters.private & filters.reply & filters.create(
        lambda _, __, query: (
                query.reply_to_message.text and query.reply_to_message.text.startswith("✂️")
        )
    )))
    client.add_handler(MessageHandler(close_an_account_input, filters.private & filters.reply & filters.create(
        lambda _, __, query: (
                query.reply_to_message.text and query.reply_to_message.text.startswith("‼️")
        )
    )))
    client.add_handler(MessageHandler(close_merchant_wallet_input, filters.private & filters.reply & filters.create(
        lambda _, __, query: (
                query.reply_to_message.text and query.reply_to_message.text.startswith("💰")
        )
    )))


def register_admin_handlers(client: Client):
    client.add_handler(MessageHandler(admii_command, filters.private & (filters.command("admin") | filters.regex("⚙管理页面"))))
    client.add_handler(CallbackQueryHandler(admin_callback_query_router, filters.create(
        lambda _, __, query: (query.data and query.data.startswith("a/")))))

    client.add_handler(MessageHandler(admin_config_reply_input, filters.private & filters.reply & filters.create(
        lambda _, __, query: (
                query.reply_to_message.text and query.reply_to_message.text.startswith("📲")
        )
    )))
    client.add_handler(MessageHandler(admin_withdraw_input, filters.private & filters.reply & filters.create(
        lambda _, __, query: (
                query.reply_to_message.text and query.reply_to_message.text.startswith("🪧")
        )
    )))
    client.add_handler(MessageHandler(admin_user_input, filters.private & filters.reply & filters.create(
        lambda _, __, query: (
                query.reply_to_message.text and query.reply_to_message.text.startswith("👨‍💻")
        )
    )))
