import pytest
from decimal import Decimal
from datetime import datetime
from campaigns.models import Brand, Campaign, DaypartingSchedule, SpendLog
from campaigns.services import (
    is_within_dayparting,
    enforce_budget,
    reset_daily_budgets,
    reset_monthly_budgets,
    log_spend,
)


@pytest.mark.django_db
def test_is_within_dayparting_no_schedule() -> None:
    brand = Brand.objects.create(name="BrandX", daily_budget=100, monthly_budget=1000)
    campaign = Campaign.objects.create(brand=brand, name="CampaignNoSchedule")
    now = datetime(2023, 1, 1, 10, 0)
    # campaign has no daypartingschedule attribute
    assert is_within_dayparting(campaign, now) is True


@pytest.mark.django_db
def test_is_within_dayparting_with_schedule() -> None:
    brand = Brand.objects.create(name="BrandY", daily_budget=100, monthly_budget=1000)
    campaign = Campaign.objects.create(brand=brand, name="CampaignWithSchedule")

    # Create real DaypartingSchedule linked to campaign
    DaypartingSchedule.objects.create(
        campaign=campaign,
        start_hour=9,
        end_hour=17,
    )

    # Reload campaign from DB to ensure relation is loaded
    campaign.refresh_from_db()

    # Inside dayparting hours
    now = datetime(2023, 1, 1, 10, 0)
    assert is_within_dayparting(campaign, now) is True

    # Exactly at start_hour (inclusive)
    now = datetime(2023, 1, 1, 9, 0)
    assert is_within_dayparting(campaign, now) is True

    # Exactly at end_hour (exclusive)
    now = datetime(2023, 1, 1, 17, 0)
    assert is_within_dayparting(campaign, now) is False

    # Before start_hour
    now = datetime(2023, 1, 1, 8, 59)
    assert is_within_dayparting(campaign, now) is False

    # After end_hour
    now = datetime(2023, 1, 1, 18, 0)
    assert is_within_dayparting(campaign, now) is False


@pytest.mark.django_db
def test_enforce_budget_below_limits() -> None:
    brand = Brand.objects.create(
        name="BrandA", daily_budget=Decimal("100.00"), monthly_budget=Decimal("1000.00")
    )
    campaign = Campaign.objects.create(
        brand=brand,
        name="Campaign1",
        current_daily_spend=Decimal("50.00"),
        current_monthly_spend=Decimal("500.00"),
        is_active=True,
    )

    enforce_budget(campaign)
    campaign.refresh_from_db()
    assert campaign.is_active is True


@pytest.mark.django_db
def test_enforce_budget_at_limits() -> None:
    brand = Brand.objects.create(
        name="BrandB", daily_budget=Decimal("100.00"), monthly_budget=Decimal("1000.00")
    )
    campaign = Campaign.objects.create(
        brand=brand,
        name="Campaign2",
        current_daily_spend=Decimal("100.00"),
        current_monthly_spend=Decimal("1000.00"),
        is_active=True,
    )

    enforce_budget(campaign)
    campaign.refresh_from_db()
    assert campaign.is_active is False


@pytest.mark.django_db
def test_enforce_budget_above_limits() -> None:
    brand = Brand.objects.create(
        name="BrandC", daily_budget=Decimal("100.00"), monthly_budget=Decimal("1000.00")
    )
    campaign = Campaign.objects.create(
        brand=brand,
        name="Campaign3",
        current_daily_spend=Decimal("150.00"),
        current_monthly_spend=Decimal("1200.00"),
        is_active=True,
    )

    enforce_budget(campaign)
    campaign.refresh_from_db()
    assert campaign.is_active is False


