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


class TaskIndex(BaseView):
    async def inputBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"🧧{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())
    async def index(self,**kwargs):
        user = self.data.get("user")
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
        search = kwargs.get('search')[0] if kwargs.get('search') else None
        taskSort = kwargs.get('sort')[0] if kwargs.get('sort') else 'all'
        taskData = TaskDate()
        task = await taskData.get_task_list(OFFSET=OFFSET, LIMIT=LIMIT, search=search,user=user[0], sort=taskSort)
        keyboard = []
        text = f"⛩️用户-任务大厅⛩️\n\n"
        task_count = await taskData.get_task_index_count(sort=taskSort,user=user[0])
        text += f"任务总数:{task_count[0]}个\n" \
                f"上线中的任务数:{task_count[1]}个\n" \
                f"您领取的任务数:{task_count[2]}个(可去用户中心查看)\n" \
                f"当前分类任务数:{task_count[3]}个\n\n" \
                f"条件分类按钮图释：💼全部👥账号+昵称👤账号🗣昵称♾️无条件\n\n" \
                f"点击下方任务按钮领取任务链接"
        if task:
            totalPages, currentPage = math.ceil(task_count[3] / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in task:
                keyboard.append([InlineKeyboardButton(f"🧧{key[2]}U-{key[1]} 👈",
                                                      callback_data=f"r/任务信息?task={key[0]}")])
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"r/任务首页?page={upPage}&sort={taskSort}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"r/任务首页?page={dowPage}&sort={taskSort}" if currentPage != totalPages else '-')])
        else:
            keyboard.append([InlineKeyboardButton(f"空/未发现", callback_data="-")])
        sorlZh={'all':'所有未接','un':'必须账号+昵称','u':'必须账号','n':'必须昵称符合','no':'无条件'}
        keyboard.append([InlineKeyboardButton(f"{'▶' if taskSort == 'all' else ''} 💼 任务筛选({sorlZh.get(taskSort)})",callback_data=f"r/任务首页?sort=all")])
        keyboard.append([InlineKeyboardButton(f"{'▶' if taskSort=='un' else ''} 👥 账昵", callback_data=f"r/任务首页?sort=un"),
                         InlineKeyboardButton(f"{'▶' if taskSort=='u' else ''} 👤 账号", callback_data=f"r/任务首页?sort=u"),
            InlineKeyboardButton(f"{'▶' if taskSort=='n' else ''} 🗣️ 昵称", callback_data=f"r/任务首页?sort=n"),
            InlineKeyboardButton(f"{'▶' if taskSort == 'no' else ''} ♾️ 无",callback_data=f"r/任务首页?sort=no")])
        # keyboard.append([InlineKeyboardButton(f"🔎 查询", callback_data="r/任务输入?text=请输入任务标题:")])
        keyboard.append([InlineKeyboardButton("🏪 发布任务", callback_data="r/判断角色?type=publish"),
                         InlineKeyboardButton("👤 用户中心", callback_data="r/任务用户中心")])
        await self.sendMsg(text=text, keyboard=keyboard,var=True)
    async def task_info(self, **kwargs):
        task_id = kwargs.get("task")[0]
        taskD = TaskDate()
        task_info = await taskD.get_task(id=task_id)
        log_count = await taskD.get_task_info_log_count(task_id=task_info[0])
        groupObj = await taskD.get_user_group(id=task_info[7])
        try:
            text = f"⛩️用户-任务申请⛩️\n\n"\
                   f"任务ID: {task_info[0]}\n" \
                   f"标题: {task_info[1] if task_info[1] else '未设置'}\n" \
                   f"单价: {task_info[2]}U\n" \
                   f"数量: {log_count[0]}/{'无限' if task_info[4] == 0 else task_info[4]}\n" \
                   f"总价: {'无限' if task_info[4] == 0 else task_info[2] * task_info[4]}\n" \
                   f"绑定群/频: {f'[{groupObj[3] }]({groupObj[6]})' if groupObj else '未绑定'} \n" \
                   f"任务状态: {'🔴 已下线' if task_info[5] == 2 else '🟢 已上线'}\n\n" \
                   f"**任务条件规则:**\n" \
                     f"{'🔸必须有用户名' if task_info[9] == 1 else ''}" \
                     f"{'🔸昵称中文,' if task_info[10] == 1 else ''}" \
                     f"\n条件规则说明:\n被邀请用户必须满足设置规则才算有效.\n\n" \
                   f"结算说明:\n领取过后获得推广链接，会记金额到您的任务账户,通过审核后结算到你的账户即可提现，后台定时检测重复邀请，账号注销，账号退群等违规\n\n" \
                   f"警告:\n非真实性账号，刷量将导致您的账号被封禁余额等不可提现,任务金额不可结算"
            keyboard = []
            keyboard.append([InlineKeyboardButton("👉 领取任务",callback_data=f"r/任务领取?task={task_info[0]}")])
            var=await Var(Id=(await self.retChat()).chat.id).read()
            keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data=f"{var if 'r/任务首页' in var else 'r/任务首页'}")])
            await self.sendMsg(text=text, keyboard=keyboard)
        except RPCError as e:
            logs.info(" ".join(str(value) for value in (e,)))
    async def task_receive(self,**kwargs):
        user = self.data.get("user")
        task_id = kwargs.get('task')[0]
        taskD = TaskDate()
        try:
            recTask =await taskD.get_task_receive_isNo(user=user[0],task=task_id)
            if not recTask:
                task_data =await taskD.get_task(id=task_id)
                if not task_data:
                   return await self.query.answer(text="任务不存在请选择其他任务")
                task_group = await taskD.get_user_group(id=task_data[7])
                if not task_group:
                    return await self.query.answer(text="推广群不存在请选择其他任务")
                if task_data[18]==1:
                    link =await self.client.create_chat_invite_link(chat_id=task_group[1],creates_join_request=True)
                else:
                    link =await self.client.create_chat_invite_link(chat_id=task_group[1])
                taskC =await taskD.post_task_receive(task=task_data[0],user=user[0],url=link.invite_link)
                if taskC:
                    await self.receive_task_info(myTask=[taskC[0]])
            else:
                await self.query.answer(text="⚠️ 您已经领取过该任务请前往我的任务查看..",show_alert=True)
                await self.receive_task_info(myTask=[recTask[0]])
        except (RPCError) as e:
            await self.query.answer(text="生成邀请链接错误请选择其他任务", show_alert=True)
            TO = TaskOperation(Client=self.client, Task=task_id)
            await TO.offline(Text=f"⚠️ 任务:{task_data[1]},频道:{task_group[3]} \n机器人权限不足已自动下线任务。。")
            await self.index()
    async def receive_task_info(self, **kwargs):
        task_id = kwargs.get("myTask")[0]
        taskD = TaskDate()
        myTask = await MyTaskDate().get_my_receive_task(id=task_id)
        maTask = await taskD.get_task(id=myTask[1])
        log_count = await taskD.get_task_info_log_count(task_id=maTask[0])
        maGroup = await taskD.get_user_group(id=maTask[7])
        try:
            text = f"👤用户-我的任务详情\n\n" \
                   f"任务ID: {maTask[0]}\n" \
                   f"标题: {maTask[1] if maTask[1] else '未设置'}\n" \
                   f"单价: {maTask[2]}U\n" \
                   f"数量: {log_count[0]}/{'无限' if maTask[4] == 0 else maTask[4]}\n" \
                   f"绑定群/频: {f'[{maGroup[3]}]({maGroup[6]})' if maGroup else '未绑定'} \n" \
                   f"任务状态: {'🔴 已下线' if maTask[5] == 2 else '🟢 已上线'}\n" \
                   f"领取ID: {myTask[0]}\n" \
                   f"领取状态: {'💚 正常' if maTask[5] == 1 and myTask[4] == 0 else '💔 已取消'}\n\n" \
                   f"**任务条件规则:**\n" \
                   f"{'🔸必须有用户名' if maTask[9] == 1 else ''}" \
                   f"{'🔸昵称中文,' if maTask[10] == 1 else ''}" \
                   f"\n条件规则说明:\n被邀请用户必须满足设置规则才算有效,后台检测重复邀请，账号注销，账号退群等违规\n\n" \
                   f"结算说明：任务日志总数大于10 会在0点02分生成前一天的结算订单,发布方审核后结算到可提现账户.\n\n" \
                   f"前往我的任务 点击 《发送群/频设置》 按钮,机器人会自动发送你接收的任务彻底解放双手" \
                   # f"推广链接：👇点url复制\n" \
                   # f"`{myTask[5]}`"
            keyboard = []
            var = await Var(Id=(await self.retChat()).chat.id).read()
            keyboard.append([InlineKeyboardButton("👉 前往我的任务", callback_data=f"r/任务我的任务")])
            keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data=f"{var if 'r/任务首页' in var else 'r/任务首页'}")])
            await self.sendMsg(text=text, keyboard=keyboard)
        except RPCError as e:
            logs.info(" ".join(str(value) for value in (e,)))
