import decimal
import re

from core.asyncio_compat import ensure_event_loop

ensure_event_loop()

from pyrogram.errors import RPCError
from pyrogram import Client
from pyrogram.types import ChatMemberUpdated

from core.bot import app
from core.config import bot_config
from public.logger import LoggerConfig
from repositories.task_data import BorInGroupData
from services.task_lifecycle import TaskOperation
from services.telegram_utils import isPrivileges


group_logs = LoggerConfig("group_membership", "logs/group_membership.log").get_logger()


class BorInGroup:
    def __init__(self, Client: Client, Updata: ChatMemberUpdated):
        self.client = Client
        self.update = Updata
        self.BIGDate = None

    async def input_group(self, **kwargs):
        group_logs.critical("机器人入群")
        BIGDate = BorInGroupData()
        user = await BIGDate.getUser(chat_id=self.update.from_user.id)
        if user and user[4] == 0:
            group = await app.get_chat(self.update.chat.id)
            is_privi = await isPrivileges(chatId=self.update.chat.id, typeG=group.type.name)
            if is_privi == 1:
                await BIGDate.putGroupState(group_id=self.update.chat.id, state=1)
                text = f"《{self.update.chat.title}》-机器人权限不足"
                return await self.client.send_message(chat_id=user[1], text=text)

            group_date = await BIGDate.getGroup(group_id=group.id)
            if group_date:
                if group_date[9] == 10:
                    text = f"《[{group.title}]({group.invite_link})》您的群已被禁用请联系管理员"
                    return await self.client.send_message(chat_id=user[1], text=text)

                await BIGDate.putGroup(group=group, id=group_date[0], user=user[0])
                text = f"《[{group.title}]({group.invite_link})》存在,数据已更新！！权限检测正常"
                group_logs.critical(text)
                return await self.client.send_message(chat_id=user[1], text=text)

            await BIGDate.postGroup(group=group, user=user[0])
            text = f"添加《[{group.title}]({group.invite_link})》成功,权限检测正常"
            return await self.client.send_message(chat_id=user[1], text=text)

    async def out_group(self, **kwargs):
        group_logs.critical("机器人退群")
        BIGDate = BorInGroupData()
        await BIGDate.putGroupState(group_id=self.update.chat.id, state=2)
        text = f"《{self.update.chat.title}》未检测到机器人"
        return await self.client.send_message(chat_id=self.update.old_chat_member.invited_by.id, text=text)

    async def invite_group(self, **kwargs):
        try:
            self.BIGDate = BorInGroupData()
            url_link = self.update.invite_link.invite_link
            new_user = self.update.new_chat_member
            group_logs.critical(
                f"邀请链接:{url_link}\n"
                f"新用户{new_user.user.username}-昵称:{new_user.user.last_name or ''}{new_user.user.first_name or ''}"
            )
            task_receive = await self.BIGDate.get_task_receive_link(link=url_link)
            if task_receive and self.update.new_chat_member:
                await self.removal_task(task_receive=task_receive)
                task_user = await self.BIGDate.get_tinvite_task_user(new=new_user)
                if await self.is_bot(task=task_receive[6:14]):
                    if await self.is_cheating(task_user=task_user, task_receive=task_receive):
                        if await self.is_proportion(task_receive=task_receive):
                            group_logs.critical("扣量")
                            return await self.BIGDate.post_task_log(
                                in_user=task_user[0],
                                recieve=task_receive[0],
                                task=task_receive[1],
                                price=task_receive[4],
                                state=10,
                                label="未通过:百分比",
                            )
                        group_logs.critical(f"{task_receive[0]}通过检测:{task_receive[4]}U-{task_receive[15]}")
                        await self.BIGDate.post_task_log(
                            in_user=task_user[0],
                            recieve=task_receive[0],
                            task=task_receive[1],
                            price=task_receive[4],
                            state=0,
                            label="已通过。",
                        )
                else:
                    group_logs.critical(f"{task_receive[0]}未通过检测:{task_receive[4]}U-{task_receive[15]}")
                    return await self.BIGDate.post_task_log(
                        in_user=task_user[0],
                        recieve=task_receive[0],
                        task=task_receive[1],
                        price=task_receive[4],
                        state=1,
                        label="未通过:任务规则不满足。",
                    )
            elif self.update.new_chat_member:
                group_logs.critical("无邀请 new_chat_member信息")
                if task := await self.BIGDate.get_Group_task_list(id=self.update.chat.id):
                    task_receive = await self.BIGDate.get_task_receive_task(task=task, url=url_link, user=1671)
                    await self.removal_task(task_receive=task_receive)
                    task_user = await self.BIGDate.get_tinvite_task_user(new=new_user)
                    if await self.is_bot(task=task_receive[6:14]):
                        group_logs.critical(f"无邀请通过检测:{task_receive[4]}U-{task_receive[15]}")
                        return await self.BIGDate.post_task_log(
                            in_user=task_user[0],
                            recieve=task_receive[0],
                            task=task_receive[1],
                            price=task_receive[4],
                            state=0,
                            label="已通过.",
                        )
                    group_logs.critical(f"无邀请未通过检测:{task_receive[4]}U-{task_receive[15]}")
                    return await self.BIGDate.post_task_log(
                        in_user=task_user[0],
                        recieve=task_receive[0],
                        task=task_receive[1],
                        price=task_receive[4],
                        state=1,
                        label="未通过:任务规则不满足.",
                    )
            else:
                group_logs.critical("邀请链接不是任务平台的")
        except Exception as err:
            group_logs.critical(f"邀请链接错误{err}")

    async def is_bot(self, **kwargs):
        try:
            task = kwargs.get("task")
            patterns = {
                "cn": re.compile(r"[\u4e00-\u9fff]"),
                "en": re.compile(r"[a-zA-Z]"),
                "ru": re.compile(r"[а-яА-Я]"),
                "ar": re.compile(r"[\u0600-\u06FF]"),
                "ja": re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u31F0-\u31FF\uFF66-\uFF9F]"),
                "ko": re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F\uA960-\uA97F\uD7B0-\uD7FF]"),
                "fa": re.compile(r"[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF\uFB00-\uFB4F]"),
            }
            flags = ("cn", "en", "ru", "ar", "ja", "ko", "fa")
            from_user = self.update.new_chat_member.user
            name = f"{from_user.last_name or ''}{from_user.first_name or ''}"
            language = {
                flag: bool(patterns[flag].search(name))
                for index, flag in enumerate(flags, start=1)
                if task[index] == 1
            }

            if any(language.values()) or len(language) == 0:
                if task[0] == 1:
                    return bool(from_user.username)
                return True
            return False
        except Exception as err:
            group_logs.error(f"判断规则错误:{err}")
            return False

    async def is_proportion(self, **kwargs):
        task_receive = kwargs.get("task_receive")
        if task_receive[5] != 100:
            log_date = await self.BIGDate.get_task_log_pass(receive=task_receive[0])
            if log_date[0] + log_date[1] > 100:
                scale = log_date[0] / (log_date[0] + log_date[1]) * 100
                if scale > task_receive[5]:
                    return True
        return False

    async def removal_task(self, **kwargs):
        try:
            task_receive = kwargs.get("task_receive")
            balance = await self.BIGDate.get_user_balance(user=task_receive[2])
            group_logs.critical(f"检测商家余额{balance}")
            if task_receive[14] == 1 and balance < decimal.Decimal(bot_config["stop_balance"]):
                group_logs.critical(f"余额不足:{balance}")
                task_operation = TaskOperation(Client=self.client, Task=task_receive[1])
                await task_operation.offline(Text=f"⚠️ 可用余额低于{bot_config['stop_balance']}u,已停用《{task_receive[15]}》任务推广请充值！！")
        except (Exception, RPCError) as err:
            group_logs.critical(f"余额错误:{err}")

    async def is_cheating(self, **kwargs):
        task_user = kwargs.get("task_user")
        task_receive = kwargs.get("task_receive")
        task_log = await self.BIGDate.get_task_log(in_id=task_user[0], task=task_receive[1])
        if task_log[0] != 0:
            group_logs.critical("用户已经加过群")
            return False
        if task_log[1] >= int(bot_config["user_alarm"]):
            group_logs.critical("用户可能作弊")
            await self.send_admin_group(inUser=task_user)
            return True
        return True

    async def send_admin_group(self, inUser):
        try:
            if inUser[8] == 0:
                text = (
                    "🚨**风险用户预警**"
                    "======被邀请人信息=======\n\n"
                    f"ID:{inUser[1]}\n"
                    f"用户名:{inUser[2] or '未设置'}\n"
                    f"昵称:{inUser[3]}{inUser[4]}\n"
                    f"客户端语言:{inUser[5] or '未知'}\n"
                    f"建档时间:{inUser[6]}\n"
                    f"\n======邀请人记录=======\n"
                )
                receive_list = await self.BIGDate.get_user_link_receive(in_user=inUser[0])
                if receive_list:
                    for receive in receive_list:
                        text += f"ID:{receive[3]}/昵称:{receive[5]}/{receive[1]}次\n"
                else:
                    text += "无被邀请人信息"

                text += "\n======任务记录=======\n"
                task_list = await self.BIGDate.get_user_link_task(in_user=inUser[0])
                if task_list:
                    for task in task_list:
                        text += f"ID:{task[0]}/任务:{task[2]}/频:[{task[4]}]({task[5]})/{task[1]}次\n"
                else:
                    text += "无被邀请人信息"

                await self.BIGDate.put_invite_task_user(id=inUser[0], key="state", value=1)
                await self.client.send_message(chat_id=int(bot_config["adminGroup"]), text=text)
        except RPCError as err:
            group_logs.error(f"发送管理员信息错误:{err}")

    async def user_exit_group(self, **kwargs):
        fullname = f"{self.update.from_user.first_name}{self.update.from_user.last_name}"
        BIGDate = BorInGroupData()
        if group := await BIGDate.getGroup(group_id=self.update.chat.id):
            if task_user := await BIGDate.get_exit_user_group_info(chatid=self.update.from_user.id, groupId=group[0]):
                await BIGDate.put_exit_user_group_info(id=task_user[0], state=1, label="未通过:用户退群")
                group_logs.critical(f"{task_user[1]}-{fullname}-用户退群-{group[3]}")
