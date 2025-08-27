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


def render_alert_email(alert: MisinformationAlert) -> Tuple[str, str]:
    """Render subject and body (plain and optional HTML) for an alert email."""
    subject = f"Misinformation Alert: {alert.title} ({alert.severity.title()})"

    context = {
        "alert": alert,
        "site_name": getattr(settings, "SITE_NAME", "News Advance"),
        "settings_url": getattr(settings, "ALERT_SETTINGS_URL", "/accounts/preferences/"),
        "generated_at": timezone.now(),
    }

    text_body = render_to_string("emails/misinformation_alert.txt", context)
    html_body = None
    try:
        html_body = render_to_string("emails/misinformation_alert.html", context)
    except Exception:
        # HTML template optional; ignore if not present
        html_body = None

    return subject, text_body, html_body


def send_misinformation_alert_email(alert: MisinformationAlert, recipients: Optional[Iterable[str]] = None, dry_run: bool = False) -> dict:
    """
    Send a misinformation alert email to opted-in users (or provided recipients).

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

    if html_body:
        # Use EmailMultiAlternatives to include HTML
        try:
            msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, recipients)
            msg.attach_alternative(html_body, "text/html")
            sent_count = msg.send()
        except Exception as e:
            errors.append(str(e))
    else:
        try:
            sent_count = send_mail(subject, text_body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
        except Exception as e:
            errors.append(str(e))

    return {"sent": sent_count, "recipients": len(recipients), "errors": errors, "dry_run": False}

