import os

from core.config import bot_config, refresh_secret_config_from_env
from data.data import ConfigData
from public.logger import LoggerConfig


config_logs = LoggerConfig("config", "logs/config.log").get_logger()


def get_config():
    try:
        config_data = ConfigData()
        config_list = config_data.get_config_list()
        secret_keys = {"OkPay_id", "OkPay_token"}
        allow_db_secret_config = os.getenv("ALLOW_DB_SECRET_CONFIG", "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

        if config_list:
            bot_config["rejectText"] = []
            for config in config_list:
                key = config[1]
                value = config[2]
                if key == "rejectText":
                    bot_config["rejectText"].append(value)
                elif key in secret_keys and not allow_db_secret_config:
                    continue
                else:
                    bot_config[key] = value

        refresh_secret_config_from_env()
        return bot_config
    except Exception as err:
        config_logs.error(f"读取配置错误{err}")
        return bot_config
