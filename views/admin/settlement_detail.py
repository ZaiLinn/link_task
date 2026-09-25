import logging
import datetime
import math

from config import CallbackQuery, Client, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config
from public.logger import LoggerConfig
from services.cache import Var
from services.telegram_utils import msgNotify
from repositories.admin.settlements import SettlementDate

logs = LoggerConfig('admin', 'logs/main.log').get_logger()


class AdminSettlementDetailMixin:
    async def settlementInfo(self,**kwargs):
        settlement,upState=kwargs.get('set')[0],kwargs.get('up')[0]
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 5
        taskState = kwargs.get('state')[0] if kwargs.get('state') else 0
        taskData = SettlementDate()
        task_log = await taskData.get_settlement_log_list(OFFSET=OFFSET, LIMIT=LIMIT,settlement= settlement, state=taskState)
        task_count = await taskData.get_settlement_info(settlement=settlement)
        keyboard = []
        settlement_types = {0: '待审核',1: '已审核',5: '待申诉',6: '已拒绝'}
        text = f"\n**后台-结算详情**\n\n" \
               f"结算ID：{task_count[0]}｜" \
               f"时间：{task_count[7].strftime('%Y-%m-%d')}\n" \
               f"资金流水：{task_count[3] or '无'}\n" \
               f"结算状态：{'申诉中' if task_count[8]==1 else settlement_types.get(task_count[5], '')}\n" \
               f"结算备注：{task_count[6] or '无'}\n" \
               f"结算任务：{task_count[10]}｜" \
               f"单价：{task_count[11]}\n" \
               f"群组：[{task_count[12]}]({task_count[13]})\n" \
               f"推手ID：{task_count[20]}｜" \
               f"推手ID：{task_count[14]}｜"\
               f"昵称：{task_count[15]}\n"\
               f"结算数量：{task_count[16]}｜" \
               f"金额：{task_count[17]}\n" \
                f"不结算数量：{task_count[18]}｜" \
                f"金额：{task_count[19]}\n"
        text+="\n**邀请列表**\n"
        if task_log:
            totalPages, currentPage = math.ceil((task_count[16] if int(taskState)==0 else task_count[18]) / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in task_log:
                user_count=await taskData.get_task_log_user_count(t_user=key[5])
                text += f"[邀请时间:{key[4].strftime('%y.%m.%d %H:%M:%S')} ｜佣金:{key[1]}](https://t.me/)\n" \
                        f"账号:`{key[8] if len(key[8]) > 1 else '未设置'}` ｜昵称:`{key[6]}{key[7]}` \n" \
                        f"状态:{key[3]} ｜其他:{user_count[0] if user_count[0]>2 else 1}次\n"
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"a/管理结算详情?page={upPage}&state={taskState}&set={settlement}&up={upState}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"a/管理结算详情?page={dowPage}&state={taskState}&set={settlement}&up={upState}" if currentPage != totalPages else '-')])
        else:
            text+="\n列表为空,未发现邀请"
        keyboard.append([InlineKeyboardButton(f"{'🌕' if int(taskState) == 0 else '🌑'} 未结算",callback_data=f"a/管理结算详情?state=0&set={settlement}&up={upState}"),
                         InlineKeyboardButton(f"{'🌕' if int(taskState) == 1 else '🌑'} 不结算",callback_data=f"a/管理结算详情?state=1&set={settlement}&up={upState}")
                         ])
        keyboard.append([InlineKeyboardButton("📑 校验流水", callback_data=f"a/用户校验流水?user={task_count[20]}")])
        if task_count[5] ==5 and task_count[8] ==1:
            keyboard.append([InlineKeyboardButton(f"✅ 确认结算", callback_data=f"a/管理结算确认?set={settlement}"),
                             InlineKeyboardButton(f"😊 偷偷结算", callback_data=f"a/管理偷结算确认?set={settlement}"),
                             InlineKeyboardButton(f"❌ 拒绝结算", callback_data=f"a/管理结算拒绝?set={settlement}")])
        var = await Var(Id=(await self.retChat()).chat.id).read()
        keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data=f"{var if 'a/管理结算首页' in var else 'a/管理结算首页'}")])
        await self.sendMsg(text=text, keyboard=keyboard)

