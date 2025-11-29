"""
Article validation utilities for filtering and identifying valid news articles.

This module provides functionality to distinguish between actual news articles
and non-article pages (category pages, author pages, tag pages, homepage, etc.).
"""

import re
import logging
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ArticleValidator:
    """
    Validator class for determining if a web page is a valid news article.
    
    Validates based on:
    - URL patterns (excludes category/tag/author pages)
    - Article metadata (publication date, author)
    - Content structure (headline, paragraphs)
    - Text length requirements
    """
    
    # URL patterns that typically indicate non-article pages
    NON_ARTICLE_URL_PATTERNS = [
        r'/tag/',
        r'/tags/',
        r'/category/',
        r'/categories/',
        r'/author/',
        r'/authors/',
        r'/search',
        r'/page/',
        r'/archive/',
        r'/archives/',
        r'/feed/',
        r'/rss',
        r'/sitemap',
        r'/about',
        r'/contact',
        r'/privacy',
        r'/terms',
        r'/login',
        r'/register',
        r'/subscribe',
        r'/newsletter',
    ]
    
    # URL patterns that indicate index/listing pages
    INDEX_PAGE_PATTERNS = [
        r'/$',  # Root URL
        r'/index\.',
        r'/home\.',
        r'/default\.',
        r'/latest/?$',
        r'/trending/?$',
        r'/popular/?$',
        r'/recent/?$',
    ]
    
    # Minimum content requirements
    MIN_ARTICLE_WORD_COUNT = 100
    MIN_PARAGRAPH_COUNT = 2
    MIN_TITLE_LENGTH = 10
    MAX_TITLE_LENGTH = 300
    
    @staticmethod
    def is_valid_article_url(url):
        """
        Check if URL pattern suggests it's an article (not a category/tag/index page).
        
        Args:
            url (str): Article URL to validate
            
        Returns:
            bool: True if URL pattern is valid for an article
        """
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Check for non-article patterns
            for pattern in ArticleValidator.NON_ARTICLE_URL_PATTERNS:
                if re.search(pattern, path, re.IGNORECASE):
                    logger.debug(f"URL rejected (non-article pattern): {url}")
                    return False
            
            # Check for index page patterns
            for pattern in ArticleValidator.INDEX_PAGE_PATTERNS:
                if re.search(pattern, path, re.IGNORECASE):
                    logger.debug(f"URL rejected (index pattern): {url}")
                    return False
            
            # Check for query parameters (usually search/filter pages)
            if parsed.query:
                params = parse_qs(parsed.query)
                # Common pagination/search parameters
                suspect_params = ['page', 'search', 'q', 'category', 'tag', 'filter']
                if any(param in params for param in suspect_params):
                    logger.debug(f"URL rejected (query params): {url}")
                    return False
            
            # Must have a path (not just domain)
            if not path or path == '/':
                logger.debug(f"URL rejected (no path): {url}")
                return False
            
            # File extensions that are not articles
            if re.search(r'\.(jpg|jpeg|png|gif|pdf|zip|css|js|xml|json)$', path, re.IGNORECASE):
                logger.debug(f"URL rejected (file extension): {url}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating URL {url}: {str(e)}")
            return False
    
    @staticmethod
    def extract_metadata(soup):
        """
        Extract article metadata from BeautifulSoup object.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            dict: Metadata including author, publish_date, title, etc.
        """
        metadata = {
            'author': None,
            'publish_date': None,
            'title': None,
            'description': None,
            'og_type': None,
        }
        
        # Extract Open Graph type
        og_type = soup.find('meta', property='og:type')
        if og_type and 'content' in og_type.attrs:
            metadata['og_type'] = og_type['content']
        
        # Extract title from meta tags
        og_title = soup.find('meta', property='og:title')
        if og_title and 'content' in og_title.attrs:
            metadata['title'] = og_title['content']
        
        # Extract description
        og_desc = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
        if og_desc and 'content' in og_desc.attrs:
            metadata['description'] = og_desc['content']
        
        # Extract author
        author_meta = soup.find('meta', attrs={'name': 'author'}) or \
                     soup.find('meta', property='article:author') or \
                     soup.find('meta', property='og:article:author')
        if author_meta and 'content' in author_meta.attrs:
            metadata['author'] = author_meta['content']
        
        # Extract publish date
        date_meta = soup.find('meta', property='article:published_time') or \
                   soup.find('meta', attrs={'name': 'publishdate'}) or \
                   soup.find('meta', attrs={'name': 'publication_date'}) or \
                   soup.find('meta', property='og:article:published_time')
        if date_meta and 'content' in date_meta.attrs:
            metadata['publish_date'] = date_meta['content']
        
        # Try to extract from time tags
        if not metadata['publish_date']:
            time_tag = soup.find('time', attrs={'datetime': True})
            if time_tag:
                metadata['publish_date'] = time_tag['datetime']
        
        return metadata
    
    @staticmethod
    def validate_article_structure(soup):
        """
        Validate that the page has proper article structure.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            dict: Validation results with 'is_valid' boolean and details
        """
        validation = {
            'is_valid': False,
            'has_title': False,
            'has_content': False,
            'has_metadata': False,
            'has_author': False,
            'has_date': False,
            'word_count': 0,
            'paragraph_count': 0,
            'reason': None
        }
        
        # Extract metadata
        metadata = ArticleValidator.extract_metadata(soup)
        
        # Check for article-specific Open Graph type
        if metadata['og_type'] and metadata['og_type'].lower() == 'article':
            validation['has_metadata'] = True
        
        # Check for author
        if metadata['author']:
            validation['has_author'] = True
        else:
            # Try finding author in common HTML patterns
            author_elem = soup.find(['span', 'div', 'a', 'p'], 
                                   class_=lambda c: c and any(x in c.lower() for x in ['author', 'byline', 'writer']))
            if author_elem:
                validation['has_author'] = True
        
        # Check for publish date
        if metadata['publish_date']:
            validation['has_date'] = True
        else:
            # Try finding date in common HTML patterns
            date_elem = soup.find(['span', 'time', 'div'], 
                                 class_=lambda c: c and any(x in c.lower() for x in ['date', 'published', 'time']))
            if date_elem:
                validation['has_date'] = True
        
        # Check for title
        title = metadata['title'] or (soup.title.text.strip() if soup.title else None)
        if title:
            title_length = len(title)
            if ArticleValidator.MIN_TITLE_LENGTH <= title_length <= ArticleValidator.MAX_TITLE_LENGTH:
                validation['has_title'] = True
        
        # Check for H1 (article headline)
        h1 = soup.find('h1')
        if h1 and not validation['has_title']:
            h1_text = h1.text.strip()
            if ArticleValidator.MIN_TITLE_LENGTH <= len(h1_text) <= ArticleValidator.MAX_TITLE_LENGTH:
                validation['has_title'] = True
        
        # Check for article content
        article_container = soup.find('article') or \
                           soup.find('div', class_=lambda c: c and any(x in c.lower() for x in ['article', 'content', 'story', 'post-content', 'entry-content']))
        
        if not article_container:
            # Fallback to main content area
            article_container = soup.find('main') or \
                              soup.find('div', id=lambda i: i and any(x in i.lower() for x in ['content', 'main', 'article']))
        
        if article_container:
            # Remove unwanted elements
            for element in article_container.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                element.decompose()
            
            # Count paragraphs
            paragraphs = article_container.find_all('p')
            meaningful_paragraphs = [p for p in paragraphs if len(p.text.strip()) > 20]
            validation['paragraph_count'] = len(meaningful_paragraphs)
            
            # Count words
            text_content = article_container.get_text(separator=' ', strip=True)
            words = text_content.split()
            validation['word_count'] = len(words)
            
            if validation['word_count'] >= ArticleValidator.MIN_ARTICLE_WORD_COUNT:
                validation['has_content'] = True
        
        # Determine if valid
        # Strict validation: Must have title, substantial content, and at least one metadata indicator
        if validation['has_title'] and validation['has_content']:
            if validation['has_metadata'] or validation['has_author'] or validation['has_date']:
                validation['is_valid'] = True
            else:
                # Relaxed validation for pages with strong content indicators
                if validation['word_count'] >= 300 and validation['paragraph_count'] >= 3:
                    validation['is_valid'] = True
                    validation['reason'] = 'Strong content indicators without explicit metadata'
                else:
                    validation['reason'] = 'Missing article metadata (author/date/og:type)'
        else:
            if not validation['has_title']:
                validation['reason'] = 'Missing or invalid title'
            elif not validation['has_content']:
                validation['reason'] = f'Insufficient content (words: {validation["word_count"]}, paragraphs: {validation["paragraph_count"]})'
        
        return validation
    
    @staticmethod
    def is_valid_article(url, html_content):
        """
        Main validation method to determine if a page is a valid news article.
        
        Args:
            url (str): Article URL
            html_content (str): HTML content of the page
            
        Returns:
            tuple: (is_valid: bool, validation_details: dict)
        """
        # First check URL pattern
        if not ArticleValidator.is_valid_article_url(url):
            return False, {
                'is_valid': False,
                'reason': 'URL pattern indicates non-article page',
                'url': url
            }
        
        # Parse HTML
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except Exception as e:
            logger.error(f"Error parsing HTML for {url}: {str(e)}")
            return False, {
                'is_valid': False,
                'reason': f'HTML parsing error: {str(e)}',
                'url': url
            }
        
        # Validate article structure
        validation = ArticleValidator.validate_article_structure(soup)
        validation['url'] = url
        
        return validation['is_valid'], validation


def is_valid_article(url, html_content):
    """
    Convenience function to validate if a page is a valid article.
    
    Args:
        url (str): Article URL
        html_content (str): HTML content of the page
        
    Returns:
        tuple: (is_valid: bool, validation_details: dict)
    """
    return ArticleValidator.is_valid_article(url, html_content)
