import uuid
import logging
import datetime
import math

from config import ForceReply, InlineKeyboardButton, RPCError, bot_config
from services.cache import Var
from services.payment import OkayPay
from services.task_lifecycle import TaskOperation
from services.telegram_utils import msgNotify
from repositories.client.publish import MerchantIndex, PublishDate
from repositories.client.settlements import SettlementDate
from repositories.client.tasks import TaskDate
from repositories.client.wallets import MerchantWalletDate
from views.base import BaseView

logs = logging.getLogger(__name__)


class MerchantWallet(BaseView):
    async def inputBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"💰{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())
    async def index(self, **kwargs):
            user = self.data.get("user")[0]
            OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
            taskState = int(kwargs.get('state')[0]) if kwargs.get('state') else -1
            MWDate = MerchantWalletDate()
            order = await MWDate.get_order_out_list(OFFSET=OFFSET, LIMIT=LIMIT, user=user,order_type=taskState)
            order_count = await MWDate.get_order_out_count(user=user,order_type=taskState)
            keyboard = []
            text = f"商家-钱包\n\n" \
                   f"账户余额:{order_count[2] or 0}\n" \
                   f"冻结余额:{order_count[1] or 0}\n" \
                   f"说明:订单号-变动金额" \
                   f"点击下方按钮进行更多操作\n"
            if order and order_count:
                totalPages, currentPage = math.ceil(order_count[0] / LIMIT), math.ceil(OFFSET / LIMIT) + 1
                upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
                for key in order:
                    keyboard.append([InlineKeyboardButton(f"{key[7]}|{'-' if key[3]==1 else '+'}{key[2]}|余额{key[4]}",
                                                          callback_data=f"r/商家钱包订单详情?order={key[0]}&state={taskState}")])
                keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                      callback_data=f"r/商家钱包?page={upPage}&state={taskState}" if upPage >= 0 else '-'),
                                 InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                                 InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                      callback_data=f"r/商家钱包?page={dowPage}&state={taskState}" if currentPage != totalPages else '-')])
            else:
                keyboard.append([InlineKeyboardButton(f"空/未发现记录", callback_data="-")])
            keyboard.append([InlineKeyboardButton(f"{'🌕' if taskState == -1 else '🌑'} 全部",callback_data=f"r/商家钱包?state=-1"),
                             InlineKeyboardButton(f"{'🌕' if taskState == 1 else '🌑'} 支出",callback_data=f"r/商家钱包?state=1"),
                             InlineKeyboardButton(f"{'🌕' if taskState == 0 else '🌑'} 收入",callback_data=f"r/商家钱包?state=0")])
            keyboard.append([InlineKeyboardButton(f"💵 在线充值", callback_data="r/商家钱包充值类型")])
            keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data="r/商家首页")])
            await self.sendMsg(text=text, keyboard=keyboard)

    async def order_info(self,**kwargs):
        taskState=kwargs.get('state')[0]
        try:
            MWDate = MerchantWalletDate()
            order =await MWDate.get_order_info(order=kwargs.get('order')[0])
            if order:
                text = "**商家-钱包账单详情**\n\n" \
                       f"订单号:{order[1]}\n" \
                       f"金额:{'-' if order[3]==1 else '+'}{order[2]}\n" \
                       f"余额:{order[4]}\n" \
                       f"备注:{order[7]}\n" \
                       f"时间:{order[8]}\n\n"
                if order[3]==0:
                    # 充值详细
                    if order[7]!='手动充值':
                        pay_info = await MWDate.get_order_m_pay_info(order_id=order[6], user=order[5])
                        if pay_info:
                            # 充值详细
                            text += f"发起时间:{pay_info[9]}\n" \
                                    f"充值订单:{pay_info[2]}\n" \
                                    f"充值金额:{pay_info[4]}\n" \
                                    f"支付状态:{'🟢 已付款' if pay_info[7] == 1 else '⚪ 未付款'}\n" \
                                    f"充值渠道:{pay_info[5]}\n" \
                                    f"渠道订单:{pay_info[6]}\n" \
                                    f"付款时间:{pay_info[8]}\n\n"
                elif order[3]==1:
                    # 支出详细
                    zhi_info = await  MWDate.get_order_m_jie_info(order_id=order[1])
                    if zhi_info:
                        text += f"**支出订单信息:**\n" \
                                f"订单号:{zhi_info[1]}\n" \
                                f"用户:{zhi_info[6]}\n" \
                                f"任务:{zhi_info[3]}\n" \
                                f"链接:{zhi_info[5]}\n" \
                                f"单价:{zhi_info[4]}\n" \
                                f"日期:{zhi_info[2].strftime('%Y-%m-%d')}\n"
                keyboard=[]
                keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data=f"r/商家钱包?state={taskState}")])
                await self.sendMsg(text=text,keyboard=keyboard)
            else:
                await self.query.answer(text="订单号不存在")
        except Exception as e:
            logs.info(" ".join(str(value) for value in (e,)))
    async def pay_index(self,**kwargs):
        text = f"**选择支付方式**\n\n" \
               f"请选择付款方式输入充值的金额,\n最低{bot_config['lowest_balance']}u\n\n" \
               f"👇请选择您的付款方式"
        keyboard = [
            [InlineKeyboardButton("💵 OkPay 付款", callback_data=f"r/商家钱包输入?text=请输入OkPay充值金额:")],
            [InlineKeyboardButton(f"↩️ 返回", callback_data="r/商家钱包")]
        ]
        await self.sendMsg(text=text,keyboard=keyboard)
    async def okpay_pay(self,**kwargs):
        user = self.data.get('user')
        msg=kwargs.get('msg')
        MWDate = MerchantWalletDate()
        order_id = uuid.uuid4().hex
        try:
            order_info = {
                'unique_id': order_id,
                'name': f"{bot_config['botName']}",
                'amount': msg,
                'return_url': bot_config.get('callback_address'),
                'coin': "USDT"
            }
            ok = OkayPay()
            ok_order = await ok.pay_link(data=order_info)
            logs.info(" ".join(str(value) for value in (ok_order,)))
            if ok_order.get('code') == 200:
                data = ok_order.get('data')
                post_pay=await MWDate.post_order_pay_info(user_id=user[0],order_id=order_id,price=msg,transaction_id=data.get('order_id'),pyt_type="okpay")
                text=f"**订单信息**\n\n" \
                     f"用户ID:{user[1]}\n" \
                     f"用户昵称:{user[3]}\n" \
                     f"充值金额:{msg}\n" \
                     f"订单号:{order_id}\n" \
                     f"👇点击按钮前往OkPay进行支付"
                keyword = [[InlineKeyboardButton("🏠 立即支付", url=ok_order['data']['pay_url'])],
                           [InlineKeyboardButton(f"↩️ 返回钱包", callback_data="r/商家钱包")]]
                await self.sendMsg(text=text,keyboard=keyword)
            else:
                text = f"**订单信息**\n\n创建订单错误请返回重试"
                keyword = [[InlineKeyboardButton(f"↩️ 返回钱包", callback_data="r/商家钱包")]]
                await self.sendMsg(text=text, keyboard=keyword)
        except Exception as e:
            logs.info("empty debug marker")
