from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from tasks.reset_missions import reset_daily_missions
from services.user_service import apply_monthly_bonus_to_all_users
from datetime import datetime
from services.leaderboard_service import update_leaderboard_cache

def schedule_all_jobs(bot):
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    # Ежедневно в 04:00 утра (после окончания дня)
    scheduler.add_job(reset_daily_missions, CronTrigger(hour=4, minute=0))

    scheduler.start()

def schedule_monthly_bonus(scheduler: AsyncIOScheduler):
    scheduler.add_job(
        apply_monthly_bonus_to_all_users,
        "cron",
        day=1,
        hour=7,
        minute=0,
        id="monthly_bonus",
        timezone="Europe/Moscow"
    )
    
    
def schedule_leaderboard_update(scheduler: AsyncIOScheduler):
    scheduler.add_job(
        update_leaderboard_cache,
        trigger="cron",
        hour=7,
        minute=0,
        id="daily_leaderboard_update",
        timezone="Europe/Moscow"
    )