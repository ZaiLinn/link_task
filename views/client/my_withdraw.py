import uuid
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


class MyWithdraw(BaseView):
    async def inputBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"🧧{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())
    async def index(self,**kwargs):
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
        taskState = kwargs.get('state')[0] if kwargs.get('state') else 0
        user = self.data.get('user')
        myW = MyWithdrawDate()
        withdraw = await myW.get_withdraw_user_list(LIMIT=LIMIT,OFFSET=OFFSET,  user_id=user[0], state=taskState)
        withdraw_count = await myW.get_withdraw_user_count(user=user[0], state=taskState)
        keyboard = []
        text = f"👤用户-我的提现️\n\n" \
               f"可提现余额:{withdraw_count[0]}\n" \
               f"提现数:{withdraw_count[1]}\n" \
               f"提现金额:{withdraw_count[2]}\n" \
               f"手续费:%{bot_config['WithdrawalRate']}\n" \
               f"点击下方任务按钮操作提现\n" \
               f"说明:提交申请后24小时内会通过okPay转入\n"
        if withdraw:
            totalPages, currentPage = math.ceil(withdraw_count[1] / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in withdraw:
                keyboard.append([InlineKeyboardButton(f"🧧{key[5]}-提现{key[2]} 👈",callback_data=f"r/任务提现详情?id={key[0]}&ups={taskState}")])
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"r/任务提现?page={upPage}&state={taskState}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"r/任务提现?page={dowPage}&state={taskState}" if currentPage != totalPages else '-')])
        else:
            keyboard.append([InlineKeyboardButton(f"空/未发现", callback_data="-")])
        keyboard.append([InlineKeyboardButton(f"{'🌕' if int(taskState) == 0 else ''} 待打款",callback_data=f"r/任务提现?state=0"),
                         InlineKeyboardButton(f"{'🌕' if int(taskState) == 1 else ''} 已打款",callback_data=f"r/任务提现?state=1"),
                         InlineKeyboardButton(f"{'🌕' if int(taskState) == 2 else ''} 已失败",callback_data=f"r/任务提现?state=2")])
        keyboard.append([InlineKeyboardButton(f"💸 立即提现", callback_data="r/任务输入?text=请输入提现金额:")])
        keyboard.append([InlineKeyboardButton("🏠 任务大厅", callback_data="r/任务首页"),
                         InlineKeyboardButton("↩️ 返回", callback_data="r/任务用户中心")])
        await self.sendMsg(text=text, keyboard=keyboard,var=True)
    async def withdrawApply(self,**kwargs):
        user,price = self.data.get('user'),kwargs.get('price_input')
        myW=MyWithdrawDate()
        try:
            okPya= OkayPay()
            ByTG = okPya.censorUserByTG(data={'telegramID': user[1]})
            if ByTG.get('data').get('exist'):
                balance = await myW.get_u_balance(user=user[0])
                balance=balance-price
                if balance >= 0:
                    order_id = uuid.uuid4().hex
                    reduce = await myW.post_create_order_u_list(order_id=order_id, price=price, order_type=1, balance=balance, user_id=user[0],label="用户提现")
                    if reduce:
                        handling_fee=price*decimal.Decimal((int(bot_config["WithdrawalRate"])/100))
                        price -= handling_fee
                        await myW.post_withdraw_list_u(user_id=user[0],price=price,state=0,link_id=order_id,label='申请提现',handling_fee=handling_fee)
                        await self.index()
                else:
                    await self.index()
                    await msgNotify(msg=self.msg, text=f"提现失败:余额不足")
            else:
                await self.msg.reply_text(text=f"提现失败:\n请前往 @okpay 钱包先关注后重新申请")
                await self.index()
        except Exception as e:
            logs.info(" ".join(str(value) for value in (e,)))
            await msgNotify(msg=self.msg,text=f"提现失败:{e}")
    async def withdrawInfo(self,**kwargs):
        wid,ups = kwargs.get('id'),kwargs.get('ups')
        if wid and ups:
            myW=MyWithdrawDate()
            info = await myW.get_withdraw_info(id=wid[0])
            if info:
                wState = {0: '打款中',1:'已打款',2:'已拒绝'}
                text = f"**👤用户-提现详情**\n\n" \
                       f"账号ID：{info[12]}\n" \
                       f"用户名：{info[13]}\n" \
                       f"昵称：{info[14]}\n" \
                       f"余额：{info[25]}\n\n" \
                       f"**提现信息**\n" \
                       f"提现时间：{info[5]}\n"\
                       f"提现ID：{info[0]}\n" \
                       f"扣款订单号：{info[4]}\n" \
                       f"提现金额：{info[24]}U\n" \
                       f"手续费：{info[11]}U\n" \
                       f"实际到账：{info[2]}U\n" \
                       f"状态：{wState.get(info[3])}\n" \
                       f"提现备注：{info[7]}\n"
                if info[3]==2:
                    text+=f"\n退款订单号：{info[8]}"
                elif info[3]==1:
                    text+=f"\n打款渠道：{info[9]}\n" \
                          f"打款订单号: {info[10]}"

                keyboard=[]
                var = await Var(Id=(await self.retChat()).chat.id).read()
                keyboard.append([InlineKeyboardButton("↩️ 返回",callback_data=f"{var if 'r/任务提现' in var else 'r/任务提现'}")])
                await self.sendMsg(text=text,keyboard=keyboard)
            else:
                return self.query.answer(text="提现申请存在")
