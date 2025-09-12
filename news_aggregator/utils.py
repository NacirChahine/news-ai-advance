"""
Utility functions for news aggregation and article handling.
"""
import re
import logging
import requests
from urllib.parse import urlparse
from newspaper import Article, ArticleException
from bs4 import BeautifulSoup
from django.utils import timezone

logger = logging.getLogger(__name__)

def clean_html(html_content):
    """
    Clean HTML content by removing scripts, styles, and other unwanted elements.

    Args:
        html_content (str): Raw HTML content

    Returns:
        str: Cleaned HTML
    """
    if not html_content:
        return ""

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove scripts, styles, and comments
    for element in soup(['script', 'style', 'iframe', 'meta', 'noscript']):
        element.decompose()

    # Remove comment nodes
    for comment in soup.findAll(text=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
        comment.extract()

    return str(soup)

def extract_article_content(url, timeout=10):
    """
    Extract article content from a URL using newspaper3k.

    Args:
        url (str): URL of the article
        timeout (int): Request timeout in seconds

    Returns:
        dict: Dictionary containing article details or None if extraction failed
    """
    try:
        # Create and download article
        article = Article(url)
        article.download()
        article.parse()

        # Extract and process data
        title = article.title
        content = article.text
        authors = article.authors
        publish_date = article.publish_date or timezone.now()
        top_image = article.top_image

        # Return structured data
        return {
            'title': title,
            'content': content,
            'authors': authors,
            'publish_date': publish_date,
            'top_image': top_image,
            'url': url
        }

    except ArticleException as e:
        logger.error(f"Error extracting article from {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error extracting article from {url}: {str(e)}")
        return None

def get_domain_from_url(url):
    """
    Extract the domain from a URL.

    Args:
        url (str): URL to parse

    Returns:
        str: Domain name
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain
    except Exception as e:
        logger.error(f"Error extracting domain from {url}: {str(e)}")
        return None

def check_url_accessibility(url, timeout=5):
    """
    Check if a URL is accessible.

    Args:
        url (str): URL to check
        timeout (int): Request timeout in seconds

    Returns:
        bool: True if URL is accessible, False otherwise
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except requests.RequestException:
        return False

def extract_main_image(html_content, base_url):
    """
    Extract the main image from HTML content.

    Args:
        html_content (str): HTML content
        base_url (str): Base URL for resolving relative paths

    Returns:
        str: URL of the main image
    """
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, 'html.parser')

    # Try to find meta og:image first
    og_image = soup.find('meta', property='og:image')
    if og_image and 'content' in og_image.attrs:
        return og_image['content']

    # Try to find Twitter image
    twitter_image = soup.find('meta', {'name': 'twitter:image'})
    if twitter_image and 'content' in twitter_image.attrs:
        return twitter_image['content']

    # Look for large images in the content
    images = soup.find_all('img')

    # Filter and sort images by dimensions, if available
    valid_images = []
    for img in images:
        # Skip small or irrelevant images
        if 'src' not in img.attrs:
            continue

        # Skip icons, spacers, etc.
        src = img['src']
        if not src or any(x in src.lower() for x in ['icon', 'logo', 'spacer', 'advertisement']):
            continue

        # Try to get dimensions
        width = img.get('width', '0')
        height = img.get('height', '0')

        try:
            width = int(width)
            height = int(height)
            area = width * height
        except (ValueError, TypeError):
            area = 0

        valid_images.append((img['src'], area))

    # Sort by area (descending)
    valid_images.sort(key=lambda x: x[1], reverse=True)

    if valid_images:
        return valid_images[0][0]

    return None

