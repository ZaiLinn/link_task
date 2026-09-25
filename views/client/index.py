import logging
from config import CallbackQuery, Client, InlineKeyboardButton, InlineKeyboardMarkup, Message, RPCError, bot_config
from core.auth import UserAuth
from repositories.client.index import IndexDate
from views.client.publish_index import PublishIndex
from views.client.task_index import TaskIndex

logs = logging.getLogger(__name__)
class Index:
    def __init__(self, Client:Client, Query:CallbackQuery=None, Msg:Message=None, Data=None):
        self.client =Client
        self.query = Query
        self.msg = Msg
        self.data= Data
    async def retChat(self):
        if self.query:
            return self.query.message
        else:
            return self.msg
    async def sendMsg(self,**kwargs):
        msg = await self.retChat()
        try:
            if self.query:
                await self.client.edit_message_text(chat_id=msg.chat.id, message_id=msg.id, text=kwargs['text'],
                                                    reply_markup=InlineKeyboardMarkup(kwargs['keyboard']),
                                                    disable_web_page_preview=True)
            else:
                if len(bot_config.get('video'))>24:
                    await self.client.send_video(chat_id=msg.chat.id, video=bot_config.get('video'), caption=kwargs['text'],
                                                 reply_markup=InlineKeyboardMarkup(kwargs['keyboard']))
                else:
                    await msg.reply_text(text=kwargs['text'], reply_markup=InlineKeyboardMarkup(kwargs['keyboard']),
                                         disable_web_page_preview=True)
        except RPCError as e:
            logs.info(" ".join(str(value) for value in (e,)))
    async def index(self,**kwargs):
        msg = await self.retChat()
        user=self.data.get('user')
        # setComm=[BotCommand("start", "开始"),BotCommand("role", "切换角色"),BotCommand("task", "任务大厅"), BotCommand("mc", "商家中心"),BotCommand("help", "帮助")]
        # comm= await self.client.get_bot_commands()
        # if len(comm) != len(setComm):
        #     await self.client.set_bot_commands(setComm)
        keyboard = []
        keyboard.append([InlineKeyboardButton("💵我是推广用户💵",callback_data="r/判断角色?type=task")])
        keyboard.append([InlineKeyboardButton("🏪我是推广商家🏪",callback_data="r/判断角色?type=publish")])
        keyboard.append([InlineKeyboardButton("💁客服群组💁",url=f"https://t.me/{bot_config['msgGroup'].replace('@', '')}")])
        keyboard.append([InlineKeyboardButton("❔使用教程", url=f"https://t.me/{bot_config['publicGroup'].replace('@', '')}")])
        if user[5] in [1, 2]:
            keyboard.append([InlineKeyboardButton("👮‍♂️管理后台👮‍♂️", callback_data="a/管理首页")])
        text = f"**欢迎使用:{bot_config.get('botName')}**\n\n" \
               f"{bot_config.get('indexTxt')}\n\n" \
               f"⛩️请选择你的用户类型⛩️\n\n" \
               f"💰 推广用户:领取推广任务,赚取佣金\n" \
               f"💸 推广商家:发布任务,推广您的链接\n\n" \
               f"🏗️技术支持:[蛇皮工作室](https://t.me/sepigzs)"
        await self.sendMsg(text=text, keyboard=keyboard)
    async def ifRole(self,**kwargs):
        user = self.data.get('user')
        try:
            indexD = IndexDate()
            role_type = kwargs.get("type")
            if role_type:
                await indexD.set_role(id=user[0], role=role_type[0])
                user =await UserAuth().resUser(id=user[0],chat_id=user[1])
            if user[6]!='publish':
                await TaskIndex(Client=self.client,Msg=self.msg, Query=self.query, Data={'user': user}).index()
            else:
                await PublishIndex(Client=self.client,Msg=self.msg,  Query=self.query, Data={'user': user}).index()
        except (RPCError,Exception) as E:
            logs.info(" ".join(str(value) for value in (E,)))
    async def backReview(self,**kwargs):
        # 删除当前消息
        msg =await self.retChat()
        await self.client.delete_messages(msg.chat.id, message_ids=msg.id)
