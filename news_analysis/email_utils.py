from typing import Iterable, List, Optional, Tuple
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from accounts.models import UserPreferences
from django.contrib.auth.models import User
from .models import MisinformationAlert


def get_opted_in_recipient_emails() -> List[str]:
    """Return list of recipient emails for users who opted into misinformation alerts."""
    qs = User.objects.filter(
        preferences__receive_misinformation_alerts=True,
        is_active=True,
    ).exclude(email="").values_list("email", flat=True).distinct()
    return list(qs)


def render_alert_email(alert: MisinformationAlert) -> Tuple[str, str, Optional[str]]:
    """Render subject and body (plain and optional HTML) for an alert email."""
    subject = f"Misinformation Alert: {alert.title} ({alert.severity.title()})"

    base_url = getattr(settings, "SITE_URL", "http://localhost:8000")

    context = {
        "alert": alert,
        "site_name": getattr(settings, "SITE_NAME", "News Advance"),
        "settings_url": getattr(settings, "ALERT_SETTINGS_URL", "/accounts/preferences/"),
        "base_url": base_url,
        "generated_at": timezone.now(),
    }

    text_body = render_to_string("emails/misinformation_alert.txt", context)
    try:
        html_body = render_to_string("emails/misinformation_alert.html", context)
    except Exception:
        # HTML template optional; ignore if not present
        html_body = None

    return subject, text_body, html_body


def send_misinformation_alert_email(alert: MisinformationAlert, recipients: Optional[Iterable[str]] = None, dry_run: bool = False) -> dict:
    """
    Send a misinformation alert email to opted-in users (or provided recipients).

    PRIVACY: Sends individual emails to each recipient to protect privacy.
    Each recipient only sees their own email address, not others.

    Returns a dict with counts and any errors.
    """
    if recipients is None:
        recipients = get_opted_in_recipient_emails()

    recipients = list(set([r.strip() for r in recipients if r and "@" in r]))
    if not recipients:
        return {"sent": 0, "recipients": 0, "errors": [], "dry_run": dry_run}

    subject, text_body, html_body = render_alert_email(alert)

    if dry_run:
        return {"sent": 0, "recipients": len(recipients), "errors": [], "dry_run": True, "subject": subject}

    errors: List[str] = []
    sent_count = 0

    # Send individual emails to protect recipient privacy
    for recipient_email in recipients:
        try:
            if html_body:
                # Use EmailMultiAlternatives to include HTML
                msg = EmailMultiAlternatives(
                    subject,
                    text_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient_email]  # Single recipient only
                )
                msg.attach_alternative(html_body, "text/html")
                result = msg.send()
                if result:
                    sent_count += 1
            else:
                # Use simple send_mail for text-only
                result = send_mail(
                    subject,
                    text_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient_email],  # Single recipient only
                    fail_silently=False
                )
                if result:
                    sent_count += 1
        except Exception as e:
            errors.append(f"Failed to send to {recipient_email}: {str(e)}")

    return {"sent": sent_count, "recipients": len(recipients), "errors": errors, "dry_run": False}

