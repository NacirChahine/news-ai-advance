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
