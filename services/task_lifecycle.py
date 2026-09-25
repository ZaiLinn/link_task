import asyncio

from core.asyncio_compat import ensure_event_loop

ensure_event_loop()

from pyrogram.errors import RPCError
from pyrogram import Client

from public.logger import LoggerConfig
from repositories.task_data import TaskOperationDate


task_logs = LoggerConfig("task_lifecycle", "logs/task_lifecycle.log").get_logger()


class TaskOperation:
    def __init__(self, Client: Client, Task=None):
        self.client = Client
        self.task = Task
        self.TOD = None
        self.task_group = None

    async def offline(self, Text):
        self.TOD = TaskOperationDate()
        try:
            self.task_group = await self.TOD.get_task_user_group_info(task_id=self.task)
            if self.task_group:
                task_logs.critical(f"通知商家任务下线：{self.task_group}")
                await self.TOD.put_task_state_info(id=self.task_group[0], state=2, label=Text)
                await self.offline_link()
                await self.client.send_message(chat_id=int(self.task_group[4]), text=Text)
        except Exception as err:
            task_logs.error(f"下线失败{err}")

    async def offline_link(self):
        if receive_list := await self.TOD.get_task_receive_list(task_id=self.task_group[0]):
            try:
                task_logs.critical(f"移除链接：{receive_list}")
                for receive in receive_list:
                    await self.client.revoke_chat_invite_link(
                        chat_id=int(self.task_group[6]),
                        invite_link=receive[2],
                    )
            except (RPCError, Exception) as err:
                task_logs.error(f"关闭链接错误:{err}")

    async def online(self, Text):
        self.TOD = TaskOperationDate()
        try:
            self.task_group = await self.TOD.get_task_user_group_info(task_id=self.task)
            task_logs.critical(f"商家任务上线：{self.task_group}")
            if self.task_group:
                await self.TOD.put_task_state_info(id=self.task_group[0], state=1, label=Text)
                await self.client.send_message(chat_id=int(self.task_group[4]), text=Text)
        except Exception as err:
            task_logs.error(f"上线失败{err}")

    async def online_link(self):
        receive_list = await self.TOD.get_task_receive_list(task_id=self.task_group[0])
        task_logs.critical(f"通知用户任务上线：{receive_list}")
        if receive_list:
            for receive in receive_list:
                await asyncio.sleep(0.1)
                try:
                    text = (
                        f"📢 **通知：{self.task_group[1]} 任务已重新上线**\n\n"
                        f"群/频道：[{self.task_group[7]}]({self.task_group[9]})\n"
                        f"该任务已重新上线，已添加自动发送列表."
                    )
                    await self.client.send_message(chat_id=receive[3], text=text)
                except RPCError as err:
                    task_logs.error(f"通知用户失败:{err}")
