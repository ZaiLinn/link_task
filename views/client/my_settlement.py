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


class MySettlement(BaseView):
    async def inputBot(self, **kwargs):
        msg = await self.retChat()
        txt = f"🧧{kwargs.get('text')[0]}"
        await msg.reply_text(text=txt, reply_to_message_id=msg.id, reply_markup=ForceReply())
    async def index(self,**kwargs):
            user = self.data.get("user")
            OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 10
            taskState = kwargs.get('state')[0] if kwargs.get('state') else 0
            closeData = MySettlementDate()
            task = await closeData.get_settlement_list(OFFSET=OFFSET, LIMIT=LIMIT, user=user[0],state=taskState)
            task_count = await closeData.get_settlement_count(user=user[0])
            keyboard = []
            text = f"用户-结算管理\n\n" \
                   f"已结算总数：{task_count[2]}-" \
                   f"已结算总金额：{task_count[3]}\n" \
                   f"已拒绝总数：{task_count[0]}-" \
                   f"已拒绝总金额：{task_count[1]}\n\n" \
                   f"待结算总数：{task_count[4]}\n" \
                   f"待结算总金额：{task_count[5]}\n\n" \
                   f"说明:任务标题-待结算佣金，\n如被恶意拒绝结算可在任务详情进行申诉\n" \
                   f"点击下方结算按钮查看详细"
            if task and task_count:
                settlement_types = {0: task_count[4], 1: task_count[2], 5: task_count[6], 6: task_count[0]}
                totalPages, currentPage = math.ceil(settlement_types.get(int(taskState)) / LIMIT), math.ceil(OFFSET / LIMIT) + 1
                upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
                for key in task:
                    keyboard.append([InlineKeyboardButton(f"{key[1]}-{key[2]} ",
                                                          callback_data=f"r/任务结算详情?set={key[0]}&up={taskState}")])
                keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                      callback_data=f"r/任务结算管理?page={upPage}&state={taskState}" if upPage >= 0 else '-'),
                                 InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                                 InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                      callback_data=f"r/任务结算管理?page={dowPage}&state={taskState}" if currentPage != totalPages else '-')])
            else:
                keyboard.append([InlineKeyboardButton(f"空/还没有结算数据", callback_data="-")])
            keyboard.append([InlineKeyboardButton(f"{'🌕' if int(taskState) == 0 else ''} 待结",callback_data=f"r/任务结算管理?state=0"),
                             InlineKeyboardButton(f"{'🌕' if int(taskState) == 1 else ''} 已结",callback_data=f"r/任务结算管理?state=1"),
                             InlineKeyboardButton(f"{'🌕' if int(taskState) == 5 else ''} 申诉",callback_data=f"r/任务结算管理?state=5"),
                             InlineKeyboardButton(f"{'🌕' if int(taskState) == 6 else ''} 拒绝",callback_data=f"r/任务结算管理?state=6")])
            keyboard.append([InlineKeyboardButton(f"↩️ 返回", callback_data="r/任务用户中心")])
            await self.sendMsg(text=text, keyboard=keyboard,var=True)
    async def settlementInfo(self,**kwargs):
        settlement,upState=kwargs.get('set')[0],kwargs.get('up')[0]
        OFFSET, LIMIT = int(kwargs.get('page')[0]) if kwargs.get('page') else 0, 5
        taskState = kwargs.get('state')[0] if kwargs.get('state') else 0
        taskData = MySettlementDate()
        task_log = await taskData.get_settlement_log_list(OFFSET=OFFSET, LIMIT=LIMIT,settlement= settlement, state=taskState)
        task_count = await taskData.get_settlement_info(settlement=settlement)
        keyboard = []
        settlement_types = {0: '待审核',1: '已审核',5: '待申诉',6: '已拒绝'}
        text = f"\n**用户-结算详情**\n\n" \
               f"结算ID：{task_count[0]}｜" \
               f"时间：{task_count[7].strftime('%Y-%m-%d')}\n" \
               f"资金流水：{task_count[3] or '无'}\n" \
               f"结算状态：{'申诉中' if task_count[8] == 1 else settlement_types.get(task_count[5], '')}\n" \
               f"结算备注：{task_count[6] or '无'}\n" \
               f"结算任务：{task_count[9]}｜" \
               f"单价：{task_count[11]}\n" \
               f"群组：[{task_count[12]}]({task_count[13]})\n" \
               f"推手ID：{task_count[14]}｜" \
               f"昵称：{task_count[15]}\n" \
               f"结算数量：{task_count[16]}｜" \
               f"金额：{task_count[17]}\n" \
               f"不结算数量：{task_count[18]}｜" \
               f"金额：{task_count[19]}\n"
        text+="\n**邀请列表**\n"
        if task_log:
            totalPages, currentPage = math.ceil((task_count[16] if int(taskState)==0 else task_count[18]) / LIMIT), math.ceil(OFFSET / LIMIT) + 1
            upPage, dowPage = OFFSET - LIMIT, OFFSET + LIMIT
            for key in task_log:
                text += f"[邀请时间:{key[3].strftime('%y.%m.%d %H:%M:%S')} ｜ 佣金:{key[1]}](https://t.me/)\n" \
                        f"账号:`{key[6] if len(key[6]) > 1 else '未设置'}` ｜ 昵称:`{key[4]}{key[5]}` \n" \
                        f"状态:{key[7]}\n"
            keyboard.append([InlineKeyboardButton(f"{'⬅️上一页' if upPage >= 0 else '-'}",
                                                  callback_data=f"r/任务结算详情?page={upPage}&state={taskState}&set={settlement}&up={upState}" if upPage >= 0 else '-'),
                             InlineKeyboardButton(f"{currentPage}/{totalPages}页", callback_data="-"),
                             InlineKeyboardButton(f"️{'➡️下一页' if currentPage != totalPages else '-'}",
                                                  callback_data=f"r/任务结算详情?page={dowPage}&state={taskState}&set={settlement}&up={upState}" if currentPage != totalPages else '-')])
        else:
            text+="\n列表为空,未发现邀请"
        keyboard.append([InlineKeyboardButton(f"{'🌕' if int(taskState) == 0 else '🌑'} 未结算",callback_data=f"r/任务结算详情?state=0&set={settlement}&up={upState}"),
                         InlineKeyboardButton(f"{'🌕' if int(taskState) == 1 else '🌑'} 不结算",callback_data=f"r/任务结算详情?state=1&set={settlement}&up={upState}")
                         ])
        if task_count[5] ==5 and task_count[8]==0:
            keyboard.append([InlineKeyboardButton(f"✅ 申诉", callback_data=f"r/任务结算申诉?set={settlement}&up={upState}")])
        var = await Var(Id=(await self.retChat()).chat.id).read()
        keyboard.append([InlineKeyboardButton("↩️ 返回",callback_data=f"{var if 'r/任务结算管理' in var else 'r/任务结算管理'}")])
        await self.sendMsg(text=text, keyboard=keyboard)
    async def appeal(self,**kwargs):
        settlement,upState=kwargs.get('set')[0],kwargs.get('up')[0]
        mySet=MySettlementDate()
        settData =await mySet.get_settlement_one(sett=settlement)
        if settData and settData[5]==5 and  settData[8]==0:
            await mySet.put_settlement_appeal(sett=settlement)
            await self.query.answer(text='提交申诉成功,请等待客服处理。。',show_alert=True)
            await self.settlementInfo(set=[settlement],up=[upState])
        else:
            await self.query.answer(text='已提交,请勿重复提交。。',show_alert=True)
