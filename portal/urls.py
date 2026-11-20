from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("start/", views.start_demo, name="start_demo"),
    path("amount/", views.amount, name="amount"),
    path("confirm-amount/", views.confirm_amount, name="confirm_amount"),
    path("numbers/six/", views.six_numbers, name="six_numbers"),
    path("numbers/six/save/", views.save_six_numbers, name="save_six_numbers"),
    path("numbers/four/", views.four_numbers, name="four_numbers"),
    path("numbers/four/save/", views.save_four_numbers, name="save_four_numbers"),
    path("waiting/four/", views.waiting_four, name="waiting_four"),
    path("success/", views.success, name="success"),
    path("reset/", views.reset_demo, name="reset_demo"),
    # Telegram webhook for Approve / Reject buttons
    path("telegram/webhook/", views.telegram_webhook, name="telegram_webhook"),
]
