from django.contrib import admin
from .models import Brand, Campaign, SpendLog, DaypartingSchedule


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "daily_budget", "monthly_budget")
    search_fields = ("name",)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "is_active",
        "current_daily_spend",
        "current_monthly_spend",
    )
    list_filter = ("is_active", "brand")
    search_fields = ("name",)


@admin.register(SpendLog)
class SpendLogAdmin(admin.ModelAdmin):
    list_display = ("campaign", "timestamp", "amount")
    list_filter = ("campaign", "timestamp")
    readonly_fields = ("timestamp",)


@admin.register(DaypartingSchedule)
class DaypartingScheduleAdmin(admin.ModelAdmin):
    list_display = ("campaign", "start_hour", "end_hour")
    list_filter = ("start_hour", "end_hour")
