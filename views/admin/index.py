import logging
from config import BotCommand, ForceReply, InlineKeyboardButton
from services.configuration import get_config
from views.base import BaseView

logs = logging.getLogger(__name__)


class Admin(BaseView):
    async def index(self, **kwargs):
        msg = await self.retChat()
        text = "✨✨✨✨✨✨✨✨✨✨✨✨\n\n" \
               "======**🏆 后台管理 🏆**======\n\n" \
               "🌟**欢迎管理员:**🌟\n" \
               "  ✅可以在此管理机器人功能"
        keyboard = [
            [InlineKeyboardButton("☸️ 机器人配置", callback_data="a/机器人配置"),
             InlineKeyboardButton("📇 结算申诉", callback_data="a/管理结算首页")],
            [InlineKeyboardButton("💸 提现审批", callback_data="a/管理提现首页"),
            InlineKeyboardButton("💰 资金流水", callback_data="a/资金充值流水")],
            [InlineKeyboardButton("👨‍💻 用户管理", callback_data="a/用户管理")],
        ]
        await self.sendMsg(text=text, keyboard=keyboard)
    async def config(self, **kwargs):
        bot_config = get_config()
        okpay_token = bot_config.get('OkPay_token') or ''
        okpay_token_text = '未配置' if not okpay_token else f"{okpay_token[:4]}****{okpay_token[-4:]}"
        text = "✨✨✨✨✨✨✨✨✨✨✨✨\n\n" \
               "======**🏆 机器人配置 🏆**======\n\n" \
               f"**🔸初始化菜单:** 初始化用户菜单命令\n" \
               f"**🔸机器人名字:** {bot_config['botName']}\n" \
               f"**🔸机器人账号:** {bot_config['botUserName']}\n" \
               f"**🔸首页欢迎词:**\n'{bot_config['indexTxt']}'\n" \
               f"**🔸视频介绍:** {'🟢 已上传' if len(bot_config['video']) > 20 else '🚫 未上传'}\n" \
               f"**🔸管理群组ID:** `{bot_config['adminGroup']}`\n" \
               f"**🔸客服群组:** {bot_config['msgGroup']}\n" \
               f"**🔸教程频道ID:** `{bot_config['publicGroup']}`\n" \
               f"**🔸访问限制:** {bot_config['restrict_limit']} (60秒问次数超过禁用5分钟)\n" \
               f"**🔸用户预警数:** {bot_config['user_alarm']} (用户同时进多少任务群预警)\n" \
               f"\n======**🛃 费率设置 🛃**======\n" \
               f"**🔸提现费率:** {bot_config['WithdrawalRate']}%\n" \
               f"**🔸商家费率:** {bot_config['MerchantRate']}%\n" \
               f"\n======**🔆 资金设置 🔆**======\n" \
               f"**🔸最低充值金额:** {bot_config['lowest_balance']} \n" \
               f"**🔸最低发布金额:** {bot_config['post_amount']} \n" \
               f"**🔸停止推广余额:** {bot_config['stop_balance']} \n" \
               f"**🔸提醒充值余额:** {bot_config['remind_balance']} \n" \
               f"**🔸最低提现金额:** {bot_config['lowest_withdraw']} \n" \
               f"\n======**🏦 OkPay设置 🏦**======\n" \
               f"**🔸商户ID:**`{bot_config['OkPay_id']}`\n" \
               f"**🔸商户Token:**`{okpay_token_text}`\n" \
               f"**🔸回调地址:**`{bot_config['callback_address']}`" \

        keyboard = []
        keyboard.append([InlineKeyboardButton(f"初始化", callback_data="a/初始化菜单")])
        keyboard.append([InlineKeyboardButton(f"改机器人名字", callback_data="a/修改配置?text=请输入机器人名"),
             InlineKeyboardButton(f"改机器人账号", callback_data="a/修改配置?text=请输入机器人账号:例子:@xxbot"),
                         InlineKeyboardButton(f"改首页欢迎词", callback_data="a/修改配置?text=请输入首页欢迎词")])
        keyboard.append([InlineKeyboardButton(f"改视频介绍", callback_data="a/修改配置?text=请上传视频介绍"),
                         InlineKeyboardButton(f"改管理群组", callback_data="a/修改配置?text=请输入管理群组:群组ID"),
            InlineKeyboardButton(f"改客服群组", callback_data="a/修改配置?text=请输入客服群组:群组账号")])
        keyboard.append([InlineKeyboardButton(f"改教程频道", callback_data="a/修改配置?text=请输入教程频道:频道ID"),
             InlineKeyboardButton(f"改访问限制", callback_data="a/修改配置?text=请输入访问限制:回复数字1到60"),
                         InlineKeyboardButton(f"改用户预警数", callback_data="a/修改配置?text=请输入用户预警数:回复数字")])

        keyboard.append([InlineKeyboardButton(f"======**🛃 费率设置 🛃**======", callback_data="-")])
        keyboard.append([InlineKeyboardButton(f"改提现费率", callback_data="a/修改配置?text=请输入提现费率:回复100内数字"),
             InlineKeyboardButton(f"改商家费率", callback_data="a/修改配置?text=请输入商家费率:回复100内数字")])

        keyboard.append([InlineKeyboardButton(f"======**🔆 资金设置 🔆**======", callback_data="-")])
        keyboard.append([InlineKeyboardButton(f"最低充值金额", callback_data="a/修改配置?text=请输入最低充值金额:"),
             InlineKeyboardButton(f"最低发布金额", callback_data="a/修改配置?text=请输入最低发布金额:")])
        keyboard.append([InlineKeyboardButton(f"停止推广余额", callback_data="a/修改配置?text=请输入停止推广余额:"),
             InlineKeyboardButton(f"提醒充值余额", callback_data="a/修改配置?text=请输入提醒充值余额:"),
             InlineKeyboardButton(f"最低提现金额", callback_data="a/修改配置?text=请输入最低提现金额:")])
        keyboard.append([InlineKeyboardButton(f"======**🏦 OkPay设置 🏦**======", callback_data="-")])
        keyboard.append([InlineKeyboardButton(f"商户ID", callback_data="a/修改配置?text=请输入商户ID:"),
             InlineKeyboardButton(f"商户Token", callback_data="a/修改配置?text=请输入商户Token:")])
        keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data="a/管理首页")])
        await self.sendMsg(text=text, keyboard=keyboard)
    async def modifBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"📲{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())
    async def initialization(self,**kwargs):
        setComm = [BotCommand("start", "开始"), BotCommand("role", "切换角色"), BotCommand("task", "任务大厅"),BotCommand("mc", "商家中心"), BotCommand("help", "帮助")]
        initial =await self.client.set_bot_commands(setComm)
        logs.info(" ".join(str(value) for value in (initial,)))
        if initial:
            await self.query.answer(text=f'初始化菜单成功', show_alert=True)
