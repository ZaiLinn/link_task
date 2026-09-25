import datetime
import re

import emoji
from pyrogram.errors import BadRequest, ChannelPrivate, FloodWait
from pyrogram.types import Message

from core.bot import app
from core.scheduler import scheduler


async def truncate_string(string, length):
    pattern = r":[^:]+:"
    text = re.sub(pattern, "", emoji.demojize(string))
    if len(text) > length:
        return text[:length] + ".."
    return text


async def isPrivileges(chatId, typeG):
    try:
        member = await app.get_chat_member(chatId, "me")
        if member.privileges:
            privileges = member.privileges
            if typeG == "CHANNEL":
                if (
                    privileges.can_delete_messages
                    and privileges.can_post_messages
                    and privileges.can_edit_messages
                    and privileges.can_invite_users
                ):
                    return 0
            elif privileges.can_delete_messages and privileges.can_invite_users:
                return 0
        return 1
    except (FloodWait, BadRequest, ChannelPrivate):
        return 2


async def timeJob(arr):
    await app.delete_messages(arr.get("id"), message_ids=arr.get("message_ids"))


async def msgNotify(msg: Message, text="无", times=5):
    msg_id = await msg.reply_text(text=f"{str(text)} \n({times}秒后删除)")
    scheduler.add_job(
        timeJob,
        trigger="date",
        run_date=datetime.datetime.now() + datetime.timedelta(seconds=times),
        args=({"id": msg_id.chat.id, "message_ids": msg_id.id},),
    )
