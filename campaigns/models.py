from django.db import models
from decimal import Decimal


class Brand(models.Model):
    name = models.CharField(max_length=255)
    daily_budget = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self) -> str:
        return self.name


class Campaign(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    current_daily_spend = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    current_monthly_spend = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    def __str__(self) -> str:
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class SpendLog(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.amount} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class DaypartingSchedule(models.Model):
    campaign = models.OneToOneField(
        Campaign, on_delete=models.CASCADE, related_name="daypartingschedule"
    )
    start_hour = models.PositiveSmallIntegerField()  # 0-23
    end_hour = models.PositiveSmallIntegerField()  # 0-23

    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.start_hour}:00 to {self.end_hour}:00"
