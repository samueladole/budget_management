import pytest
from unittest.mock import patch
from datetime import datetime
from decimal import Decimal
from campaigns.models import Brand, Campaign, DaypartingSchedule
from campaigns.tasks import enforce_campaign_status, reset_daily, reset_monthly


@pytest.mark.django_db
def test_enforce_campaign_status_pauses_outside_dayparting() -> None:
    brand = Brand.objects.create(
        name="Brand1", daily_budget=Decimal("100"), monthly_budget=Decimal("1000")
    )
    campaign = Campaign.objects.create(
        brand=brand,
        name="Camp",
        current_daily_spend=Decimal("0"),
        current_monthly_spend=Decimal("0"),
        is_active=True,
    )

    DaypartingSchedule.objects.create(campaign=campaign, start_hour=9, end_hour=17)

    with patch("campaigns.tasks.datetime") as mock_datetime:
        # Setup mock datetime.now() to return 8am (outside dayparting)
        mock_datetime.now.return_value = datetime.now().replace(hour=8)
        mock_datetime.side_effect = datetime

        enforce_campaign_status()

    campaign.refresh_from_db()
    assert campaign.is_active is False


@pytest.mark.django_db
def test_enforce_campaign_status_enforces_budget_within_dayparting() -> None:
    brand = Brand.objects.create(
        name="Brand2", daily_budget=Decimal("100"), monthly_budget=Decimal("1000")
    )
    campaign = Campaign.objects.create(
        brand=brand,
        name="Camp2",
        current_daily_spend=Decimal("150"),  # over budget
        current_monthly_spend=Decimal("500"),
        is_active=True,
    )

    DaypartingSchedule.objects.create(campaign=campaign, start_hour=0, end_hour=23)

    with patch("campaigns.tasks.datetime") as mock_datetime:
        # Setup mock datetime.now() to return 12pm (within dayparting)
        mock_datetime.now.return_value = datetime.now().replace(hour=12)
        mock_datetime.side_effect = datetime

        enforce_campaign_status()

    campaign.refresh_from_db()
    assert campaign.is_active is False


@pytest.mark.django_db
def test_reset_daily_and_monthly_tasks() -> None:
    brand = Brand.objects.create(
        name="Brand3", daily_budget=Decimal("100"), monthly_budget=Decimal("1000")
    )
    campaign = Campaign.objects.create(
        brand=brand,
        name="Camp3",
        current_daily_spend=Decimal("50"),
        current_monthly_spend=Decimal("500"),
        is_active=False,
    )

    reset_daily()
    campaign.refresh_from_db()
    assert campaign.current_daily_spend == Decimal("0.00")
    assert campaign.is_active is True

    campaign.current_daily_spend = Decimal("20")
    campaign.is_active = False
    campaign.save()

    reset_monthly()
    campaign.refresh_from_db()
    assert campaign.current_monthly_spend == Decimal("0.00")
