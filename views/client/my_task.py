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


class MyTask(BaseView):
    async def inputBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"🧧{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())
    async def index(self,**kwargs):
        user= self.data.get('user')
        times = datetime.datetime.now().strftime('%Y-%m-%d')
        balance_count = await MyTaskDate().get_my_index_count(user=user[0],times=times)
        text = f"👤️用户-中心\n\n" \
               f"用户ID:{user[1]}\n" \
               f"用户名:{user[2]}" \
               f"名字:{user[3]}\n" \
               f"状态:{'正常' if user[4]==0 else '禁用'}\n" \
               f"可提现余额:{balance_count[0]}U\n" \
               f"待结算金额:{balance_count[1]}U\n" \
               f"未结算收益:{balance_count[2]}U\n" \
               f"创建时间:{user[9]}"
        keyboard=[]
        keyboard.append([InlineKeyboardButton("🧾 我的任务", callback_data=f"r/任务我的任务"),
                         InlineKeyboardButton("🔖 任务结算", callback_data=f"r/任务结算管理")])
        keyboard.append([InlineKeyboardButton("💸 提现中心", callback_data=f"r/任务提现"),
                         InlineKeyboardButton("💰 资金钱包", callback_data=f"r/任务资金钱包")])
        keyboard.append([InlineKeyboardButton("🏛️ 任务大厅", callback_data=f"r/任务首页")])
        keyboard.append([InlineKeyboardButton("💁客服群组", url=f"https://t.me/{bot_config['msgGroup'].replace('@', '')}"),
                         InlineKeyboardButton("❔教程频道", url=f"https://t.me/{bot_config['publicGroup'].replace('@', '')}")])
        await self.sendMsg(text=text,keyboard=keyboard)
    async def my_task(self,**kwargs):
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
        taskState = int(kwargs.get('state')[0]) if kwargs.get('state') else 0
        user = self.data.get('user')
        taskData = MyTaskDate()
        task = await taskData.get_my_receive_task_list(OFFSET=OFFSET, LIMIT=LIMIT,user_id=user[0], state=taskState)
        task_count = await taskData.get_my_receive_task_count(user=user[0])
        keyboard = []
        text = f"👤用户-我的任务️\n\n"\
               f"任务总数:{task_count[0] + task_count[1]}\n" \
                f"进行中的任务:{task_count[0]}\n" \
                f"已取消的任务:{task_count[2]}\n" \
                f"已下线的任务:{task_count[1]}\n" \
               f"成功邀请总数:{task_count[3]}\n" \
               f"点击下方任务按钮领取任务链接"
        if task:
            total={0:task_count[0],1:task_count[2],2:task_count[1]}
            totalPages, currentPage = math.ceil(total.get(taskState) / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in task:
                keyboard.append([InlineKeyboardButton(f"🧧{key[2]}-通过:{key[3]}｜{key[1]}",
                                                      callback_data=f"r/任务我的任务信息?rec={key[0]}")])
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"r/任务我的任务?page={upPage}&state={taskState}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"r/任务我的任务?page={dowPage}&state={taskState}" if currentPage != totalPages else '-')])
        else:
            keyboard.append([InlineKeyboardButton(f"空/未发现", callback_data="-")])
        keyboard.append([InlineKeyboardButton(f"{'🌕' if taskState == 0 else ''} 进行中",callback_data=f"r/任务我的任务?state=0"),
                         InlineKeyboardButton(f"{'🌕' if taskState == 1 else ''} 已取消",callback_data=f"r/任务我的任务?state=1"),
                         InlineKeyboardButton(f"{'🌕' if taskState == 2 else ''} 已下线",callback_data=f"r/任务我的任务?state=2")])
        keyboard.append([InlineKeyboardButton("🔗 发送群/频设置", callback_data="r/发送群设置")])
        keyboard.append([InlineKeyboardButton("🔗 生成推广", callback_data=f"r/任务生成推广消息")])
        keyboard.append([InlineKeyboardButton("↩️ 返回", callback_data="r/任务用户中心")])
        await self.sendMsg(text=text, keyboard=keyboard,var=True)
    async def my_task_info(self, **kwargs):
        rec_id = kwargs.get("rec")[0]
        taskD = TaskDate()
        myTask = await MyTaskDate().get_my_receive_task(id=rec_id)
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
                   f"结算说明：任务日志总数大于10 会在0点02分生成前一天的结算订单,发布方审核后结算到可提现账户.\n" \
                   f"我的任务点击 《发送群/频设置》 按钮,机器人会自动发送你接收的任务彻底解放双手" \
                   # f"推广链接：👇点url复制\n" \
                   # f"`{myTask[5]}`"
            keyboard = []
            keyboard.append([InlineKeyboardButton("🧾 任务日志",callback_data=f"r/任务我的任务日志?rec={rec_id}")])
            if  maTask[5] == 1:
                keyboard.append([InlineKeyboardButton(f"{'💔 取消任务' if myTask[4]==0 else '💚 恢复任务'}",callback_data=f"r/任务取消任务?rec={rec_id}&state={myTask[4]}")])
            var = await Var(Id=(await self.retChat()).chat.id).read()
            keyboard.append([InlineKeyboardButton("↩️ 返回",callback_data=f"{var if 'r/任务我的任务' in var else 'r/任务我的任务'}")])
            await self.sendMsg(text=text, keyboard=keyboard)
        except RPCError as e:
            logs.info(" ".join(str(value) for value in (e,)))
    async def my_task_cancel(self,**kwargs):
        rec, state = kwargs.get("rec"), kwargs.get("state")
        myTask = await MyTaskDate().put_my_receive_sate(id=rec[0],state=(1 if int(state[0])==0 else 0))
        if myTask:
            await self.query.answer(text=f"{'取消任务' if int(state[0])==0 else '恢复任务'}成功",show_alert=True)
            await  self.my_task_info(rec=rec)
        else:
            await self.query.answer(text=f"{'取消任务' if int(state[0])==0 else '恢复任务'}失败",show_alert=True)
    async def my_task_log(self,**kwargs):
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
        taskState = kwargs.get('state')[0] if kwargs.get('state') else 0
        taskData = MyTaskDate()
        task_log = await taskData.get_my_tsk_log_list(OFFSET=OFFSET, LIMIT=LIMIT, rec=kwargs.get('rec')[0], state=taskState)
        task_count = await taskData.get_my_tsk_log_list_count(rec=kwargs.get('rec')[0], state=taskState)
        keyboard = []
        text = f"👤用户-任务日志\n\n" \
               f"日志总数:{task_count[0]}\n"
        if int(taskState) ==0:
            text += f"当前数量:{task_count[1] or 0}\n" \
                    f"当前佣金:{task_count[2] or 0}U\n"
        elif int(taskState) ==1:
            text += f"不结算数量:{task_count[1] or 0}\n" \
                    f"不结算佣金:{task_count[2] or 0}U\n"
        text += f"邀请列表\n\n"
        if task_log and task_count:
            totalPages, currentPage = math.ceil(task_count[1] / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in task_log:
                text += f"[邀请时间:{key[3]}-佣金:{key[1]}](https://t.me/)\n" \
                        f"账号:`{key[6] if len(key[6]) > 1 else '未设置'}`-昵称:`{key[4]}{key[5]}`\n" \
                        f"状态:{key[7]}\n"
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"r/任务我的任务日志?page={upPage}&state={taskState}&rec={kwargs.get('rec')[0]}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"r/任务我的任务日志?page={dowPage}&state={taskState}&rec={kwargs.get('rec')[0]}" if currentPage != totalPages else '-')])
        else:
            text+="空/未发现数据\n"
        keyboard.append([InlineKeyboardButton(f"{'🌕' if int(taskState) == 0 else '🌑'} 已通过",
                                              callback_data=f"r/任务我的任务日志?state=0&rec={kwargs.get('rec')[0]}"),
                         InlineKeyboardButton(f"{'🌕' if int(taskState) == 1 else '🌑'} 未通过",
                                              callback_data=f"r/任务我的任务日志?state=1&rec={kwargs.get('rec')[0]}")
                         ])

        keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data=f"r/任务我的任务信息?rec={kwargs.get('rec')[0]}")])
        await self.sendMsg(text=text, keyboard=keyboard)
    async def my_Assemble_message(self,**kwargs):
        user = self.data.get('user')
        myTask = MyTaskDate()
        myList =await myTask.get_my_receive_success_list(user=user[0])
        text = "频道甄选\n\n"
        if myList:
            for my in myList:
                text+=f"👉 [{await truncate_string(string=my[0],length=15)}]({my[1]})\n"
        else:
            text += f"推广频道为空/请去接任务"
        keyboard=[[InlineKeyboardButton(f"❌ 删除", callback_data=f"r/删除当前消息")]]
        await self.sendMsg(text=text,keyboard=keyboard,type=True)
    async def sendGroupSet(self,**kwargs):
        user = self.data.get('user')
        myTask = MyTaskDate()
        if user:
            my_group = await myTask.get_send_group_list(user_id=user[0])
            text = "**选择频道**\n\n" \
                   "邀请机器人进频道机器人会自动发任务消息\n\n" \
                   "群状态：🟢正常🟡无权限⚫已退群🔴封禁\n" \
                   "请确认是否已经将机器人拉入并设置管理员\n" \
                   "点下邀请进频道或群按钮,出现权限检测正常后点击刷新\n\n" \
                   "发送状态:✅ 启用发送 ❌ 取消发送\n" \
                   "👇点击频道名字可取消与启用发送"
            keyboard = []
            if my_group:
                row = []
                g_type={0:"🟢",1:"🟡",2:"⚫",10:"🔴"}
                send_t={0:"✅",1:"❌"}
                for group in my_group:
                    row.append(InlineKeyboardButton(f"{g_type[group[9]]}-{group[3]}-{send_t[group[7]]}",callback_data=f"r/发送群状态?gid={group[0]}&st={group[7]}"))
                    if len(row) >= 2:
                        keyboard.append(row)
                        row = []
                keyboard.append(row)
            else:
                keyboard.append([InlineKeyboardButton("⚠️未找到到群/频道,请邀请机器人入群", callback_data=f"-")])
            keyboard.append([InlineKeyboardButton("🌸邀请进群组",
                                                  url=f"https://t.me/{bot_config['botUserName'].replace('@', '')}?startgroup=true"),
                             InlineKeyboardButton("🏵️邀请进频道",
                                                  url=f"https://t.me/{bot_config['botUserName'].replace('@', '')}?startchannel=true")])
            keyboard.append([InlineKeyboardButton("🔄 刷新", callback_data=f"r/发送群设置"),
                             InlineKeyboardButton("↩️ 返回", callback_data=f"r/任务我的任务")])
            await self.sendMsg(text=text, keyboard=keyboard)
    async def sendGroupstate(self,**kwargs):
        try:
            id = kwargs.get("gid")
            state = kwargs.get("st")
            myTask = MyTaskDate()
            if state := '1' if state[0]=='0' else '0':
                await myTask.put_send_group_state(id=id[0], state=state)
                await self.sendGroupSet()
                await self.query.answer(text=f"{'取消成功' if state==0 else '启用成功'}")
        except (RPCError,Exception) as e:
            await self.query.answer(text=f"修改错误：{e}",show_alert=True)
