import redis
from core.config import redis_config

redis_client = redis.Redis(
    host=redis_config['host'],
    port=redis_config['port'],
    db=redis_config['db'],
    password=redis_config['password'],
)
