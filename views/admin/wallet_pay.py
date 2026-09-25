import logging
import math

from config import CallbackQuery, Client, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config
from repositories.admin.wallets import AdminWalletDate

logs = logging.getLogger(__name__)


class AdminWalletPayMixin:
    async def inputBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"💳{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())

    async def index(self, **kwargs):
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
        taskState = int(kwargs.get('state')[0]) if kwargs.get('state') else -1
        AWD = AdminWalletDate()
        list = await AWD.get_pay_list(OFFSET=OFFSET, LIMIT=LIMIT, state=taskState)
        count = await AWD.get_pay_count(state=taskState)
        keyboard = []
        text = f"💸资金-充值流水\n\n" \
               f"充值总金额:{count[1]}\n" \
               f"充值成功总金额:{count[2]}\n" \
               f"充值未支付总金额{count[3]}\n\n" \
               f"说明：状态｜充值用户｜充值金额\n" \
               f"点击下方按钮查看详细\n"
        if list:
            totalPages, currentPage = math.ceil(count[0] / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in list:
                keyboard.append([InlineKeyboardButton(f"{'🟢' if key[3] == 1 else '⚪'} {key[2]}｜{key[5]}｜{key[1]}",
                                                      callback_data=f"a/资金充值详细?order={key[0]}&state={taskState}")])
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"a/资金充值流水?page={upPage}&state={taskState}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"a/资金充值流水?page={dowPage}&state={taskState}" if currentPage != totalPages else '-')])
        else:
            keyboard.append([InlineKeyboardButton(f"空/未发现记录", callback_data="-")])
        keyboard.append(
            [InlineKeyboardButton(f"{'🌕' if taskState == -1 else '🌑'} 全部", callback_data=f"a/资金充值流水?state=-1"),
             InlineKeyboardButton(f"{'🌕' if taskState == 1 else '🌑'} 成功", callback_data=f"a/资金充值流水?state=1"),
             InlineKeyboardButton(f"{'🌕' if taskState == 0 else '🌑'} 失败", callback_data=f"a/资金充值流水?state=0")])
        keyboard.append(
            [InlineKeyboardButton(f"👉 充值流水", callback_data=f"a/资金充值流水"),
             InlineKeyboardButton(f"商家流水", callback_data=f"a/资金商家流水"),
             InlineKeyboardButton(f"用户流水", callback_data=f"a/资金用户流水")])
        keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data="a/管理首页")])
        await self.sendMsg(text=text, keyboard=keyboard)

    async def pay_info(self,**kwargs):
        state,order = kwargs.get('state'),kwargs.get('order')
        try:
            AWD = AdminWalletDate()
            order = await AWD.get_pay_info(id=order[0])
            if order:
                text = "**充值-充值详细**\n\n" \
                       f"用户ID:{order[10]}\n" \
                       f"用户名:{order[11]}\n" \
                       f"用户昵称:{order[12]}\n" \
                       f"实时余额:{order[15]}\n\n" \
                       f"创建时间:{order[9]}\n" \
                       f"充值订单:{order[2]}\n" \
                       f"充值金额:{order[4]}\n" \
                       f"支付状态:{'🟢 已付款' if order[7]==1 else '⚪ 未付款'}\n" \
                       f"充值渠道:{order[5]}\n"
                if order[7]==1:
                    text+=f"渠道订单:{order[6]}\n" \
                          f"付款时间:{order[8]}\n\n" \
                         f"**入账订单信息:**\n" \
                            f"订单号:{order[13]}\n" \
                            f"单价:{order[14]}\n" \
                            f"余额:{order[15]}\n"
                keyboard = []
                keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data=f"a/资金充值流水?state={state[0]}")])
                await self.sendMsg(text=text, keyboard=keyboard)
            else:
                await self.query.answer(text="订单号不存在")
        except Exception as e:
            logs.info(" ".join(str(value) for value in (e,)))

