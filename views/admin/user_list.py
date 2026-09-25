import logging
import decimal
import math

from config import CallbackQuery, Client, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config, datetime, redis_client
from public.logger import LoggerConfig
from services.telegram_utils import msgNotify
from repositories.admin.users import UserDate

logs = LoggerConfig('user', 'logs/main.log').get_logger()


class AdminUserListMixin:
    async def inputBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"👨‍💻{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())

    async def getUser(self, **kwargs):
        msg = await  self.retChat()
        OFFSET, LIMIT = 0, 10
        if kwargs.get('page'):
            OFFSET = int(kwargs.get('page')[0])
        search = kwargs.get('search')[0] if kwargs.get('search') else None
        userType = int(kwargs.get('type')[0]) if kwargs.get('type') else 0
        userS, userList = await UserDate().get_user_list(admin=userType, search=search, limit=LIMIT, offset=OFFSET)
        if userList and len(userList) > 0:
            totalPages, currentPage = math.ceil(userS[0] / LIMIT), int(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            content = []
            for user in userList:
                content.append([InlineKeyboardButton(f"{'👮‍' if user[5] == 1 else '👳‍'}{user[3]}",
                                                     callback_data=f"a/用户详情?user={user[0]}")])
            content.append([InlineKeyboardButton(f"{'上一页' if upPage >= 0 else '-'}",
                                                 callback_data=f"a/用户管理?page={upPage}&type={userType}" if upPage >= 0 else '-'),
                            InlineKeyboardButton(f"{currentPage}/{totalPages}", callback_data="-"),
                            InlineKeyboardButton(f"{'下一页' if currentPage != totalPages else '-'}",
                                                 callback_data=f"a/用户管理?page={dowPage}&type={userType}" if currentPage != totalPages else '-')])
        else:
            content = [[InlineKeyboardButton(f"空/么有用户", callback_data="-")]]
        keyboard = [
            [InlineKeyboardButton(f"{'🟢' if userType == 0 else ''}普通用户", callback_data=f"a/用户管理?type=0"),
             InlineKeyboardButton(f"{'🟢' if userType == 1 else ''}管理员", callback_data=f"a/用户管理?type=1"),
             ],[InlineKeyboardButton(f"查询用户", callback_data="a/用户输入?text=请输入用户名或者昵称:")],
            [InlineKeyboardButton(f"↩️ 返回", callback_data="a/管理首页")]]
        text = "✨✨✨✨✨✨✨✨✨✨✨✨\n\n" \
               "======**🏆 用户查询 🏆**======\n" \
               f"〖用户数〗{userS[0]}人\n" \
               f"👮‍管理员:{userS[2]}\n" \
               f"👳用户:{userS[1]}\n"
        await self.sendMsg(text=text, keyboard=content+keyboard)

    async def userInfo(self, **kwargs):
        msg = await  self.retChat()
        userID = kwargs.get('user')[0]
        user = await UserDate().get_user(id=userID)
        text = "✨✨✨✨✨✨✨✨✨✨✨✨\n" \
               f"💡**用户资料**💡\n\n" \
               f"〖用户ID〗`{user[1] or '无'}`(点击复制)\n" \
               f"〖用户账号〗`{user[2] or '无'}`(点击复制)\n" \
               f"〖用户昵称〗`{user[3] or '无'}`(点击复制)\n" \
               f"〖注册时间〗`{user[9] or '无'}`(点击复制)\n" \
               f"〖用户状态〗{'🟢正常' if user[4] == 0 else '🔴禁用'}\n" \
               f"〖用户权限〗{'👮‍管理员' if user[5] == 1 else '👳‍用户'}\n" \
               f"〖用户余额〗{user[8]}\n" \
               f"〖商家余额〗{user[7]} "
        keyboard = []
        if user[5] == 0:
            keyboard.append([InlineKeyboardButton("🔐设置管理员", callback_data=f"a/设置管理员?user={user[0]}&p=0")])
        elif user[5] == 1:
            keyboard.append([InlineKeyboardButton("🔓取消管理员", callback_data=f"a/设置管理员?user={user[0]}&p=1")])
        if user[4]==0:
            keyboard.append([InlineKeyboardButton("🚷 禁用户", callback_data=f"a/禁用户?user={user[0]}")])
        else:
            keyboard.append([InlineKeyboardButton("✅ 解禁用户", callback_data=f"a/禁用户?user={user[0]}")])
        keyboard.append([InlineKeyboardButton("💳 手动充值", callback_data=f"a/用户输入?text=请输入充值金额:{user[0]}")])
        keyboard.append([InlineKeyboardButton("✅ 用户校验流水", callback_data=f"a/用户校验流水?user={user[0]}")])
        keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data="a/用户管理")])
        await self.sendMsg(text=text, keyboard=keyboard)

