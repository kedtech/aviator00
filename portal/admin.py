from django.contrib import admin
from .models import DemoSession, DemoEvent
class DemoEventInline(admin.TabularInline):
    model = DemoEvent
    extra = 0
    readonly_fields = ("event_type", "description", "created_at")
@admin.register(DemoSession)
class DemoSessionAdmin(admin.ModelAdmin):
    list_display = ("reference", "platform", "demo_points", "phone_number", "four_numbers", "six_numbers", "status", "created_at")
    list_filter = ("platform", "status", "created_at")
    search_fields = ("reference", "phone_number", "four_numbers", "six_numbers")
    readonly_fields = ("reference", "created_at")
    inlines = [DemoEventInline]
@admin.register(DemoEvent)
class DemoEventAdmin(admin.ModelAdmin):
    list_display = ("session", "event_type", "created_at")
    readonly_fields = ("created_at",)
