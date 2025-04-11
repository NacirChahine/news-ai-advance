import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from newspaper import Article, build
from django.db import IntegrityError
from news_aggregator.models import NewsSource, NewsArticle

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetches news articles from configured sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source_id', 
            type=int, 
            help='ID of a specific news source to fetch (optional)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of articles to fetch per source'
        )

    def handle(self, *args, **options):
        source_id = options.get('source_id')
        limit = options.get('limit')
        
        if source_id:
            try:
                sources = [NewsSource.objects.get(id=source_id)]
                self.stdout.write(f"Fetching news from source: {sources[0].name}")
            except NewsSource.DoesNotExist:
                self.stderr.write(f"Error: News source with ID {source_id} does not exist")
                return
        else:
            sources = NewsSource.objects.all()
            self.stdout.write(f"Fetching news from {sources.count()} sources")
        
        for source in sources:
            self.fetch_articles_for_source(source, limit)
            
        self.stdout.write(self.style.SUCCESS('News article fetching completed!'))
    
    def fetch_articles_for_source(self, source, limit):
        """Fetch articles for a specific source"""
        self.stdout.write(f"Processing {source.name} ({source.url})")
        
        try:
            # Build a newspaper Source object
            news_source = build(source.url, memoize_articles=False)
            
            # Get article URLs
            news_source.download()
            news_source.parse()
            
            # Limit the number of articles to process
            article_urls = news_source.article_urls()
            count = 0
            
            for url in article_urls:
                if count >= limit:
                    break
                
                # Skip if we already have this article in the database
                if NewsArticle.objects.filter(url=url).exists():
                    continue
                
                try:
                    # Download and parse the article
                    article = Article(url)
                    article.download()
                    article.parse()
                    
                    # Skip articles without a title or content
                    if not article.title or not article.text:
                        continue
                    
                    # Parse publish date or use current time if not available
                    if article.publish_date:
                        published_date = article.publish_date
                    else:
                        published_date = timezone.now()
                    
                    # Create the NewsArticle instance
                    news_article = NewsArticle(
                        title=article.title,
                        source=source,
                        url=url,
                        author=', '.join(article.authors) if article.authors else '',
                        published_date=published_date,
                        content=article.text,
                        image_url=article.top_image,
                    )
                    news_article.save()
                    
                    count += 1
                    self.stdout.write(f"  Added: {article.title}")
                    
                except IntegrityError:
                    # Handle duplicate URLs (race condition)
                    continue
                except Exception as e:
                    self.stderr.write(f"  Error processing article {url}: {str(e)}")
            
            self.stdout.write(self.style.SUCCESS(f"Added {count} articles from {source.name}"))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error fetching articles from {source.name}: {str(e)}"))
