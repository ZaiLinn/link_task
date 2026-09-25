import json

from core.redis_client import redis_client
from public.logger import LoggerConfig


cache_logs = LoggerConfig("cache", "logs/cache.log").get_logger()


class Var:
    def __init__(self, Id=None):
        self.id = Id

    async def write(self, value=None):
        if value is None:
            return False
        try:
            redis_client.set(self._key(), json.dumps(value, default=str), ex=60 * 60 * 24)
            return True
        except Exception as err:
            cache_logs.error(f"写入临时变量失败:{err}")
            return False

    async def read(self, default="无"):
        try:
            value = redis_client.get(self._key())
            if value:
                return json.loads(value)
            return default
        except Exception as err:
            cache_logs.error(f"读取临时变量失败:{err}")
            return default

    def _key(self):
        return f"var{self.id}"
