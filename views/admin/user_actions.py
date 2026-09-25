import logging
import decimal
import math

from config import CallbackQuery, Client, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config, datetime, redis_client
from public.logger import LoggerConfig
from services.telegram_utils import msgNotify
from repositories.admin.users import UserDate

logs = LoggerConfig('user', 'logs/main.log').get_logger()


class AdminUserActionMixin:
    async def setAdmin(self, **kwargs):
        msg = await  self.retChat()
        if kwargs.get('user'):
            user = await UserDate().get_user_by_chat_id(chat_id=msg.chat.id)
            if user and user[5] == 2:
                pa = 1 if kwargs.get('p')[0] == '0' else 0
                if await UserDate().set_admin(id=kwargs.get('user')[0], admin=pa):
                    redis_client.delete(f"restrict{msg.chat.id}")
                    await self.client.answer_callback_query(self.query.id, text='设置管理员成功', show_alert=True)
                    await self.backReview()
                    await self.userInfo(user=kwargs.get('user'))
                else:
                    await self.client.answer_callback_query(self.query.id, text='数据异常', show_alert=True)
            elif user[5] == 1:
                await self.client.answer_callback_query(self.query.id, text='设置失败:你没权限添加管理员',
                                                        show_alert=True)
            else:
                await self.client.answer_callback_query(self.query.id, text='设置管理员失败:用户不存在',
                                                        show_alert=True)

    async def banUser(self,**kwargs):
        msg = await  self.retChat()
        user = await UserDate().get_user(id=kwargs.get('user')[0])
        if user[4]==1:
            await UserDate().set_user_state(id=user[0], state=0)
            await self.reviewNotify(user=[user[0]])
        else:
            await UserDate().set_user_state(id=user[0], state=1)
            await self.reviewNotify(user=[user[0]])
        redis_client.delete(f"restrict{msg.chat.id}")
        await self.userInfo(user=[kwargs.get('user')[0]])

    async def backReview(self,**kwargs):
        # 删除当前消息或者媒体消息返回
        msg =await  self.retChat()
        await self.client.delete_messages(msg.chat.id, message_ids=msg.id)

    async def reviewNotify(self, **kwargs):
        '''组装消息通知用户'''
        car = UserDate()
        toUser = await car.get_user(id=kwargs.get('user')[0])
        text = "✨✨✨✨✨✨✨✨✨✨✨✨\n" \
               f"💡**用户资料**💡\n\n" \
               f"〖用户ID〗`{toUser[1] or '无'}`(点击复制)\n" \
               f"〖用户账号〗`{toUser[2] or '无'}`(点击复制)\n" \
               f"〖用户昵称〗`{toUser[3] or '无'}`(点击复制)\n" \
               f"〖用户状态〗{'🟢正常' if toUser[4] == 0 else '🔴禁用'}\n"
        text += f"〖通知消息〗** {'🟢 您已被管理员解除禁用' if toUser[4]==0 else '🔴 您已被管理员禁用'} "
        try:
            await self.client.send_message(chat_id=toUser[1], text=text, disable_web_page_preview=True)
        except RPCError as e:
            msg = await self.retChat()
            await msgNotify(msg=msg, text='❗通知用户失败', times=5)

