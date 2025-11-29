# Article Validation System

## Overview

The article validation system is designed to filter and scrape only valid news articles while excluding non-article pages such as category pages, author pages, tag pages, homepage, and navigation pages.

## Features

### 1. **URL Pattern Validation**
The system validates URLs to ensure they point to actual articles rather than index or listing pages.

**Rejected URL Patterns:**
- Category pages: `/category/`, `/categories/`
- Tag pages: `/tag/`, `/tags/`
- Author pages: `/author/`, `/authors/`
- Search pages: `/search`
- Archive pages: `/archive/`, `/archives/`
- Pagination: `/page/`
- Utility pages: `/about`, `/contact`, `/privacy`, `/terms`
- Index pages: `/`, `/index.html`, `/home`, `/latest`, `/trending`
- Query parameters: `?page=`, `?search=`, `?category=`, `?tag=`

### 2. **Article Metadata Validation**
The system checks for article-specific metadata to verify authenticity:

- **Open Graph Type**: Checks for `og:type="article"`
- **Author Information**: Looks for author metadata or byline elements
- **Publication Date**: Validates presence of publication timestamps
- **Title**: Ensures proper title length (10-300 characters)

### 3. **Content Structure Validation**
Validates the page has proper article structure:

- **Minimum Word Count**: 100 words
- **Minimum Paragraphs**: 2 paragraphs
- **Article Container**: Presence of `<article>` tag or content divs
- **Headline**: H1 tag with article title

### 4. **Multi-Level Validation**
The system employs a three-stage validation process:

1. **URL Pattern Check**: Quick rejection of obvious non-article URLs
2. **Metadata Extraction**: Parses HTML for article-specific metadata
3. **Content Validation**: Analyzes content structure and substance

## Usage

### Command Line

The `fetch_news` management command has been enhanced with article validation:

```bash
# Fetch articles with validation enabled (default)
python manage.py fetch_news

# Fetch from specific source with validation
python manage.py fetch_news --source_id 1

# Fetch limited number of articles
python manage.py fetch_news --limit 20

# Disable validation and scrape all pages
python manage.py fetch_news --scrape-all
```

### Programmatic Usage

```python
from news_aggregator.article_validator import ArticleValidator

# Validate a URL pattern
url = 'https://example.com/news/2024/11/breaking-story'
is_valid_url = ArticleValidator.is_valid_article_url(url)

# Validate complete article (URL + HTML content)
html_content = "<html>...</html>"
is_valid, details = ArticleValidator.is_valid_article(url, html_content)

if is_valid:
    print("Valid article!")
    print(f"Word count: {details['word_count']}")
    print(f"Has metadata: {details['has_metadata']}")
else:
    print(f"Invalid: {details['reason']}")
```

## Configuration

You can customize validation thresholds in `news_aggregator/article_validator.py`:

```python
class ArticleValidator:
    MIN_ARTICLE_WORD_COUNT = 100  # Minimum words
    MIN_PARAGRAPH_COUNT = 2       # Minimum paragraphs
    MIN_TITLE_LENGTH = 10         # Minimum title length
    MAX_TITLE_LENGTH = 300        # Maximum title length
```

## Validation Details

### Valid Article Example

```html
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
        <p>Article content with substantial information...</p>
        <p>More paragraphs with meaningful content...</p>
    </article>
</body>
</html>
```

**Validation Result**: ✅ **VALID**
- Has article metadata (og:type)
- Has author information
- Has publication date
- Has proper title
- Has sufficient content (>100 words)

### Invalid Examples

#### Example 1: Category Page
```
URL: https://example.com/category/politics
Reason: URL pattern indicates non-article page
```

#### Example 2: Insufficient Content
```html
<html>
<head><title>Short Page</title></head>
<body>
    <h1>Short Page</h1>
    <p>Too short.</p>
</body>
</html>
```
**Validation Result**: ❌ **INVALID**
- Reason: Insufficient content (words: 3, paragraphs: 1)

#### Example 3: Missing Metadata
```html
<html>
<head><title>Some Page</title></head>
<body>
    <h1>Some Page</h1>
    <div>
        <p>Some content here.</p>
        <p>More content.</p>
    </div>
</body>
</html>
```
**Validation Result**: ❌ **INVALID**
- Reason: Missing article metadata (author/date/og:type)

