import datetime
from pyrogram.errors import RPCError
from core.bot import app
from core.config import bot_config
from core.scheduler import scheduler
from handlers.setup import register_admin_handlers, register_client_handlers
from public.logger import LoggerConfig
from public.security import redact_config
from public.web import start_server
from services.configuration import get_config
from services.network import addressNetwork
from services.settlement import SettlementTime
from services.task_broadcast import TaskSendMsg


logs = LoggerConfig('main', 'logs/main.log').get_logger()


def main():
    try:
        logs.critical('启动成功')
        runtime_config = get_config()
        if not runtime_config.get("callback_address"):
            public_ip = addressNetwork()
            if public_ip:
                runtime_config["callback_address"] = f"http://{public_ip}:8888/okPay"

        logs.critical(f"读取配置文件:{redact_config(runtime_config)}")

        scheduler.start()
        schedulerObj = scheduler.add_job(SettlementTime, trigger='cron', hour=0, minute=5, misfire_grace_time=60)
        logs.critical(f"定时结算执行时间:{schedulerObj}")
        taskSendTime = scheduler.add_job(TaskSendMsg, "interval", kwargs={'client': app}, seconds=60 * 60)
        logs.critical(f"定时任务发送执行时间:{taskSendTime}")

        register_client_handlers(app)
        register_admin_handlers(app)
        scheduler.add_job(start_server, trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=1))
        app.run()
    except RPCError as e:
        logs.error(f"pyrogram启动错误:{e}")
    except Exception as e:
        logs.error(f"启动错误{e}")


if __name__ == '__main__':
    main()
