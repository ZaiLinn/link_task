import logging
import datetime
import decimal
import math

from config import ForceReply, InlineKeyboardButton, RPCError, bot_config
from services.cache import Var
from services.payment import OkayPay
from services.task_lifecycle import TaskOperation
from services.telegram_utils import msgNotify, truncate_string
from repositories.client.settlements import MySettlementDate
from repositories.client.tasks import MyTaskDate, TaskDate
from repositories.client.wallets import MyWalletDate
from repositories.client.withdrawals import MyWithdrawDate
from views.base import BaseView

logs = logging.getLogger(__name__)


class MyWallet(BaseView):
    async def inputBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"🧧{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())

    async def index(self, **kwargs):
        try:
            user = self.data.get("user")[0]
            OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
            taskState = int(kwargs.get('state')[0]) if kwargs.get('state') else -1
            MWDate = MyWalletDate()
            order = await MWDate.get_order_out_list(OFFSET=OFFSET, LIMIT=LIMIT, user=user, order_type=taskState)
            order_count = await MWDate.get_order_out_count(user=user, order_type=taskState)
            keyboard = []
            text = f"👤用户-资金流水\n\n" \
                   f"账户余额:{order_count[1]}\n" \
                   f"待结算:{order_count[2]}\n" \
                   f"说明:订单号-变动金额" \
                   f"点击下方按钮进行更多操作\n"
            if order and order_count:
                totalPages, currentPage = math.ceil(order_count[0] / LIMIT), math.ceil(OFFSET / LIMIT) + 1
                upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
                for key in order:
                    keyboard.append([InlineKeyboardButton(f"{key[7]}-金额{key[2]}-余额{key[4]}",
                                                          callback_data=f"r/任务资金订单详情?order={key[0]}&state={taskState}")])
                keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                      callback_data=f"r/任务资金钱包?page={upPage}&state={taskState}" if upPage >= 0 else '-'),
                                 InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                                 InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                      callback_data=f"r/任务资金钱包?page={dowPage}&state={taskState}" if currentPage != totalPages else '-')])
            else:
                keyboard.append([InlineKeyboardButton(f"空/未发现记录", callback_data="-")])
            keyboard.append([InlineKeyboardButton(f"{'🌕' if taskState == -1 else '🌑'} 全部",
                                                  callback_data=f"r/任务资金钱包?state=-1"),
                             InlineKeyboardButton(f"{'🌕' if taskState == 0 else '🌑'} 收入",
                                                  callback_data=f"r/任务资金钱包?state=0"),
                             InlineKeyboardButton(f"{'🌕' if taskState == 1 else '🌑'} 支出",
                                                  callback_data=f"r/任务资金钱包?state=1")])
            keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data="r/任务用户中心")])
            await self.sendMsg(text=text, keyboard=keyboard,var=True)
        except Exception as e:
            logs.info(" ".join(str(value) for value in (e,)))

    async def order_info(self, **kwargs):
        taskState,order=kwargs.get('state'),kwargs.get('order')
        try:
            MWDate = MyWalletDate()
            order = await MWDate.get_order_info(order=order[0])
            if order:
                text = "**用户-钱包账单详情**\n\n" \
                       f"订单号:{order[1]}\n" \
                       f"金额:{'-' if order[3]==1 else '+'}{order[2]}\n" \
                       f"余额:{order[4]}\n" \
                       f"备注:{order[7]}\n" \
                       f"时间:{order[8]}\n\n"
                if order[3] == 0:
                    # 充值详细
                    if order[7] == "任务结算":
                        zhi_info = await  MWDate.get_order_u_jie_info(order_id=order[1])
                        if zhi_info:
                            text += f"**支出订单信息:**\n" \
                                    f"订单号:{zhi_info[1]}\n" \
                                    f"用户:{zhi_info[6]}\n" \
                                    f"任务:{zhi_info[3]}\n" \
                                    f"链接:{zhi_info[5]}\n" \
                                    f"单价:{zhi_info[4]}\n" \
                                    f"日期:{zhi_info[2].strftime('%Y-%m-%d')}\n"
                    elif order[7] == "提现失败退回金额":
                        text += f"**提现失败退回订单信息:**\n" \
                                f"订单号:{order[6]}\n"
                elif order[3]==1:
                    # 支出详细
                    if order[7] == "用户提现":
                        ti_info= await  MWDate.get_order_u_withdraw_info(order_id=order[1])
                        if ti_info:
                            text += f"**提现订单信息:**\n"
                            if ti_info[3]==0:
                                text += f"状态:待审核\n"
                            elif ti_info[3]==1:
                                text += f"状态:已打款\n"\
                                    f"时间:{ti_info[6]}\n" \
                                    f"渠道:{ti_info[9]}\n" \
                                    f"渠道订单:{ti_info[10]}\n" \
                                    f"备注:{ti_info[7]}\n"
                            elif ti_info[3]==2:
                                text += f"状态:已拒绝\n" \
                                        f"拒绝时间:{ti_info[6]}\n"\
                                        f"拒绝原因:{ti_info[7]}\n" \
                                        f"退款订单号:{ti_info[8]}"
                keyboard = []
                var = await Var(Id=(await self.retChat()).chat.id).read()
                keyboard.append([InlineKeyboardButton("↩️ 返回",callback_data=f"{var if 'r/任务资金钱包' in var else 'r/任务资金钱包'}")])
                await self.sendMsg(text=text, keyboard=keyboard)
            else:
                await self.query.answer(text="订单号不存在")
        except Exception as e:
            logs.info(" ".join(str(value) for value in (e,)))
