import uuid
import logging
import decimal
import math

from config import CallbackQuery, Client, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config, datetime, redis_client
from public.logger import LoggerConfig
from services.telegram_utils import msgNotify
from repositories.admin.users import UserDate

logs = LoggerConfig('user', 'logs/main.log').get_logger()


class AdminUserWalletMixin:
    async def pay_user(self,**kwargs):
        price,user_id=kwargs.get('price'),kwargs.get('user_id')
        userD = UserDate()
        balance = await userD.get_order_m_balance(user_id=user_id)
        order_id = uuid.uuid4().hex
        post_order_m = await userD.post_order_m_info(order_id=order_id, price=price, order_type=0,
                                                   balance=balance + price, user_id=user_id, label="手动充值")
        await self.userInfo(user=[user_id])
        if post_order_m:
            text = f"💳 充值成功 {price} USDT\n\n" \
                   f"充值前余额:{balance}\n" \
                   f"当前余额:{balance + price}\n"
            await msgNotify(msg=self.msg,text=text)
        else:
            text = f"💳 充值失败 {price} USDT\n\n" \
                   f"充值前余额:{balance}\n"
            await msgNotify(msg=self.msg, text=text)

    async def checkCalculation(self,**kwargs):
        userID = kwargs.get('user')
        try:
            myW = UserDate()
            info = await myW.get_check_order_out_list(user=userID[0])
            if info:
                chae=decimal.Decimal(0.00)
                upOrder={}
                for order in info:
                    if order[3]==0:
                        settlenment = await myW.get_check_settlenment(order=order[1])
                        if settlenment[5]!=order[2]:
                            chae+= decimal.Decimal(order[2])-decimal.Decimal(settlenment[5])
                            balance= upOrder[4]+settlenment[5]
                            await myW.put_check_order(price=settlenment[5],balance=balance,
                                                      label=f"{order[7]}\n修复结算:结算id-{settlenment[0]},错误金额:{order[2]},正确金额:{settlenment[5]},请前往结算查看结算id核对",
                                                      order_id=order[0],user_id=order[5])
                            order=await myW.get_check_order_info(order=order[0])
                        else:
                            balance = upOrder[4] + order[2]
                            if balance != order[4]:
                                await myW.put_check_order(price=order[2], balance=balance,label=f"{order[7]}",
                                                          order_id=order[0], user_id=order[5])
                                order = await myW.get_check_order_info(order=order[0])
                    elif order[3]==1:
                        balance = upOrder[4] - order[2]
                        if balance!=order[4]:
                            await myW.put_check_order(price=order[2], balance=balance,label=f"{order[7]}",
                                                      order_id=order[0], user_id=order[5])
                            order = await myW.get_check_order_info(order=order[0])
                    upOrder=order
                await msgNotify(self.query.message,text=f"修复完毕:多结算{chae}")
                await self.query.answer(text=f"修复完毕:多结算{chae}",show_alert=True)
        except Exception as  e:
            logs.error(f"订单修复错误:{e}")