@pytest.mark.django_db
def test_reset_daily_budgets() -> None:
    brand = Brand.objects.create(
        name="BrandTest",
        daily_budget=Decimal("100.00"),
        monthly_budget=Decimal("1000.00"),
    )

    # Create two campaigns with non-zero daily spend and inactive status
    campaign1 = Campaign.objects.create(
        brand=brand,
        name="Campaign 1",
        current_daily_spend=Decimal("50.00"),
        is_active=False,
    )
    campaign2 = Campaign.objects.create(
        brand=brand,
        name="Campaign 2",
        current_daily_spend=Decimal("75.00"),
        is_active=False,
    )

    # Call the function under test
    reset_daily_budgets()

    # Refresh from DB to get latest values
    campaign1.refresh_from_db()
    campaign2.refresh_from_db()

    # Assert daily spend reset and campaigns reactivated
    assert campaign1.current_daily_spend == Decimal("0.00")
    assert campaign1.is_active is True

    assert campaign2.current_daily_spend == Decimal("0.00")
    assert campaign2.is_active is True


@pytest.mark.django_db
def test_reset_monthly_budgets() -> None:
    brand = Brand.objects.create(
        name="BrandTest",
        daily_budget=Decimal("100.00"),
        monthly_budget=Decimal("1000.00"),
    )

    # Create campaigns with non-zero monthly spend
    campaign1 = Campaign.objects.create(
        brand=brand,
        name="Campaign 1",
        current_monthly_spend=Decimal("500.00"),
    )
    campaign2 = Campaign.objects.create(
        brand=brand,
        name="Campaign 2",
        current_monthly_spend=Decimal("750.00"),
    )

    # Call the function
    reset_monthly_budgets()

    # Refresh campaigns to get updated values
    campaign1.refresh_from_db()
    campaign2.refresh_from_db()

    # Assert monthly spends are reset
    assert campaign1.current_monthly_spend == Decimal("0.00")
    assert campaign2.current_monthly_spend == Decimal("0.00")


@pytest.mark.django_db
def test_log_spend_normal() -> None:
    brand = Brand.objects.create(
        name="BrandA", daily_budget=Decimal("100.00"), monthly_budget=Decimal("1000.00")
    )
    campaign = Campaign.objects.create(
        brand=brand,
        name="Camp1",
        current_daily_spend=Decimal("0.00"),
        current_monthly_spend=Decimal("0.00"),
        is_active=True,
    )

    log_spend(campaign.id, Decimal("10.00"))

    campaign.refresh_from_db()
    spend_logs = SpendLog.objects.filter(campaign=campaign)

    assert len(spend_logs) == 1
    assert spend_logs[0].amount == Decimal("10.00")
    assert campaign.current_daily_spend == Decimal("10.00")
    assert campaign.current_monthly_spend == Decimal("10.00")
    assert campaign.is_active is True


@pytest.mark.django_db
def test_log_spend_pause_campaign() -> None:
    brand = Brand.objects.create(
        name="BrandB", daily_budget=Decimal("50.00"), monthly_budget=Decimal("100.00")
    )
    campaign = Campaign.objects.create(
        brand=brand,
        name="Camp2",
        current_daily_spend=Decimal("45.00"),
        current_monthly_spend=Decimal("90.00"),
        is_active=True,
    )

    # This spend exceeds daily budget (45 + 10 > 50)
    log_spend(campaign.id, Decimal("10.00"))

    campaign.refresh_from_db()
    spend_logs = SpendLog.objects.filter(campaign=campaign)

    assert len(spend_logs) == 1
    assert campaign.current_daily_spend == Decimal("55.00")
    assert campaign.current_monthly_spend == Decimal("100.00")
    assert campaign.is_active is False  # campaign paused


@pytest.mark.django_db
def test_log_spend_inactive_campaign_raises() -> None:
    brand = Brand.objects.create(
        name="BrandC", daily_budget=Decimal("100.00"), monthly_budget=Decimal("1000.00")
    )
    campaign = Campaign.objects.create(
        brand=brand,
        name="Camp3",
        current_daily_spend=Decimal("0.00"),
        current_monthly_spend=Decimal("0.00"),
        is_active=False,
    )

    with pytest.raises(ValueError, match="Cannot log spend for an inactive campaign."):
        log_spend(campaign.id, Decimal("10.00"))
