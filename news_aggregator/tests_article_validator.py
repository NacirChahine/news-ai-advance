"""
Tests for article validation functionality.
"""

import unittest
from news_aggregator.article_validator import ArticleValidator


class TestArticleValidator(unittest.TestCase):
    """Test cases for ArticleValidator class"""

    def test_valid_article_urls(self):
        """Test that valid article URLs pass validation"""
        valid_urls = [
            'https://example.com/news/2024/11/breaking-news-story',
            'https://example.com/article/important-update',
            'https://example.com/2024/11/29/news-headline',
            'https://example.com/politics/election-results',
            'https://example.com/world/international-summit',
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(
                    ArticleValidator.is_valid_article_url(url),
                    f"Expected {url} to be valid"
                )

    def test_invalid_category_urls(self):
        """Test that category pages are rejected"""
        invalid_urls = [
            'https://example.com/category/politics',
            'https://example.com/categories/world',
            'https://example.com/tag/breaking-news',
            'https://example.com/tags/economy',
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(
                    ArticleValidator.is_valid_article_url(url),
                    f"Expected {url} to be invalid (category/tag page)"
                )

    def test_invalid_author_urls(self):
        """Test that author pages are rejected"""
        invalid_urls = [
            'https://example.com/author/john-doe',
            'https://example.com/authors/jane-smith',
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(
                    ArticleValidator.is_valid_article_url(url),
                    f"Expected {url} to be invalid (author page)"
                )

    def test_invalid_index_urls(self):
        """Test that index/homepage URLs are rejected"""
        invalid_urls = [
            'https://example.com/',
            'https://example.com/index.html',
            'https://example.com/home.php',
            'https://example.com/latest',
            'https://example.com/trending',
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(
                    ArticleValidator.is_valid_article_url(url),
                    f"Expected {url} to be invalid (index page)"
                )

    def test_invalid_query_param_urls(self):
        """Test that URLs with search/filter query params are rejected"""
        invalid_urls = [
            'https://example.com/news?page=2',
            'https://example.com/articles?search=covid',
            'https://example.com/news?category=politics',
            'https://example.com/stories?tag=breaking',
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(
                    ArticleValidator.is_valid_article_url(url),
                    f"Expected {url} to be invalid (query params)"
                )

    def test_invalid_file_extensions(self):
        """Test that non-HTML file URLs are rejected"""
        invalid_urls = [
            'https://example.com/document.pdf',
            'https://example.com/image.jpg',
            'https://example.com/photo.png',
            'https://example.com/archive.zip',
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(
                    ArticleValidator.is_valid_article_url(url),
                    f"Expected {url} to be invalid (file extension)"
                )

    def test_extract_metadata_with_og_tags(self):
        """Test metadata extraction from Open Graph tags"""
        html = """
        <html>
        <head>
            <meta property="og:type" content="article">
            <meta property="og:title" content="Breaking News Story">
            <meta property="article:author" content="John Doe">
            <meta property="article:published_time" content="2024-11-29T10:00:00Z">
        </head>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        metadata = ArticleValidator.extract_metadata(soup)
        
        self.assertEqual(metadata['og_type'], 'article')
        self.assertEqual(metadata['title'], 'Breaking News Story')
        self.assertEqual(metadata['author'], 'John Doe')
        self.assertEqual(metadata['publish_date'], '2024-11-29T10:00:00Z')

    def test_validate_valid_article_structure(self):
        """Test validation of a properly structured article"""
        html = """
        <html>
        <head>
            <title>Breaking News: Important Update</title>
            <meta property="og:type" content="article">
            <meta property="article:author" content="Jane Smith">
            <meta property="article:published_time" content="2024-11-29T10:00:00Z">
        </head>
        <body>
            <article>
                <h1>Breaking News: Important Update</h1>
                <div class="author">By Jane Smith</div>
                <time datetime="2024-11-29">November 29, 2024</time>
                <p>This is the first paragraph of the article with substantial content that provides important information to the readers. In today's fast-paced world, staying informed about current events is more crucial than ever.</p>
                <p>This is the second paragraph continuing the story with more details and context about the breaking news event. Experts from various fields have weighed in on the significance of this development and its potential impact on society.</p>
                <p>This is the third paragraph providing additional analysis and expert opinions on the matter. The implications of this news story extend far beyond what was initially anticipated by most observers and analysts.</p>
                <p>This is the fourth paragraph with concluding remarks and future implications of the news story. As we move forward, it will be important to monitor how this situation develops and what actions stakeholders will take in response.</p>
            </article>
        </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        validation = ArticleValidator.validate_article_structure(soup)
        
        self.assertTrue(validation['is_valid'])
        self.assertTrue(validation['has_title'])
        self.assertTrue(validation['has_content'])
        self.assertTrue(validation['has_metadata'])
        self.assertTrue(validation['has_author'])
        self.assertTrue(validation['has_date'])
        self.assertGreater(validation['word_count'], ArticleValidator.MIN_ARTICLE_WORD_COUNT)
        self.assertGreater(validation['paragraph_count'], ArticleValidator.MIN_PARAGRAPH_COUNT)

    def test_validate_invalid_article_no_content(self):
        """Test validation rejects page without substantial content"""
        html = """
        <html>
        <head>
            <title>Category: Politics</title>
        </head>
        <body>
            <h1>Politics Category</h1>
            <p>Browse our politics articles.</p>
            <ul>
                <li><a href="/article1">Article 1</a></li>
                <li><a href="/article2">Article 2</a></li>
            </ul>
        </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        validation = ArticleValidator.validate_article_structure(soup)
        
        self.assertFalse(validation['is_valid'])
        self.assertLess(validation['word_count'], ArticleValidator.MIN_ARTICLE_WORD_COUNT)

    def test_validate_invalid_article_no_metadata(self):
        """Test validation rejects page without article metadata"""
        html = """
        <html>
        <head>
            <title>Some Page Title</title>
        </head>
        <body>
            <h1>Some Page Title</h1>
            <div class="content">
                <p>This page has some content but lacks article-specific metadata like author and publish date.</p>
                <p>It might be a static page or informational content rather than a news article.</p>
            </div>
        </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        validation = ArticleValidator.validate_article_structure(soup)
        
        # Should be invalid due to lack of metadata and insufficient content
        self.assertFalse(validation['is_valid'])
        self.assertFalse(validation['has_metadata'])

    def test_is_valid_article_complete(self):
        """Test complete article validation with URL and HTML"""
        url = 'https://example.com/news/2024/11/breaking-story'
        html = """
        <html>
        <head>
            <title>Breaking News: Major Development</title>
            <meta property="og:type" content="article">
            <meta property="article:author" content="Reporter Name">
            <meta property="article:published_time" content="2024-11-29T10:00:00Z">
        </head>
        <body>
            <article>
                <h1>Breaking News: Major Development</h1>
                <div class="author">By Reporter Name</div>
                <time datetime="2024-11-29">November 29, 2024</time>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. This represents a significant development in the ongoing situation.</p>
                <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Industry experts have been monitoring this closely for several weeks now.</p>
                <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. The implications of this development are expected to be far-reaching across multiple sectors.</p>
                <p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Stakeholders are preparing their responses and developing comprehensive action plans.</p>
            </article>
        </body>
        </html>
        """
        
        is_valid, details = ArticleValidator.is_valid_article(url, html)
        
        self.assertTrue(is_valid)
        self.assertTrue(details['has_title'])
        self.assertTrue(details['has_content'])
        self.assertTrue(details['has_metadata'])

    def test_is_valid_article_invalid_url(self):
        """Test that invalid URL pattern fails validation immediately"""
        url = 'https://example.com/category/politics'
        html = '<html><body><h1>Category Page</h1></body></html>'
        
        is_valid, details = ArticleValidator.is_valid_article(url, html)
        
        self.assertFalse(is_valid)
        self.assertIn('URL pattern', details['reason'])

    def test_minimum_word_count_threshold(self):
        """Test that articles below minimum word count are rejected"""
        html = """
        <html>
        <head>
            <title>Short Article</title>
            <meta property="og:type" content="article">
        </head>
        <body>
            <article>
                <h1>Short Article</h1>
                <p>Too short.</p>
            </article>
        </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        validation = ArticleValidator.validate_article_structure(soup)
        
        self.assertFalse(validation['is_valid'])
        self.assertLess(validation['word_count'], ArticleValidator.MIN_ARTICLE_WORD_COUNT)


if __name__ == '__main__':
    unittest.main()
