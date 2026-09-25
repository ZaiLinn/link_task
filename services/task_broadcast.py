import asyncio

from pyrogram.errors import RPCError

from core.config import bot_config
from public.logger import LoggerConfig
from repositories.task_data import TaskSendMsgData
from services.task_lifecycle import TaskOperation


broadcast_logs = LoggerConfig("task_broadcast", "logs/task_broadcast.log").get_logger()


async def get_task_text(app, my_receive):
    try:
        task_send_data = TaskSendMsgData()
        count = await task_send_data.get_my_receive_count(id=my_receive[0], url=my_receive[3])
        if count[0][0] > 0:
            link = await app.create_chat_invite_link(
                chat_id=my_receive[1],
                creates_join_request=True if my_receive[5] == 1 else False,
            )
            await task_send_data.put_my_receive_url(id=my_receive[0], link_url=link.invite_link)
            await app.revoke_chat_invite_link(chat_id=my_receive[1], invite_link=my_receive[3])
            return [my_receive[2], link.invite_link]
        return [my_receive[2], my_receive[3]]
    except RPCError:
        task_operation = TaskOperation(Client=app, Task=my_receive[4])
        await task_operation.offline(Text=f"⚠️ 频道:{my_receive[2]}) \n无创建链接权限已下架任务。。")
        return False


async def TaskSendMsg(**kwargs):
    app = kwargs.get("client")
    broadcast_logs.critical("定时任务推送开始")
    task_send_data = TaskSendMsgData()
    if send_user := await task_send_data.get_task_user_list():
        for user in send_user:
            broadcast_logs.critical(f"发送用户：{user}")
            if groups := await task_send_data.get_task_group_list(userId=user[0]):
                text = [f"**⛩️[{bot_config['botName']}](https://t.me/{bot_config.get('botUserName').replace('@', '')}/)⛩️**\n\n"]
                await asyncio.sleep(1)
                my_list = await task_send_data.get_my_receive_success_list(user=user[0])
                for my in my_list:
                    await asyncio.sleep(0.1)
                    if my_receive := await get_task_text(app=app, my_receive=my):
                        text.append(f"[{my_receive[0]}]({my_receive[1]})\n")

                if len(text) > 1:
                    for group in groups:
                        broadcast_logs.critical(f"发送频道：{group}")
                        try:
                            await asyncio.sleep(1)
                            msg_id = await app.send_message(
                                chat_id=group[1],
                                text="".join(text),
                                disable_web_page_preview=True,
                            )
                            await app.delete_messages(chat_id=group[1], message_ids=group[8])
                            await task_send_data.put_send_task_msgId(id=group[0], msgId=msg_id.id)
                        except (RPCError, Exception) as err:
                            broadcast_logs.error(f"定时推送错误：{err}")
                            await task_send_data.put_send_group_state(id=group[0], out_state=1, state=1)
                            await app.send_message(chat_id=user[1], text=f"《[{group[3]}]({group[6]})》-机器人权限不足")
