import logging
import datetime
import math

from config import CallbackQuery, Client, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config
from public.logger import LoggerConfig
from services.cache import Var
from services.telegram_utils import msgNotify
from repositories.admin.settlements import SettlementDate

logs = LoggerConfig('admin', 'logs/main.log').get_logger()


class AdminSettlementListMixin:
    async def index(self, **kwargs):
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
        taskState = int(kwargs.get('state')[0]) if kwargs.get('state') else 5
        closeData = SettlementDate()
        task = await closeData.get_settlement_list(OFFSET=OFFSET, LIMIT=LIMIT, state=taskState)
        task_count = await closeData.get_settlement_count()
        keyboard = []
        text = f"**后台-结算管理**\n\n" \
               f"结算总数(含拒绝)：{task_count[0]}\n" \
               f"结算总金额(含拒绝)：{task_count[1]}\n\n" \
               f"未结算总数：{task_count[8]}｜" \
               f"未结算总金额：{task_count[9]}\n" \
               f"已结算总数：{task_count[4]}｜" \
               f"已结算总金额：{task_count[5]}\n" \
               f"已拒绝总数：{task_count[2]}｜" \
               f"已拒绝总金额：{task_count[3]}\n\n" \
               f"申诉中总数：{task_count[6]}\n" \
               f"申诉总金额：{task_count[7]}\n\n" \
               f"按钮说明:任务标题-推广人-待结算佣金" \
               f"申诉:用户提交申诉后管理器进行最终裁决\n" \
               f"点击下方结算按钮查看详细"
        if task and task_count:
            settlement_types = {0:task_count[8],5: task_count[6], 1: task_count[4], 6: task_count[2]}
            totalPages, currentPage = math.ceil(settlement_types.get(taskState) / LIMIT), math.ceil(
                OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in task:
                keyboard.append([InlineKeyboardButton(f"{key[1].strftime('%Y/%m/%d')}-{key[2]}-{key[4]} ",
                                                      callback_data=f"a/管理结算详情?set={key[0]}&up={taskState}")])
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"a/管理结算首页?page={upPage}&state={taskState}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"a/管理结算首页?page={dowPage}&state={taskState}" if currentPage != totalPages else '-')])
        else:
            keyboard.append([InlineKeyboardButton(f"空/还没数据", callback_data="-")])
        keyboard.append([InlineKeyboardButton(f"{'🌕' if taskState == 5 else ''}申诉",
                                              callback_data=f"a/管理结算首页?state=5"),
                         InlineKeyboardButton(f"{'🌕' if taskState == 0 else ''}未结",
                                              callback_data=f"a/管理结算首页?state=0"),
                         InlineKeyboardButton(f"{'🌕' if taskState == 1 else ''}已结",
                                              callback_data=f"a/管理结算首页?state=1"),
                         InlineKeyboardButton(f"{'🌕' if taskState == 6 else ''}已拒",
                                              callback_data=f"a/管理结算首页?state=6")])
        keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data="a/管理首页")])
        await self.sendMsg(text=text, keyboard=keyboard,var=True)

