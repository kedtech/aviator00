from django.db import models
from django.utils import timezone
import uuid


class DemoSession(models.Model):
    PLATFORM_CHOICES = [
        ("SPIN CITY", "Spin City"),
        ("MWNOS", "MWNOS"),
        ("AFRICANBET", "Africanbet"),
    ]
    STATUS_CHOICES = [
        ("started", "Started"),
        ("pending_four", "Pending Four Review"),
        ("four_approved", "Four Approved"),
        ("four_rejected", "Four Rejected"),
        ("pending_six", "Pending Six Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES)
    demo_points = models.PositiveIntegerField(default=100)
    phone_number = models.CharField(max_length=20, blank=True)
    six_numbers = models.CharField(max_length=32, blank=True)
    four_numbers = models.CharField(max_length=24, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="started")
    created_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.platform} · {str(self.reference)[:8]} · {self.status}"


class DemoEvent(models.Model):
    session = models.ForeignKey(DemoSession, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=40)
    description = models.CharField(max_length=240)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.event_type} - {self.created_at:%Y-%m-%d %H:%M}"
