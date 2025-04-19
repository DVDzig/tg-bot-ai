from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from tasks.reset_missions import (
    reset_daily_missions, 
    reset_expired_subscriptions,
    send_reminder_messages
)
from services.user_service import apply_monthly_bonus_to_all_users
from datetime import datetime


def schedule_all_jobs(scheduler: AsyncIOScheduler):
    # Сброс ежедневных миссий в 03:00 по Москве
    scheduler.add_job(reset_daily_missions, "cron", hour=3, minute=0)

    # Сброс просроченных подписок в 04:00 по Москве
    scheduler.add_job(reset_expired_subscriptions, "cron", hour=4, minute=0)
    
    # Проверка напоминаний — каждый день в 10:00
    scheduler.add_job(send_reminder_messages, "cron", hour=10, minute=0)


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