def summarize_text(text, max_sentences=5):
    """
    Generate a simple extractive summary of text.
    This is a basic implementation - in production, more sophisticated
    approaches like transformer-based summarization would be used.

    Args:
        text (str): Text to summarize
        max_sentences (int): Maximum number of sentences in summary

    Returns:
        str: Summary text
    """
    import nltk
    from nltk.tokenize import sent_tokenize
    from nltk.corpus import stopwords

    try:
        nltk.data.find('punkt')
    except LookupError:
        nltk.download('punkt')

    try:
        nltk.data.find('stopwords')
    except LookupError:
        nltk.download('stopwords')

    # Tokenize text into sentences
    sentences = sent_tokenize(text)

    # If text is already short, return as is
    if len(sentences) <= max_sentences:
        return text

    # Get stopwords
    stop_words = set(stopwords.words('english'))

    # Calculate word frequency (excluding stopwords)
    word_freq = {}
    for sentence in sentences:
        for word in nltk.word_tokenize(sentence.lower()):
            if word not in stop_words and word.isalnum():
                if word in word_freq:
                    word_freq[word] += 1
                else:
                    word_freq[word] = 1

    # Calculate sentence scores based on word frequency
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        score = 0
        for word in nltk.word_tokenize(sentence.lower()):
            if word in word_freq:
                score += word_freq[word]
        sentence_scores[i] = score

    # Get the top sentences
    top_sentence_indices = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
    top_sentence_indices = sorted([idx for idx, _ in top_sentence_indices])

    # Create summary
    summary_sentences = [sentences[i] for i in top_sentence_indices]
    summary = ' '.join(summary_sentences)

    return summary


# --- Reliability Scoring ---

def compute_source_reliability(source):
    """Compute a 0..100 reliability score for a NewsSource based on related article analyses.
    Factors:
      - Fact-check ratings (weighted by confidence) → 60%
      - Bias consistency (lower stdev of bias_score is better) → 20%
      - Logical fallacy frequency (fewer per article is better) → 20%
    """
    try:
        from news_analysis.models import FactCheckResult, BiasAnalysis, LogicalFallacyDetection
        from django.db.models import Avg, Count
        import statistics

        articles = list(source.articles.all())
        if not articles:
            return 0.0
        article_ids = [a.id for a in articles]

        # Fact-check score
        fc_qs = FactCheckResult.objects.filter(article_id__in=article_ids)
        rating_weight = {
            'true': 1.0,
            'mostly_true': 0.85,
            'half_true': 0.6,
            'mostly_false': 0.25,
            'false': 0.0,
            'pants_on_fire': 0.0,
            'unverified': 0.5,
        }
        fc_scores = []
        for fc in fc_qs.iterator():
            base = rating_weight.get(fc.rating, 0.5)
            conf = fc.confidence if (fc.confidence is not None) else 0.7
            fc_scores.append(base * conf + base * (1 - conf))  # keep base; weight is gentle
        fact_part = (sum(fc_scores) / len(fc_scores) * 100.0) if fc_scores else 50.0

        # Bias consistency: lower stdev => higher score
        bias_scores = list(BiasAnalysis.objects.filter(article_id__in=article_ids).values_list('bias_score', flat=True))
        if len(bias_scores) >= 2:
            sigma = statistics.pstdev(bias_scores)
            sigma = min(max(sigma, 0.0), 1.0)
            bias_consistency = (1.0 - sigma) * 100.0
        elif len(bias_scores) == 1:
            bias_consistency = 85.0
        else:
            bias_consistency = 60.0

        # Fallacy penalty: avg fallacies per article, max penalty 20 at >=3/article
        fallacy_count = LogicalFallacyDetection.objects.filter(article_id__in=article_ids).count()
        avg_fallacies = fallacy_count / max(len(articles), 1)
        fallacy_penalty = min(avg_fallacies / 3.0, 1.0) * 20.0
        fallacy_component = max(0.0, 100.0 - fallacy_penalty)

        # Weighted aggregate
        score = 0.6 * fact_part + 0.2 * bias_consistency + 0.2 * fallacy_component
        return max(0.0, min(100.0, score))
    except Exception:
        return float(source.reliability_score or 0.0)


def update_source_reliability(source):
    """Compute and persist reliability score for a source."""
    score = compute_source_reliability(source)
    # Avoid unnecessary writes
    if abs((source.reliability_score or 0.0) - score) >= 1e-6:
        source.reliability_score = score
        source.save(update_fields=['reliability_score'])
    return score
