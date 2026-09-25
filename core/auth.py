import json

from pyrogram.types import Message

from core.config import bot_config
from core.redis_client import redis_client
from data.data import ChatUser
from public.logger import LoggerConfig


auth_logs = LoggerConfig("auth", "logs/auth.log").get_logger()


class RestrictAccess:
    def __init__(self, Msg: Message = None):
        self.msg = Msg

    async def limit_check(self):
        msg = self.msg
        try:
            key = f"restrict{msg.chat.id}"
            count = redis_client.get(key)
            if count is None or int(count) < int(bot_config["restrict_limit"]):
                redis_client.incr(key)
                if count is None:
                    redis_client.expire(key, 60)
                return True

            if int(count) == int(bot_config["restrict_limit"]):
                redis_client.incr(key)
                redis_client.expire(key, 60 * int(bot_config["restrict_time"]))
                await msg.reply_text(f"访问频率过高限制访问-{bot_config['restrict_time']}分钟")
            return False
        except Exception as err:
            auth_logs.error(f"访问限制错误：{err}")
            return False


class UserAuth:
    def __init__(self, Msg: Message = None):
        self.msg = Msg

    async def auth(self, FromUser=None):
        msg = self.msg
        try:
            key = f"user{FromUser.id}"
            user = redis_client.get(key)
            if user:
                user = json.loads(user)
            else:
                user = await ChatUser(Msg=msg).get_or_create(FromUser)
                redis_client.set(key, json.dumps(user, default=str), ex=600)

            if user[4] == 1:
                return False
            return user
        except Exception as err:
            auth_logs.error(f"账号访问错误{err}")
            await msg.reply_text("账号访问错误")
            return False

    async def resUser(self, id, chat_id):
        try:
            key = f"user{chat_id}"
            user = await ChatUser().get(id=id)
            redis_client.set(key, json.dumps(user, default=str), ex=600)
            return user
        except Exception as err:
            auth_logs.error(f"重新设置账号缓存错误{err}")
            return False
