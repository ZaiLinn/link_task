import uuid
import logging
import datetime
import decimal
import math

from config import CallbackQuery, Client, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config, redis_client
from services.payment import OkayPay
from services.telegram_utils import msgNotify
from repositories.admin.withdrawals import Withdraw

logs = logging.getLogger(__name__)


class AdminWithdrawActionMixin:
    async def consentWithdraw(self,**kwargs):
        wid = kwargs.get('wid')
        myW = Withdraw()
        info = await myW.get_withdraw_info(id=wid[0])
        if info:
            okPya= OkayPay()
            ByTG = await okPya.censorUserByTG(data={'telegramID': info[13]})
            if ByTG.get('data').get('exist'):
                transfer_ = await okPya.transfer({'unique_id':info[4],'name': f"{bot_config['botName']}-用户佣金提现",
                                            'amount':info[2],'to_user_id':info[13],'coin':'USDT'})
                if transfer_.get('data') and transfer_.get('data').get('order_id'):
                    pay_time=datetime.datetime.now()
                    await myW.put_withdraw_consent(wid=wid[0],pay_time=pay_time,pay_type="OkPay",pay_order=transfer_.get('data').get('order_id'),label="OkPay提现成功")
                    await self.query.answer(text="《同意》用户提现操作成功",show_alert=True)
                    text=f"💰 提现成功-{info[2]} USDT\n\n" \
                         f"提现订单号:{info[4]}\n" \
                         f"提现时间:{info[5]}\n\n" \
                         f"OkPay订单号:`{transfer_.get('data').get('order_id')}`\n" \
                         f"到账时间:{pay_time.strftime('%y.%m.%d %H:%M:%S')}\n" \
                         f"请前往 @okpay 查看详情\n"
                    await self.client.send_message(chat_id=info[13],text=text)
                else:
                    await myW.put_withdraw_consent(wid=wid[0],label="OkPay提现成功")
                    await self.query.answer(text=f"订单已经转款成功请返回:{transfer_.get('msg')}", show_alert=True)
            else:
                await self.query.answer(text=f"用户未使用过OkPay已通知用户", show_alert=True)
                await self.client.send_message(chat_id=info[13], text=f"请前往 @okpay 先关注,下次再打款..")
            await self.withdrawInfo(wid=wid)

    async def rejectWithdraw(self,**kwargs):
        wid,reject = kwargs.get('wid'),kwargs.get('text')
        myW = Withdraw()
        info = await myW.get_withdraw_info(id=wid)
        if info and info[8] is None:
            balance_u = await myW.get_order_u_balance(user_id=info[1])
            order_id = uuid.uuid4().hex
            pay_time = datetime.datetime.now()
            if await myW.put_withdraw_reject(wid=wid,pay_time=pay_time,return_order=order_id,label=reject):
                if int(info[16])==0:
                    try:
                        await myW.post_create__order_u(order_id=order_id, price=info[2], order_type=0, balance=balance_u[0] + info[2],
                                                       user_id=info[1], link_id=info[4], label='提现失败退回金额')
                        text = f"💰 提现被拒绝-{info[2]} USDT\n\n" \
                               f"提现订单号:{info[4]}\n" \
                               f"提现时间:{info[5]}\n\n" \
                               f"退回订单号:`{order_id}`\n" \
                               f"退回时间:{pay_time.strftime('%y.%m.%d %H:%M:%S')}\n" \
                               f"拒绝原因:{reject}\n" \
                               f"请前往 钱包 查看详情\n"
                        await self.client.send_message(chat_id=info[13], text=text)
                    except RPCError as e:
                        logs.info(" ".join(str(value) for value in (e,)))
                    await msgNotify(msg=self.msg,text=f"拒绝提现成功:{reject},通知用户成功")
                else:
                    await msgNotify(msg=self.msg,text=f"拒绝提现成功:{reject},用户封号不用通知")
        await self.withdrawInfo(wid=[wid])

