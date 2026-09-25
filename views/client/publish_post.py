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


class PublishPostTask(BaseView):
    async def inputBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"➕{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())
    async def postTask(self,**kwargs):
        user=self.data.get("user")
        taskD = PublishDate()
        try:
            get_task = await taskD.load_user_task_interim(user=user[0])
            if get_task:
                await self.task_release_form(task=[get_task[0]])
        except RPCError as e:
            logs.info(" ".join(str(value) for value in (e,)))
    async def task_release_form(self,**kwargs):
        msg = await self.retChat()
        user = self.data.get('user')
        task_id = kwargs.get("task")[0]
        publish = PublishDate()
        task_info = await publish.get_task(id=task_id)
        groupObj = await publish.get_user_group(id=task_info[7])
        order_count = await MerchantIndex().get_order_out_count(user=user[0], order_type=0)
        try:
            text=f"**⛩任务发布⛩**\n\n" \
                 f"任务ID: {task_info[0]}\n" \
                 f"标题: {task_info[1] if task_info[1] else '未设置'}\n" \
                 f"单价: {task_info[2]}\n" \
                 f"数量: {'无限' if task_info[4]==0 else task_info[4]}\n" \
                 f"总价: {'无限' if task_info[4]==0 else task_info[2]*task_info[4]}\n" \
                 f"可用余额: {order_count[1] - order_count[0]}\n" \
                 f"绑定群/频:{f'[{groupObj[3] }]({groupObj[6]})' if groupObj else '未绑定'} \n\n" \
                 f"**任务条件规则:**\n" \
                 f"{'🔸必须有用户名' if task_info[9] == 1 else ''}" \
                 f"{'🔸昵称中文,' if task_info[10] == 1 else ''}" \
                 f"{'🔸昵称英文,' if task_info[11] == 1 else ''}" \
                 f"{'🔸昵称俄文,' if task_info[12] == 1 else ''}" \
                 f"{'🔸昵称阿拉伯,' if task_info[13] == 1 else ''}" \
                 f"{'🔸昵称日文,' if task_info[14] == 1 else ''}" \
                 f"{'🔸昵称韩文,' if task_info[15] == 1 else ''}" \
                 f"{'🔸昵称波斯' if task_info[16] == 1 else ''}" \
                 f"\n条件规则说明:\n被邀请用户必须满足设置规则才算有效.\n\n" \
                 f"任务状态: {'🔴 未上线' if task_info[5]==0 else '🟢 已上线'}\n\n" \
                 f"说明：\n未设置数量默认为不限数量,每次成功任务将会冻结相应单价的账号余额,直至余额为最低{bot_config['stop_balance']}u停止推广.\n" \
                 f"冻结金额:\n每次邀请都会冻结金额在审核后有效的邀请将会扣除，无效的邀请金额将会返还到账号余额\n"
            keyboard=[]
            keyboard.append([InlineKeyboardButton("✂️设置标题",callback_data=f"r/商家发布输入?text=请输入任务标题:{task_info[0]}"),
                             InlineKeyboardButton("✂️设置单价",callback_data=f"r/商家发布输入?text=请输入任务单价:{task_info[0]}"),
                             InlineKeyboardButton("💕 绑定群/频", callback_data=f"r/商家发布选择群?task={task_info[0]}")
                             # ,InlineKeyboardButton("✂️设置数量",callback_data=f"r/商家发布输入?text=请输入任务数量:{task_info[0]}")
                             ])
            if user[5] in [1,2]:
                keyboard.append([InlineKeyboardButton(f"📉 ({task_info[17]}%)设置有效百分比",callback_data=f"r/商家发布输入?text=请输入百分比:{task_info[0]}:例88")])
            keyboard.append([InlineKeyboardButton("--任务条件类型(昵称或用户名)--", callback_data=f"-")])
            keyboard.append([InlineKeyboardButton(f"{'🔸' if task_info[10]==1 else ''}中文昵称", callback_data=f"r/商家发布规则?task={task_info[0]}&cn={task_info[10]}"),
                            InlineKeyboardButton(f"{'🔸' if task_info[9]==1 else ''}必须有用户名", callback_data=f"r/商家发布规则?task={task_info[0]}&username={task_info[9]}")])
            keyboard.append([InlineKeyboardButton(f"{'🔓  未开启-私密群审核(不用申请)' if task_info[18] == 0 else '🔐 已开启-私密群审核(需要申请)'} ",callback_data=f"r/商家发布私密审核?id={task_info[0]}&nr={task_info[18]}")])
            keyboard.append([InlineKeyboardButton("✅ 确认提交",callback_data=f"r/商家发布提交?task={task_info[0]}")])
            keyboard.append([InlineKeyboardButton("❌ 取消发布", callback_data=f"r/商家发布取消?task={task_info[0]}"),
                             InlineKeyboardButton("↩️ 返回", callback_data=f"r/商家首页")])
            await self.sendMsg(text=text,keyboard=keyboard)
        except RPCError as e:
            logs.info(" ".join(str(value) for value in (e,)))
    async def set_task_state(self,**kwargs):
        id,nr = kwargs.get("id")[0],kwargs.get("nr")[0]
        await PublishDate().put_task_state(id=id,nr=(1 if int(nr) ==0 else 0))
        await self.task_release_form(task=kwargs.get("id"))
    async def detect_rule(self,**kwargs):
        task = kwargs.get("task")
        pubD = PublishDate()
        for key,value in kwargs.items():
            if key !="task":
                await pubD.put_task_info(id=task[0],key=f"is_{key}",value=1 if int(value[0])==0 else 0)
        await self.task_release_form(task=task)
    async def opt_group(self,**kwargs):
        user = self.data.get('user')
        task = kwargs.get('task')[0]
        if user:
                my_group =await PublishDate().get_user_group_list(user=user[0])
                text = "**选择频道**\n\n" \
                       "选择以下按钮绑定到任务\n\n" \
                       "图示：🟢正常🟡无权限⚫已退群🔴被禁用\n" \
                       "请确认是否已经将机器人拉入并设置管理员\n" \
                       "点下方按钮可邀请进频道或群,出现权限检测正常后点击刷新" \
                       "👇请选择一个提交"
                keyboard = []

                if my_group:
                    for group in my_group:
                        ty_emoji = "🟢"
                        if group[9] == 1:
                            ty_emoji = "🟡"
                        elif group[9] == 2:
                            ty_emoji = "⚫"
                        elif group[9] == 10:
                            ty_emoji = "🔴"
                        keyboard.append([InlineKeyboardButton(f"{ty_emoji}-{group[3]}",callback_data=f"r/商家发布关联群?group={group[0]}&task={task}")])
                else:
                    keyboard.append([InlineKeyboardButton("⚠️未找到到群/频道,请邀请机器人入群", callback_data=f"-")])
                keyboard.append([InlineKeyboardButton("🌸邀请进群组",url=f"https://t.me/{bot_config['botUserName'].replace('@', '')}?startgroup=true"),
                                 InlineKeyboardButton("🏵️邀请进频道",url=f"https://t.me/{bot_config['botUserName'].replace('@', '')}?startchannel=true")])
                keyboard.append([InlineKeyboardButton("🔄 刷新", callback_data=f"r/商家发布选择群?task={task}"),
                                 InlineKeyboardButton("↩️ 返回", callback_data=f"r/商家发布表单?task={task}")])
                await self.sendMsg(text=text,keyboard=keyboard)
            # else:
            #     return await self.client.answer_callback_query(self.query.id, text="⚠️未找到需要推广到群/频道，请先邀请机器人进入",show_alert=True)
    async def be_group_task(self,**kwargs):
        try:
            group,task = kwargs.get("group")[0],kwargs.get("task")[0]
            publish = PublishDate()
            groupObj = await publish.get_user_group(id=group)
            if groupObj[9] == 0:
                be_task = await publish.be_group_to_task(group=group, task=task)
                if be_task:
                    await self.task_release_form(task=[task])
                else:
                    await self.query.answer(text="绑定任务失败请检查", show_alert=True)
            else:
                await self.query.answer(text="绑定任务失败请:请选择<🟢正常>状态机器人", show_alert=True)
        except Exception as e:
            logs.info(" ".join(str(value) for value in (e,)))
    async def task_release_cancel(self,**kwargs):
        task =kwargs.get('task')[0]
        default =await PublishDate().default_task(id=task)
        if default:
            return await PublishIndex(Client=self.client,Query=self.query,Data=self.data).index()
        else:
            await self.query.answer(text="取消任务失败，请联系管理员",show_alert=True)
    async def submit_task(self,**kwargs):
        msg = await self.retChat()
        task_id = kwargs.get("task")[0]
        pubObj = PublishDate()
        taskDate =await pubObj.get_task(id=task_id)
        if taskDate:
            if not taskDate[1]:
                return await self.query.answer(text="⛔ 您还未设置任务标题",show_alert=True)
            elif not taskDate[7]:
                return await self.query.answer(text="⛔ 您还未绑定频道/群组",show_alert=True)
            order_count = await MerchantIndex().get_order_out_count(user=self.data.get('user')[0], order_type=0)
            if order_count[1] - order_count[0] <= taskDate[2]*taskDate[4]:
                return await self.query.answer(text=f"⛔ 您的余额少于最低发布金额 {bot_config['post_amount']}请充值",show_alert=True)
            elif taskDate[4]==0 and (order_count[1] - order_count[0]) <=int(bot_config['post_amount']):
                return await self.query.answer(text=f"⛔ 无限数量模式下请保证可用余额大于{bot_config['post_amount']}u", show_alert=True)
            sub = await pubObj.put_task_info(id=task_id,key="state",value=1)
            if sub:
                await self.query.answer(text="✅ 发布任务成功",show_alert=True)
                return await PublishIndex(Client=self.client, Query=self.query, Data=self.data).index()
# 任务管理
