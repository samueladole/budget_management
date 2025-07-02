from datetime import datetime
from typing import Callable, TypeVar

from celery import shared_task as celery_shared_task

from .models import Campaign
from .services import (
    enforce_budget,
    is_within_dayparting,
    reset_daily_budgets,
    reset_monthly_budgets,
)

F = TypeVar("F", bound=Callable[..., object])


def shared_task(func: F) -> F:
    return celery_shared_task(func)  # type: ignore


@shared_task
def enforce_campaign_status() -> None:
    now = datetime.now()
    for campaign in Campaign.objects.select_related("brand"):
        if is_within_dayparting(campaign, now):
            enforce_budget(campaign)
        else:
            campaign.is_active = False
            campaign.save()


@shared_task
def reset_daily() -> None:
    reset_daily_budgets()


@shared_task
def reset_monthly() -> None:
    reset_monthly_budgets()
