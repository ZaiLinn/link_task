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


class PublishIndex(BaseView):
    async def index(self,**kwargs):
        user = self.data.get("user")
        order_count = await MerchantIndex().get_order_out_count(user=user[0], order_type=0)
        text = f"**⛩商户中心⛩️**\n\n" \
               f"余额:{order_count[1]}\n" \
               f"冻结:{order_count[0]}\n" \
               f"可用余额:{order_count[1] - order_count[0]}\n\n" \
               f"❕ 说明:可在商户中心进行发布,可用余额少于{bot_config['stop_balance']}任务将会暂停\n\n" \
               f"💸 推广商家:发布任务,推广您的链接\n\n"
        keyboard = []
        keyboard.append([InlineKeyboardButton("➕ 发布新任务",callback_data="r/商家发布")])
        keyboard.append([InlineKeyboardButton("💼 任务列表",callback_data="r/商家任务列表"),
                         InlineKeyboardButton("📋 结算管理",callback_data="r/商家结算管理")])
        keyboard.append([InlineKeyboardButton("💰 钱包(查看余额)",callback_data="r/商家钱包"),InlineKeyboardButton(f"💸 在线充值", callback_data="r/商家钱包充值类型")])
        keyboard.append([InlineKeyboardButton("🏛️ 任务大厅",callback_data="r/判断角色?type=task")])
        await self.sendMsg(text=text, keyboard=keyboard)
