from django.core.management.base import BaseCommand
from news_aggregator.models import NewsSource
from news_aggregator.utils import update_source_reliability


class Command(BaseCommand):
    help = "Recalculate and persist reliability scores for all news sources"

    def add_arguments(self, parser):
        parser.add_argument('--only-zero', action='store_true', help='Only update sources with zero score')

    def handle(self, *args, **options):
        qs = NewsSource.objects.all()
        if options.get('only_zero'):
            qs = qs.filter(reliability_score__lte=0)
        count = 0
        for src in qs.iterator():
            score = update_source_reliability(src)
            self.stdout.write(self.style.SUCCESS(f"{src.name}: {score:.3f}/100"))
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Updated {count} source(s)"))