## Statistics and Monitoring

When running the fetch command, you'll see detailed statistics:

```
Processing Example News (https://example.com)
  ✓ Added: Breaking News Story About...
  ✓ Added: Important Update on Current...
  ✗ Error processing article https://example.com/bad-url: Request timeout
Added 15 articles from Example News
  Skipped 5 existing articles
  Skipped 12 non-article pages (validation)
```

## Testing

### Unit Tests

Run the article validator unit tests:

```bash
python -m unittest news_aggregator.tests_article_validator -v
```

### Integration Tests

Run Django integration tests:

```bash
python manage.py test news_aggregator.tests.ArticleValidationTests -v 2
```

### Test Coverage

The test suite covers:
- ✅ Valid article URL patterns
- ✅ Invalid category/tag/author URLs
- ✅ Invalid index/homepage URLs
- ✅ Invalid query parameter URLs
- ✅ Invalid file extensions
- ✅ Metadata extraction from Open Graph tags
- ✅ Valid article structure validation
- ✅ Invalid article with insufficient content
- ✅ Invalid article without metadata
- ✅ Complete end-to-end validation flow
- ✅ Minimum word count thresholds

## Benefits

1. **Improved Data Quality**: Only legitimate news articles are stored
2. **Reduced Noise**: Category pages, navigation pages excluded
3. **Storage Efficiency**: No wasted database space on non-articles
4. **Better Analysis**: ML models work with quality article content
5. **Flexible Control**: `--scrape-all` flag for backward compatibility

## Advanced Features

### Relaxed Validation

If a page lacks explicit metadata but has strong content indicators (≥300 words, ≥3 paragraphs), it may still pass validation.

### Debug Logging

Enable debug logging to see why pages are rejected:

```python
import logging
logging.getLogger('news_aggregator.article_validator').setLevel(logging.DEBUG)
```

Output:
```
DEBUG: URL rejected (category pattern): https://example.com/category/tech
DEBUG: URL rejected (query params): https://example.com/news?page=2
```

## Future Enhancements

Potential improvements for future versions:

1. **Machine Learning Classification**: Train an ML model to identify article vs. non-article pages
2. **Site-Specific Rules**: Customizable validation rules per news source
3. **Content Quality Scoring**: Rank articles by content quality
4. **Language Detection**: Validate language-specific patterns
5. **Image Validation**: Ensure featured images are present and valid

## Troubleshooting

### Issue: Too many articles rejected

**Solution**: Check if your news source uses non-standard URL patterns. You may need to adjust the URL pattern filters or use `--scrape-all` mode.

### Issue: Valid articles being rejected

**Solution**: Review validation logs and adjust minimum thresholds (word count, paragraph count) if needed for your specific news sources.

### Issue: Category pages being scraped

**Solution**: Ensure validation is enabled (don't use `--scrape-all`) and check that URL patterns match your site structure.

## API Reference

### `ArticleValidator.is_valid_article_url(url)`
Check if URL pattern suggests it's an article.

**Parameters:**
- `url` (str): Article URL to validate

**Returns:**
- `bool`: True if URL pattern is valid for an article

### `ArticleValidator.extract_metadata(soup)`
Extract article metadata from BeautifulSoup object.

**Parameters:**
- `soup` (BeautifulSoup): Parsed HTML

**Returns:**
- `dict`: Metadata including author, publish_date, title, description, og_type

### `ArticleValidator.validate_article_structure(soup)`
Validate that the page has proper article structure.

**Parameters:**
- `soup` (BeautifulSoup): Parsed HTML

**Returns:**
- `dict`: Validation results with 'is_valid' boolean and details

### `ArticleValidator.is_valid_article(url, html_content)`
Main validation method to determine if a page is a valid news article.

**Parameters:**
- `url` (str): Article URL
- `html_content` (str): HTML content of the page

**Returns:**
- `tuple`: (is_valid: bool, validation_details: dict)

## License

This feature is part of the News Advance project and follows the same license terms.
