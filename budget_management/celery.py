import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budget_management.settings")

app = Celery("budget_management")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "enforce-campaign-status-every-5-minutes": {
        "task": "campaigns.tasks.enforce_campaign_status",
        "schedule": crontab(minute="*/5"),  # every 5 minutes
    },
    "reset-daily-spend-at-midnight": {
        "task": "campaigns.tasks.reset_daily",
        "schedule": crontab(minute=0, hour=0),  # every day at midnight
    },
    "reset-monthly-spend-on-first": {
        "task": "campaigns.tasks.reset_monthly",
        "schedule": crontab(
            minute=0, hour=0, day_of_month="1"
        ),  # 1st day of month at midnight
    },
}
