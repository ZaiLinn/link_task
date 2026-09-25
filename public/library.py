"""Deprecated compatibility layer for the old fleet-promotion module.

The active bot flow uses service modules under ``services/``.  The previous
implementation in this file mixed scheduling, Telegram API calls, raw SQL, and
legacy fleet-promotion behavior that is no longer wired into the router.
"""

import datetime
import logging

from pyrogram.errors import BadRequest, ChannelPrivate, FloodWait
from core.bot import app
from core.scheduler import scheduler
from services.telegram_utils import isPrivileges as check_bot_privileges


logs = logging.getLogger(__name__)


async def isPrivileges(chatId):
    try:
        group_type = await app.get_chat(chatId)
        status = await check_bot_privileges(chatId=chatId, typeG=group_type.type.name)
        return status, group_type if status in (0, 1) else {}
    except (FloodWait, BadRequest, ChannelPrivate):
        return 2, {}


async def timeJob(arr):
    await app.delete_messages(arr.get("id"), message_ids=arr.get("message_ids"))


async def msgNotify(id=None, text="无", times=2):
    msg_id = await app.send_message(
        chat_id=id,
        text=f"{str(text)} \n({times}秒后删除)",
        disable_web_page_preview=True,
    )
    scheduler.add_job(
        timeJob,
        trigger="date",
        run_date=datetime.datetime.now() + datetime.timedelta(seconds=times),
        args=({"id": msg_id.chat.id, "message_ids": msg_id.id},),
    )


async def trafficStatistics():
    logs.warning("public.library.trafficStatistics is deprecated and disabled")
    return False


async def examineOpponent(chatId):
    logs.warning("public.library.examineOpponent is deprecated and disabled")
    return False


async def requestFleetGroupInfo(group_id, link_group):
    logs.warning("public.library.requestFleetGroupInfo is deprecated and disabled")
    return False


async def marshalling(group_list=None, group_chat=None, fleet=None):
    logs.warning("public.library.marshalling is deprecated and disabled")
    return []


async def convoyDriving():
    logs.warning("public.library.convoyDriving is deprecated and disabled")
    return False


__all__ = [
    "isPrivileges",
    "msgNotify",
    "timeJob",
    "trafficStatistics",
    "examineOpponent",
    "requestFleetGroupInfo",
    "marshalling",
    "convoyDriving",
]
