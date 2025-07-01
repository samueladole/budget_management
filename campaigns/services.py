from datetime import datetime
from decimal import Decimal
from django.db import transaction
from .models import Campaign, SpendLog


def is_within_dayparting(campaign: Campaign, now: datetime) -> bool:
    if not hasattr(campaign, "daypartingschedule"):
        return True
    schedule = campaign.daypartingschedule
    return schedule.start_hour <= now.hour < schedule.end_hour


def enforce_budget(campaign: Campaign) -> None:
    brand = campaign.brand
    if (
        campaign.current_daily_spend >= brand.daily_budget
        or campaign.current_monthly_spend >= brand.monthly_budget
    ):
        campaign.is_active = False
        campaign.save()


def reset_daily_budgets() -> None:
    for campaign in Campaign.objects.all():
        campaign.current_daily_spend = Decimal("0.00")
        campaign.is_active = True
        campaign.save()


def reset_monthly_budgets() -> None:
    for campaign in Campaign.objects.all():
        campaign.current_monthly_spend = Decimal("0.00")
        campaign.save()


def log_spend(campaign_id: int, amount: Decimal) -> None:
    """
    Log a spend for a campaign, update campaign spend,
    and pause campaign if budgets are exceeded.
    """
    with transaction.atomic():
        campaign = (
            Campaign.objects.select_for_update()
            .select_related("brand")
            .get(id=campaign_id)
        )

        if not campaign.is_active:
            # Skip logging spend if campaign is inactive
            raise ValueError("Cannot log spend for an inactive campaign.")

        # Create spend log
        SpendLog.objects.create(campaign=campaign, amount=amount)

        # Update campaign spend totals
        campaign.current_daily_spend += amount
        campaign.current_monthly_spend += amount

        # Check budget limits
        if (
            campaign.current_daily_spend > campaign.brand.daily_budget
            or campaign.current_monthly_spend > campaign.brand.monthly_budget
        ):
            campaign.is_active = False  # Pause campaign

        campaign.save(
            update_fields=["current_daily_spend", "current_monthly_spend", "is_active"]
        )
