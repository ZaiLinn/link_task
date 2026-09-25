import asyncio
import decimal
import datetime
import uuid

from pyrogram.errors import RPCError

from core.bot import app
from public.logger import LoggerConfig
from repositories.task_data import AutomaticDettlementTimeDate, SettlementTimeDate
from services.telegram_utils import isPrivileges


settlement_logs = LoggerConfig("settlement", "logs/settlement.log").get_logger()

# Max concurrent settlements processed in parallel. Keeps DB and Telegram load bounded.
_SETTLEMENT_CONCURRENCY = 5
# Max concurrent Telegram get_chat_member calls per settlement (Telegram rate limit guard).
_MEMBER_CHECK_CONCURRENCY = 10


async def SettlementTime():
    try:
        current_time = datetime.datetime.now() - datetime.timedelta(days=1)
        one_day = current_time.strftime("%Y-%m-%d")
        settlement_logs.critical(f"{one_day}-结算定时器")
        sett_date = SettlementTimeDate()
        sett_list = await sett_date.get_settlenment_list(time=one_day)
        if sett_list:
            sem = asyncio.Semaphore(_SETTLEMENT_CONCURRENCY)

            async def _process_one(sett):
                async with sem:
                    cel_sett = await sett_date.get_settlenment_info(r_id=sett[0], m_id=sett[4], time_d=one_day)
                    if cel_sett:
                        if await sett_date.put_settlenment_info(s_id=cel_sett[0], r_id=sett[0], time_d=one_day):
                            settlement_logs.critical(f"时间：{one_day}任务人：{sett[0]},提交结算成功")

            await asyncio.gather(*[_process_one(sett) for sett in sett_list])
        else:
            settlement_logs.critical(f"时间：{one_day}，没有需要提交的结算")
        settlement_logs.critical(f"{one_day}-生成结算完成")
        await AutomaticDettlementTime()
    except Exception as err:
        settlement_logs.error(f"结算定时器错误{err}")


async def StatisticalSuccessRate(task):
    sett_date = AutomaticDettlementTimeDate()
    sett_list = await sett_date.get_settlement_log_rate(id=task[0])
    # Thresholds: tasks with keyword (7) and/or username (8) requirements have higher
    # expected churn, so the fraud-rate ceiling is raised before flagging as cheat.
    rate = 100
    if task[7] == 1 and task[8] == 1:
        rate -= 70
    elif task[7] == 1:
        rate -= 60
    elif task[8] == 1:
        rate -= 60
    else:
        rate -= 8

    if sett_list[1] <= decimal.Decimal(rate / 100):
        settlement_logs.critical(f"正常结算:{rate / 100}<={sett_list}")
        return True
    settlement_logs.critical(f"疑似作弊:{rate / 100}-{sett_list}")
    return False


async def CheckBillingInvited(sett):
    try:
        sett_date = AutomaticDettlementTimeDate()
        log_list = await sett_date.get_log_list(settlement=sett[0])
        if log_list and sett[10] and sett[12]:
            is_privi = await isPrivileges(chatId=sett[10], typeG=sett[12])
            if is_privi == 0:
                sem = asyncio.Semaphore(_MEMBER_CHECK_CONCURRENCY)

                async def _check_member(log_row):
                    async with sem:
                        try:
                            await app.get_chat_member(chat_id=sett[10], user_id=log_row[2])
                        except RPCError:
                            await sett_date.put_task_log_info(id=log_row[0], state=1, label="未通过:用户已注销")
                        except Exception as err:
                            settlement_logs.critical(f"用户检测错误{err}")

                await asyncio.gather(*[_check_member(row) for row in log_list])
            else:
                settlement_logs.critical(f"机器人不在群[{sett[11]}]或权限不足")
        return await sett_date.get_price(settlement_id=sett[0])
    except Exception as err:
        settlement_logs.error(f"自动结算检测用户退群注销错误:{err}")
        return None


async def _process_settlement(sett, sett_date, one_day):
    settlement_logs.critical(sett)
    price = await CheckBillingInvited(sett=sett)
    if not price or price <= decimal.Decimal(0):
        put_settlement = await sett_date.put_settlement_info(settlement=sett[0], state=5, label="结算金额为零")
        settlement_logs.critical(f"时间：{one_day}之前-id:{sett}\n结算金额为零{put_settlement}")
        return

    if not await StatisticalSuccessRate(task=sett):
        put_settlement = await sett_date.put_settlement_info(
            settlement=sett[0], state=5, label="拒绝结算疑似作弊",
        )
        settlement_logs.critical(f"时间：{one_day}之前-:{sett}\n拒绝结算疑似作弊:{put_settlement}")
        return

    order_id_m = uuid.uuid4().hex
    order_id_u = uuid.uuid4().hex
    ok = await sett_date.atomic_settle(
        settlement_id=sett[0],
        merchant_id=sett[3],
        user_id=sett[4],
        order_id_m=order_id_m,
        order_id_u=order_id_u,
        price=price,
    )
    settlement_logs.critical(
        f"时间：{one_day}之前-:{sett}\n原子结算结果:{ok}，超时的自动结算{'成功' if ok else '失败'},"
    )


async def AutomaticDettlementTime():
    try:
        current_time = datetime.datetime.now() - datetime.timedelta(days=1)
        one_day = current_time.strftime("%Y-%m-%d")
        settlement_logs.critical(f"{one_day}之前的结算-超时结算定时器开始")
        sett_date = AutomaticDettlementTimeDate()
        sett_list = await sett_date.get_settlenment_list(time=one_day)
        if sett_list:
            sem = asyncio.Semaphore(_SETTLEMENT_CONCURRENCY)

            async def _run(sett):
                async with sem:
                    await _process_settlement(sett, sett_date, one_day)

            await asyncio.gather(*[_run(sett) for sett in sett_list])
        else:
            settlement_logs.critical(f"时间：{one_day}，没有超时的自动结算")
        settlement_logs.critical(f"{one_day}之前的结算-超时结算定时器结束")
    except Exception as err:
        settlement_logs.error(f"超时定时结算错误:{err}")
