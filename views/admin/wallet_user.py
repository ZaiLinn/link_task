import logging
import math

from config import CallbackQuery, Client, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config
from repositories.admin.wallets import AdminWalletDate

logs = logging.getLogger(__name__)


class AdminWalletUserMixin:
    async def user(self, **kwargs):
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
        taskState = int(kwargs.get('state')[0]) if kwargs.get('state') else -1
        AWD = AdminWalletDate()
        list = await AWD.get_order_u_list(OFFSET=OFFSET, LIMIT=LIMIT, order_type=taskState)
        count = await AWD.get_order_u_count(order_type=taskState)
        logs.info(" ".join(str(value) for value in (count,)))
        keyboard = []
        text = f"💸资金-用户流水\n\n" \
               f"总余额:{count[1]}\n" \
               f"说明：类型｜用户｜金额｜说明\n" \
               f"点击下方按钮查看详细\n"
        if list:
            totalPages, currentPage = math.ceil(count[0] / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in list:
                keyboard.append([InlineKeyboardButton(f"{'➕' if key[2] == 0 else '➖'} {key[4]}｜{key[1]}｜{key[3]}",
                                                      callback_data=f"a/资金用户详细?order={key[0]}&state={taskState}")])
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"a/资金用户流水?page={upPage}&state={taskState}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"a/资金用户流水?page={dowPage}&state={taskState}" if currentPage != totalPages else '-')])
        else:
            keyboard.append([InlineKeyboardButton(f"空/未发现记录", callback_data="-")])
        keyboard.append(
            [InlineKeyboardButton(f"{'🌕' if taskState == -1 else '🌑'} 全部", callback_data=f"a/资金用户流水?state=-1"),
             InlineKeyboardButton(f"{'🌕' if taskState == 1 else '🌑'} 支出", callback_data=f"a/资金用户流水?state=1"),
             InlineKeyboardButton(f"{'🌕' if taskState == 0 else '🌑'} 收入", callback_data=f"a/资金用户流水?state=0")])
        keyboard.append(
            [InlineKeyboardButton(f"充值流水", callback_data=f"a/资金充值流水"),
             InlineKeyboardButton(f"商家流水", callback_data=f"a/资金商家流水"),
             InlineKeyboardButton(f"👉 用户流水", callback_data=f"a/资金用户流水")])
        keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data="a/管理首页")])
        await self.sendMsg(text=text, keyboard=keyboard)

    async def user_info(self,**kwargs):
        taskState,order=kwargs.get('state'),kwargs.get('order')
        try:
            AWD = AdminWalletDate()
            order =await AWD.get_order_u_info(id=order[0])
            if order:
                text = "**用户流水-流水详情**\n\n" \
                       f"ID:{order[9]}\n" \
                       f"用户ID:{order[10]}\n" \
                       f"用户名:{order[11]}\n" \
                       f"用户昵称:{order[12]}\n" \
                       f"实时余额:{order[17]}\n\n" \
                       f"订单号:{order[1]}\n" \
                       f"金额:{'-' if order[3]==1 else '+'}{order[2]}\n" \
                       f"余额:{order[4]}\n" \
                       f"备注:{order[7]}\n" \
                       f"时间:{order[8]}\n\n"
                if order[3]==0:
                    if "任务结算" in order[7]:
                        zhi_info = await  AWD.get_order_u_jie_info(order_id=order[1])
                        if zhi_info:
                            text += f"**支出订单信息:**\n" \
                                    f"订单号:{zhi_info[1]}\n" \
                                    f"用户:{zhi_info[6]}\n" \
                                    f"任务:{zhi_info[3]}\n" \
                                    f"链接:{zhi_info[5]}\n" \
                                    f"单价:{zhi_info[4]}\n" \
                                    f"日期:{zhi_info[2].strftime('%Y-%m-%d')}\n"
                    elif "提现失败退回金额" in order[7]:
                        text += f"**提现订单信息:**\n" \
                                f"订单号:{order[6]}\n"
                elif order[3]==1:
                    # 支出详细
                    if "用户提现" in order[7]:
                        ti_info= await  AWD.get_order_u_withdraw_info(order_id=order[1])
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
                keyboard=[]
                keyboard.append([InlineKeyboardButton("📑 校验流水", callback_data=f"a/用户校验流水?user={order[9]}")])
                keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data=f"a/资金用户流水?state={taskState[0]}")])
                await self.sendMsg(text=text,keyboard=keyboard)
            else:
                await self.query.answer(text="订单号不存在")
        except Exception as e:
            logs.info(" ".join(str(value) for value in (e,)))

