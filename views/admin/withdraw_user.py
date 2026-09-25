import logging
import datetime
import decimal
import math

from config import CallbackQuery, Client, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config, redis_client
from services.payment import OkayPay
from services.telegram_utils import msgNotify
from repositories.admin.withdrawals import Withdraw

logs = logging.getLogger(__name__)


class AdminWithdrawUserMixin:
    async def userInfo(self, **kwargs):
        wid,userID = kwargs.get('wid'),kwargs.get('user')
        user = await Withdraw().get_user(id=userID[0])
        text = f"💡**提现用户资料**💡\n\n" \
               f"〖用户ID〗`{user[1] or '无'}`(点击复制)\n" \
               f"〖用户账号〗`{user[2] or '无'}`(点击复制)\n" \
               f"〖用户昵称〗`{user[3] or '无'}`(点击复制)\n" \
               f"〖用户状态〗{'🟢正常' if user[4] == 0 else '🔴禁用'}\n" \
               f"〖用户权限〗{'👮‍管理员' if user[5] == 1 else '👳‍用户'}\n"
        keyboard = []
        if user[4] == 0:
            keyboard.append([InlineKeyboardButton("🚷 禁用户", callback_data=f"a/管理提现禁用户?wid={wid[0]}&user={userID[0]}")])
        else:
            keyboard.append([InlineKeyboardButton("✅ 解禁用户", callback_data=f"a/管理提现禁用户?wid={wid[0]}&user={userID[0]}")])
        keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data=f"a/管理提现详情?wid={wid[0]}")])
        await self.sendMsg(text=text, keyboard=keyboard)

    async def banUser(self, **kwargs):
        wid,userID = kwargs.get('wid'),kwargs.get('user')
        user = await Withdraw().get_user(id=userID[0])
        logs.info(" ".join(str(value) for value in (user,)))
        if user[4] == 1:
            await Withdraw().set_user_state(id=userID[0], state=0)
        else:
            await Withdraw().set_user_state(id=userID[0], state=1)
        redis_client.delete(f"restrict{user[1]}")
        await self.userInfo(wid=wid,user=userID)

    async def capitalFlow(self,**kwargs):
        wid, userID = kwargs.get('wid'), kwargs.get('user')
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
        MWDate = Withdraw()
        order = await MWDate.get_order_out_list(OFFSET=OFFSET, LIMIT=LIMIT, user=userID[0])
        order_count = await MWDate.get_order_out_count(user=userID[0])
        keyboard = []
        text = f"👤用户-资金流水\n\n" \
               f"账户余额:{order_count[1]}\n\n" \
               f"资金流水列表\n"
        if order and order_count:
            totalPages, currentPage = math.ceil(order_count[0] / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in order:
                text+=f"\n{'➕' if key[3]==0 else '➖'} {key[2]}|余额:{key[4]}\n" \
                      f"备注:{key[7]}\n" \
                      f"时间:{key[8]}\n"
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"a/提现用户流水?page={upPage}&wid={wid[0]}&user={userID[0]}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"a/提现用户流水?page={dowPage}&wid={wid[0]}&user={userID[0]}" if currentPage != totalPages else '-')])
        else:
            text+=f"空/未发现记录"
        keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data=f"a/管理提现详情?wid={wid[0]}")])
        await self.sendMsg(text=text, keyboard=keyboard)

    async def settlementHistory(self,**kwargs):
        wid, userID = kwargs.get('wid'), kwargs.get('user')
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
        MWDate = Withdraw()
        settlement_list = await MWDate.get_settlement_list(OFFSET=OFFSET, LIMIT=LIMIT, user=userID[0])
        settlement_count = await MWDate.get_settlement_count(user=userID[0])
        keyboard = []
        text = f"👤用户-任务结算记录\n\n" \
                f"已结算总数：{settlement_count[2]}|" \
                f"已结算总金额：{settlement_count[3]}\n" \
                f"已拒绝总数：{settlement_count[0]}|" \
                f"已拒绝总金额：{settlement_count[1]}\n" \
                f"待结算总数：{settlement_count[4]}|" \
                f"待结算总金额：{settlement_count[5]}\n\n" \
                f"任务结算列表\n"
        if settlement_list and settlement_count:
            totalPages, currentPage = math.ceil(settlement_count[6] / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in settlement_list:
                state_in ={0:'❓',1:'✅',5:'❎',6:'❌'}
                text+=f"\n{state_in.get(key[1])} 备注:{key[2]}|时间:{key[5].strftime('%Y-%m-%d')}｜金额:{key[12]}\n" \
                      f"出账订单:{key[3]} ｜ 入账订单:{key[4]}\n"\
                      f"出账用户:{key[6]}|@{key[7]}|{key[8]}\n" \
                      f"出账任务:{key[9]}|频道:[{key[10]}]({key[11]})\n"
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"a/提现结算历史?page={upPage}&wid={wid[0]}&user={userID[0]}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"a/提现结算历史?page={dowPage}&wid={wid[0]}&user={userID[0]}" if currentPage != totalPages else '-')])
        else:
            text+=f"空/未发现记录"
        keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data=f"a/管理提现详情?wid={wid[0]}")])
        await self.sendMsg(text=text, keyboard=keyboard)

    async def taskHistory(self,**kwargs):
        wid, userID = kwargs.get('wid'), kwargs.get('user')
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
        MWDate = Withdraw()
        task_list = await MWDate.get_taskHistory_list(OFFSET=OFFSET, LIMIT=LIMIT, user=userID[0])
        task_count = await MWDate.get_taskHistory_count(user=userID[0])
        keyboard = []
        text = f"👤用户-任务记录\n\n" \
                f"任务总数：{task_count[0]}\n" \
                f"邀请有效数：{task_count[1]}｜" \
                f"邀请有效佣金：{task_count[2]}\n" \
                f"邀请无效数：{task_count[3]}｜" \
                f"邀请无效佣金：{task_count[4]}\n" \
                f"任务列表\n"
        if task_list and task_count:
            totalPages, currentPage = math.ceil(task_count[0] / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in task_list:
                text+=f"\n任务:{key[2]}｜频道:[{key[3]}]({key[4]})\n" \
                      f"有效数:{key[5]}｜无效数{key[6]}\n" \
                      f"时间:{key[1].strftime('%y.%m.%d %H:%M:%S')}\n"
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"a/提现任务历史?page={upPage}&wid={wid[0]}&user={userID[0]}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"a/提现任务历史?page={dowPage}&wid={wid[0]}&user={userID[0]}" if currentPage != totalPages else '-')])
        else:
            text+=f"空/未发现记录"
        keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data=f"a/管理提现详情?wid={wid[0]}")])
        await self.sendMsg(text=text, keyboard=keyboard)

