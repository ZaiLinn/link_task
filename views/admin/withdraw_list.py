import logging
import datetime
import decimal
import math

from config import CallbackQuery, Client, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config, redis_client
from services.payment import OkayPay
from services.telegram_utils import msgNotify
from repositories.admin.withdrawals import Withdraw

logs = logging.getLogger(__name__)


class AdminWithdrawListMixin:
    async def inputBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"🪧{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())

    async def index(self, **kwargs):
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 20
        taskState = int(kwargs.get('state')[0]) if kwargs.get('state') else 0
        myW = Withdraw()
        withdraw = await myW.get_withdraw_list(LIMIT=LIMIT, OFFSET=OFFSET, state=taskState)
        withdraw_count = await myW.get_withdraw_count()
        keyboard = []
        text = f"👤后台-提现管理\n\n" \
               f"待提现金额:{withdraw_count[1]}\n" \
               f"待提现数:{withdraw_count[0]}\n\n" \
               f"已提现金额:{withdraw_count[3]}\n" \
               f"已提现数:{withdraw_count[2]}\n\n" \
               f"拒绝提现金额:{withdraw_count[5]}\n" \
               f"拒绝提现数:{withdraw_count[4]}\n\n" \
               f"点击下方任务按钮操作提现\n"
        if withdraw:
            settlement_types = {0: withdraw_count[0], 1: withdraw_count[2], 2: withdraw_count[4]}
            totalPages, currentPage = math.ceil(settlement_types.get(taskState) / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in withdraw:
                keyboard.append([InlineKeyboardButton(f"🧧{key[5]}-提现{key[1]} 👈",
                                                      callback_data=f"a/管理提现详情?wid={key[0]}&ups={taskState}")])
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"a/管理提现首页?page={upPage}&state={taskState}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"a/管理提现首页?page={dowPage}&state={taskState}" if currentPage != totalPages else '-')])
        else:
            keyboard.append([InlineKeyboardButton(f"空/未发现", callback_data="-")])
        keyboard.append(
            [InlineKeyboardButton(f"{'🌕' if int(taskState) == 0 else ''} 待审核",
                                  callback_data=f"a/管理提现首页?state=0"),
             InlineKeyboardButton(f"{'🌕' if int(taskState) == 1 else ''} 已打款",
                                  callback_data=f"a/管理提现首页?state=1"),
             InlineKeyboardButton(f"{'🌕' if int(taskState) == 2 else ''} 已拒绝",
                                  callback_data=f"a/管理提现首页?state=2")])
        keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data="a/管理首页")])
        await self.sendMsg(text=text, keyboard=keyboard)

    async def withdrawInfo(self, **kwargs):
        wid = kwargs.get('wid')
        if wid:
            myW = Withdraw()
            info = await myW.get_withdraw_info(id=wid[0])
            logs.info(" ".join(str(value) for value in (info,)))
            if info:
                wState = {0: '打款中', 1: '已打款', 2: '已拒绝'}
                text = f"**管理-提现详情**\n\n" \
                       f"**提现信息**\n" \
                       f"提现时间：{info[5]}\n" \
                       f"提现ID：{info[0]}\n" \
                       f"扣款订单号：{info[4]}\n" \
                       f"提现金额：{info[2]+info[11]}U\n" \
                       f"手续费：{info[11]}U\n" \
                       f"实际到账：{info[2]}U\n" \
                       f"状态：{wState.get(info[3])}\n" \
                       f"提现备注：{info[7]}\n" \
                       f"\n**用户信息**\n" \
                       f"ID:{info[12]}\n" \
                       f"账号ID：{info[13]}\n" \
                       f"用户名：{info[14]}\n" \
                       f"昵称：{info[15]}\n" \
                       f"余额：{info[20]}\n"

                if info[3] == 2:
                    text += f"\n退回订单号：{info[8]}\n"
                elif info[3] == 1:
                    text += f"\n打款渠道：{info[9]}\n" \
                            f"订单号: {info[10]}\n"\
                            f"打款时间: {info[6]}\n"
                text+=f"\n说明:可以查看用户的资金结算任务历史记录判断用户情况，也可以在用户管理内禁用用户\n" \
                       f"注意:点击同意提现后会立刻进行okpay转账请确认资金充足,拒绝提现后资金将返还给用户"
                keyboard = []
                keyboard.append([InlineKeyboardButton("💰资金流水", callback_data=f"a/提现用户流水?wid={wid[0]}&user={info[1]}"),
                                 InlineKeyboardButton("🧾结算历史", callback_data=f"a/提现结算历史?wid={wid[0]}&user={info[1]}"),
                                 InlineKeyboardButton("📝任务历史", callback_data=f"a/提现任务历史?wid={wid[0]}&user={info[1]}")])
                keyboard.append([InlineKeyboardButton("📑 校验流水", callback_data=f"a/用户校验流水?user={info[1]}"),
                                 InlineKeyboardButton("👤 用户管理", callback_data=f"a/管理提现用户详情?wid={wid[0]}&user={info[1]}")])
                if info[3] == 0:
                    keyboard.append([InlineKeyboardButton("🚫 拒绝提现", callback_data=f"a/管理提现输入?text=请输入拒绝原因:{wid[0]}"),
                                     InlineKeyboardButton("🟢 同意提现", callback_data=f"a/提现同意?wid={wid[0]}")])
                keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data=f"a/管理提现首页")])
                await self.sendMsg(text=text, keyboard=keyboard)
            else:
                return self.query.answer(text="提现申请存在")

