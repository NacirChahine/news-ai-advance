import datetime
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import IntegrityError
from news_aggregator.models import NewsSource, NewsArticle
from news_aggregator.article_validator import ArticleValidator

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
        parser.add_argument(
            '--scrape-all',
            action='store_true',
            help='Scrape all pages without article validation (includes category pages, etc.)'
        )

    def handle(self, *args, **options):
        source_id = options.get('source_id')
        limit = options.get('limit')
        scrape_all = options.get('scrape_all', False)

        if scrape_all:
            self.stdout.write(self.style.WARNING('Article validation is DISABLED. All pages will be scraped.'))
        else:
            self.stdout.write('Article validation is ENABLED. Only valid articles will be scraped.')

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
            self.fetch_articles_for_source(source, limit, scrape_all)

        self.stdout.write(self.style.SUCCESS('News article fetching completed!'))

    def fetch_articles_for_source(self, source, limit, scrape_all=False):
        """Fetch articles for a specific source"""
        self.stdout.write(f"Processing {source.name} ({source.url})")

        try:
            # Get the main page to extract article links
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(source.url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an error for bad responses

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'lxml')

            # Find all links that might be articles
            article_links = []
            base_domain = urlparse(source.url).netloc

            for link in soup.find_all('a', href=True):
                url = link['href']

                # Handle relative URLs
                if not url.startswith('http'):
                    url = urljoin(source.url, url)

                # Basic URL filtering
                url_path = urlparse(url).path
                parsed_url = urlparse(url)
                
                # Skip if not from same domain
                if parsed_url.netloc != base_domain:
                    continue
                
                # Skip file extensions
                if url_path.endswith(('.jpg', '.png', '.pdf', '.zip', '.css', '.js')):
                    continue
                
                # Skip anchors
                if '#' in url:
                    continue

                # Apply URL validation if not scraping all
                if not scrape_all:
                    if not ArticleValidator.is_valid_article_url(url):
                        continue
                else:
                    # Minimal filtering for scrape-all mode
                    if (not url_path.strip('/') or
                        '/tag/' in url_path or
                        '/category/' in url_path):
                        continue

                article_links.append(url)

            # Remove duplicates and limit
            article_links = list(dict.fromkeys(article_links))[:limit * 3]  # Get more than needed in case some fail

            count = 0
            skipped_validation = 0
            skipped_existing = 0
            
            for url in article_links:
                if count >= limit:
                    break

                # Skip if we already have this article in the database
                if NewsArticle.objects.filter(url=url).exists():
                    skipped_existing += 1
                    continue

                try:
                    # Download and parse the article
                    article_response = requests.get(url, headers=headers, timeout=10)
                    article_response.raise_for_status()
                    article_html = article_response.text
                    article_soup = BeautifulSoup(article_html, 'lxml')

                    # Validate article if not in scrape-all mode
                    if not scrape_all:
                        is_valid, validation_details = ArticleValidator.is_valid_article(url, article_html)
                        if not is_valid:
                            skipped_validation += 1
                            logger.debug(f"Skipped {url}: {validation_details.get('reason', 'Invalid article')}")
                            continue

                    # Extract title - looking for common patterns
                    title = None
                    if article_soup.title:
                        title = article_soup.title.text.strip()

                    # Try to find a more specific title
                    title_tag = article_soup.find('h1') or article_soup.find('h2', class_=lambda c: c and (
                                'title' in c or 'heading' in c))
                    if title_tag:
                        title = title_tag.text.strip()

                    # Extract content - this is simplified and might need customization
                    content_div = article_soup.find('article') or article_soup.find('div', class_=lambda c: c and (
                                'article' in c or 'content' in c or 'story' in c))

                    if not content_div:
                        # Fallback to main content area
                        content_div = article_soup.find('main') or article_soup.find('div', id=lambda i: i and (
                                    'content' in i or 'main' in i))

                    if content_div:
                        # Remove script, style, and nav elements
                        for element in content_div.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                            element.decompose()

                        # Get all paragraphs
                        paragraphs = [p.text.strip() for p in content_div.find_all('p') if p.text.strip()]
                        content = '\n\n'.join(paragraphs)
                    else:
                        content = ""

                    # Skip articles without a title or content
                    if not title or not content:
                        continue

                    # Try to find author
                    author = ""
                    author_elem = article_soup.find(['span', 'div', 'a'],
                                                    class_=lambda c: c and ('author' in c or 'byline' in c))
                    if author_elem:
                        author = author_elem.text.strip()

                    # Try to extract publish date from metadata
                    published_date = None
                    date_meta = article_soup.find('meta', property='article:published_time') or \
                               article_soup.find('meta', attrs={'name': 'publishdate'}) or \
                               article_soup.find('meta', attrs={'name': 'publication_date'})
                    if date_meta and 'content' in date_meta.attrs:
                        try:
                            from dateutil import parser as date_parser
                            published_date = date_parser.parse(date_meta['content'])
                        except Exception:
                            pass
                    
                    # Try time tag if metadata not found
                    if not published_date:
                        time_tag = article_soup.find('time', attrs={'datetime': True})
                        if time_tag:
                            try:
                                from dateutil import parser as date_parser
                                published_date = date_parser.parse(time_tag['datetime'])
                            except Exception:
                                pass
                    
                    # Use current time as fallback
                    if not published_date:
                        published_date = timezone.now()

                    # Try to find image
                    image_url = ""
                    main_image = article_soup.find('meta', property='og:image') or article_soup.find('meta', attrs={
                        'name': 'twitter:image'})
                    if main_image and 'content' in main_image.attrs:
                        image_url = main_image['content']
                    else:
                        # Fallback to first large image in the article
                        img_tag = article_soup.find('img', class_=lambda c: c and (
                                    'featured' in c or 'main' in c or 'hero' in c))
                        if img_tag and 'src' in img_tag.attrs:
                            image_url = urljoin(url, img_tag['src'])

                    # Create the NewsArticle instance
                    news_article = NewsArticle(
                        title=title,
                        source=source,
                        url=url,
                        author_name=author,
                        published_date=published_date,
                        content=content,
                        image_url=image_url,
                    )
                    news_article.save()

                    count += 1
                    self.stdout.write(f"  ✓ Added: {title[:80]}{'...' if len(title) > 80 else ''}")

                except IntegrityError:
                    # Handle duplicate URLs (race condition)
                    skipped_existing += 1
                    continue
                except Exception as e:
                    self.stderr.write(f"  ✗ Error processing article {url}: {str(e)}")

            # Summary output
            self.stdout.write(self.style.SUCCESS(f"Added {count} articles from {source.name}"))
            if skipped_existing > 0:
                self.stdout.write(f"  Skipped {skipped_existing} existing articles")
            if skipped_validation > 0 and not scrape_all:
                self.stdout.write(f"  Skipped {skipped_validation} non-article pages (validation)")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error fetching articles from {source.name}: {str(e)}"))