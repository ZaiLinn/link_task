import uuid
import logging
import datetime
import math

from config import CallbackQuery, Client, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config
from public.logger import LoggerConfig
from services.cache import Var
from services.telegram_utils import msgNotify
from repositories.admin.settlements import SettlementDate

logs = LoggerConfig('admin', 'logs/main.log').get_logger()


class AdminSettlementActionMixin:
    async def confirm(self,**kwargs):
        settlement = kwargs.get('set')[0]
        try:
            Settl = SettlementDate()
            info = await Settl.get_confirm_info(settlement=settlement)
            if info and info[5] > 0:
                bark_order = await Settl.get_order_m_balance(user_id=info[2])
                bark_order_u = await Settl.get_order_u_balance(user_id=info[3])
                balance = bark_order[0] - info[5]
                balance_u = bark_order_u[0] + info[5]
                if balance >= 0 and balance_u > bark_order_u[0]:
                    order_id = uuid.uuid4().hex
                    reduce = await Settl.post_create__order_m(order_id=order_id, price=info[5], order_type=1,
                                                              balance=balance, user_id=info[2], label="任务结算")
                    if reduce:
                        # 给用户加余额
                        order_id_u = uuid.uuid4().hex
                        reduce = await Settl.post_create__order_u(
                            order_id=order_id_u, price=info[5], order_type=0, balance=balance_u,
                            user_id=info[3], link_id=order_id, label='任务结算')
                        if reduce and await Settl.put_settlement_info(settlement=settlement, pay_order=order_id,
                                                                      income_order=order_id_u, label="申诉结算被管理员通过"):
                            await self.query.answer(text="结算成功", show_alert=True)
                            await self.index()
                            text = f"💳 申诉结算成功\n\n" \
                                   f"结算任务:{info[6]}\n"\
                                   f"结算金额:{info[5]} USDT💰\n"\
                                   f"结算日期:{info[1].strftime('%Y-%m-%d')}\n\n"\
                                   f"备注:申诉结算被管理员通过"
                            await self.client.send_message(chat_id=info[4],text=text)
                            # await self.client.send_message(chat_id=info[7],text=text)
                    else:
                        await self.query.answer(text="扣款错误", show_alert=True)
                else:
                    await self.query.answer(text="余额错误", show_alert=True)
            else:
                logs.info(" ".join(str(value) for value in ("结算金额错误",)))

                await self.query.answer(text="结算金额错误", show_alert=True)
        except (Exception,RPCError) as e:
            logs.critical(f"发生错误:{e}")

    async def tou_confirm(self,**kwargs):
        settlement = kwargs.get('set')[0]
        try:
            Settl = SettlementDate()
            info = await Settl.get_confirm_info(settlement=settlement)
            if info and info[5] > 0:
                bark_order = await Settl.get_order_m_balance(user_id=info[2])
                bark_order_u = await Settl.get_order_u_balance(user_id=info[3])
                balance = bark_order[0] - info[5]
                balance_u = bark_order_u[0] + info[5]
                if balance >= 0 and balance_u > bark_order_u[0]:
                    order_id = uuid.uuid4().hex
                    reduce = await Settl.post_create__order_m(order_id=order_id, price=info[5], order_type=1,
                                                              balance=balance, user_id=info[2], label="任务结算")
                    if reduce:
                        # 给用户加余额
                        if reduce and await Settl.put_reject_settlement_info(settlement=settlement,label="申诉被管理员拒绝"):
                            await self.query.answer(text="结算成功", show_alert=True)
                            await self.index()
                            text = f"⛔ 申诉结算失败\n\n" \
                                   f"结算任务:{info[6]}\n"\
                                   f"结算金额:{info[5]} USDT💰\n"\
                                   f"结算日期:{info[1].strftime('%Y-%m-%d')}\n\n"\
                                   f"备注:结算已过期,申诉应在结算日24小时内申诉."
                            await self.client.send_message(chat_id='5692641141',text=text)
                            # await self.client.send_message(chat_id=info[4],text=text)
                    else:
                        await self.query.answer(text="扣款错误", show_alert=True)
                else:
                    await self.query.answer(text="余额错误", show_alert=True)
            else:
                logs.info(" ".join(str(value) for value in ("结算金额错误",)))
                await self.query.answer(text="结算金额错误", show_alert=True)
        except (Exception,RPCError) as e:
            logs.critical(f"发生错误:{e}")

    async def reject(self,**kwargs):
        settlement = kwargs.get('set')[0]
        try:
            Settl = SettlementDate()
            task_log_reject=await Settl.put_reject_settlement_info(settlement=settlement,label="申诉结算被管理员拒绝")
            if task_log_reject:
                info = await Settl.get_confirm_info(settlement=settlement)
                logs.info(" ".join(str(value) for value in (info,)))
                await self.index()
                text = f"⛔ 申诉结算被拒绝\n\n"\
                f"结算任务:{info[6]}\n"\
                f"结算金额:{info[5]} USDT💰\n"\
                f"结算日期:{info[1].strftime('%Y-%m-%d')}\n\n"\
                f"备注:申诉结算被管理员拒绝"
                # await self.client.send_message(chat_id=info[4], text=text)
                await self.client.send_message(chat_id=info[7], text=text)
            else:
                await msgNotify(msg=self.msg, text="拒绝结算失败")
        except Exception as e:
            logs.info(" ".join(str(value) for value in ('拒绝审核',e,)))
            await msgNotify(msg=self.msg, text=f"拒绝结算错误:{e}",times=10)

