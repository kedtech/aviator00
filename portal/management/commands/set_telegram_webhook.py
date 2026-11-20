from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import os


class Command(BaseCommand):
    help = "Set Telegram webhook URL for this project (path: /telegram/webhook/)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            help="Full webhook URL, e.g. https://your-domain.com/telegram/webhook/",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete the current webhook instead of setting a new one",
        )
        parser.add_argument(
            "--info",
            action="store_true",
            help="Show current webhook info",
        )

    def handle(self, *args, **options):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", None) or os.getenv("TELEGRAM_BOT_TOKEN")

        if not token:
            self.stderr.write(
                self.style.ERROR(
                    "TELEGRAM_BOT_TOKEN is not set.\n"
                    "Add it to aviator.env or .env, then try again."
                )
            )
            return

        base_api = f"https://api.telegram.org/bot{token}"

        if options["info"]:
            try:
                response = requests.get(f"{base_api}/getWebhookInfo", timeout=15)
                data = response.json()
                self.stdout.write(self.style.SUCCESS("Current webhook info:"))
                self.stdout.write(str(data))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to get webhook info: {e}"))
            return

        if options["delete"]:
            try:
                response = requests.post(f"{base_api}/deleteWebhook", timeout=15)
                data = response.json()
                if data.get("ok"):
                    self.stdout.write(self.style.SUCCESS("Webhook deleted successfully."))
                else:
                    self.stderr.write(self.style.ERROR(f"Failed to delete webhook: {data}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error: {e}"))
            return

        webhook_url = options.get("url")

        if not webhook_url:
            render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
            if render_host:
                webhook_url = f"https://{render_host}/telegram/webhook/"
            else:
                self.stderr.write(
                    self.style.ERROR(
                        "No --url provided and RENDER_EXTERNAL_HOSTNAME is not set.\n"
                        "Usage example:\n"
                        "  python manage.py set_telegram_webhook --url https://your-domain.com/telegram/webhook/"
                    )
                )
                return

        # Ensure trailing path is correct
        if not webhook_url.rstrip("/").endswith("telegram/webhook"):
            self.stdout.write(
                self.style.WARNING(
                    "Tip: the Django URL is /telegram/webhook/ — make sure your URL ends with that."
                )
            )

        self.stdout.write(f"Setting webhook to: {webhook_url}")

        try:
            response = requests.post(
                f"{base_api}/setWebhook",
                json={"url": webhook_url},
                timeout=15,
            )
            data = response.json()

            if data.get("ok"):
                self.stdout.write(
                    self.style.SUCCESS(f"Webhook set successfully to:\n{webhook_url}")
                )
            else:
                self.stderr.write(self.style.ERROR(f"Failed to set webhook: {data}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error while setting webhook: {e}"))
