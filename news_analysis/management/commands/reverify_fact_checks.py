import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from news_analysis.models import FactCheckResult
from news_aggregator.models import NewsArticle
from news_analysis.utils import verify_claim_with_ai

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Re-verify existing fact checks using an LLM (Ollama) with simple rate limiting"

    def add_arguments(self, parser):
        parser.add_argument('--article_id', type=int, help='Only re-verify fact-checks for this article ID')
        parser.add_argument('--only-unverified', action='store_true', help='Only re-verify entries rated unverified')
        parser.add_argument('--older-than-days', type=int, default=14, help='Only re-verify entries older than N days (default: 14)')
        parser.add_argument('--limit', type=int, default=50, help='Max number of fact checks to process (default: 50)')
        parser.add_argument('--model', type=str, default='llama3', help='Ollama model to use (default: llama3)')
        parser.add_argument('--delay', type=float, default=1.0, help='Seconds to sleep between verifications (default: 1.0)')

    def handle(self, *args, **options):
        article_id = options['article_id']
        only_unverified = options['only_unverified']
        older_than_days = options['older_than_days']
        limit = options['limit']
        model = options['model']
        delay = options['delay']

        qs = FactCheckResult.objects.all().select_related('article')
        if article_id:
            qs = qs.filter(article_id=article_id)
        if only_unverified:
            qs = qs.filter(rating='unverified')
        if older_than_days and older_than_days > 0:
            cutoff = timezone.now() - timezone.timedelta(days=older_than_days)
            qs = qs.filter(Q(last_verified__lt=cutoff) | Q(last_verified__isnull=True))

        total = qs.count()
        if total == 0:
            self.stdout.write("No fact checks match the criteria.")
            return

        self.stdout.write(f"Re-verifying up to {min(limit, total)} of {total} fact checks...")

        processed = 0
        for fc in qs.order_by('last_verified', 'id')[:limit]:
            try:
                article = fc.article
                content = article.content or ''
                result = verify_claim_with_ai(fc.claim, context_text=content, model=model)
                fc.rating = result.get('rating', fc.rating)
                fc.explanation = result.get('explanation', fc.explanation)[:2000]
                fc.sources = str(result.get('sources', fc.sources))[:1000]
                conf = result.get('confidence')
                if conf is not None:
                    fc.confidence = conf
                fc.last_verified = timezone.now()
                fc.save(update_fields=['rating', 'explanation', 'sources', 'confidence', 'last_verified'])
                processed += 1
                self.stdout.write(f"  Updated fact-check {fc.id} (rating={fc.rating})")
                time.sleep(max(0.0, delay))
            except Exception as e:
                logger.exception("Error re-verifying fact-check %s", fc.id)
                self.stderr.write(f"  Error re-verifying {fc.id}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Done. Processed {processed} fact checks."))

