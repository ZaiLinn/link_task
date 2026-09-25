from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(
    timezone='Asia/Shanghai',
    job_defaults={'max_instances': 1, 'coalesce': False},
)
