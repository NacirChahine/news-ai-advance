from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from typing import Optional
from news_analysis.models import MisinformationAlert
from news_analysis.email_utils import send_misinformation_alert_email

class Command(BaseCommand):
    help = "Send misinformation alert emails to opted-in users"

    def add_arguments(self, parser):
        parser.add_argument('--alert-id', type=int, help='Specific alert ID to send')
        parser.add_argument('--since', type=str, help='Send alerts detected since YYYY-MM-DD')
        parser.add_argument('--active-only', action='store_true', help='Only send active alerts')
        parser.add_argument('--dry-run', action='store_true', help='Do not send, just report counts')

    def handle(self, *args, **options):
        alert_id: Optional[int] = options.get('alert_id')
        since_str: Optional[str] = options.get('since')
        active_only: bool = options.get('active_only', False)
        dry_run: bool = options.get('dry_run', False)

        qs = MisinformationAlert.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        if since_str:
            try:
                since_dt = datetime.strptime(since_str, '%Y-%m-%d')
                qs = qs.filter(detected_at__gte=since_dt)
            except ValueError:
                self.stderr.write(self.style.ERROR("Invalid --since format. Use YYYY-MM-DD"))
                return
        if alert_id:
            qs = qs.filter(id=alert_id)

        count = qs.count()
        if count == 0:
            self.stdout.write("No alerts match the given criteria.")
            return

        total_sent = 0
        total_errors = []
        for alert in qs.order_by('-detected_at'):
            result = send_misinformation_alert_email(alert, recipients=None, dry_run=dry_run)
            if dry_run:
                self.stdout.write(f"[DRY RUN] Would send '{alert.title}' to {result.get('recipients', 0)} recipients.")
            else:
                self.stdout.write(f"Sent '{alert.title}' to {result.get('recipients', 0)} recipients; delivered: {result.get('sent', 0)}")
                total_sent += result.get('sent', 0)
                errs = result.get('errors', [])
                if errs:
                    total_errors.extend(errs)

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry run completed."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Completed sending. Total delivered: {total_sent}"))
            if total_errors:
                self.stderr.write(self.style.WARNING(f"Errors encountered: {', '.join(total_errors)}"))

