<!-- 🔄 Synced with README.md → Maintain human-readable summaries here.  
**AI NOTE**: This file contains extended technical context for the AI. -->

# News Advance: Technical Documentation

An AI-powered news credibility analyzer built with Django. This document provides detailed technical information for AI context.

## Project Architecture

The News Advance system is built on Django 5.2 with a modular architecture organized into specialized apps:

- **news_aggregator**: News collection, storage, and management
- **news_analysis**: AI analysis pipelines and algorithms (bias detection, sentiment analysis)
- **accounts**: User authentication, profiles, saved articles, and preference management

## Data Models

### News Aggregator Models

- **NewsSource**: Represents news publishers with reliability metrics
  - Fields: name, url, description, reliability_score
  - Relationships: one-to-many with NewsArticle

- **NewsArticle**: Core content model for news articles
  - Fields: title, content, author, published_date, url, summary, image_url, is_analyzed, is_summarized
  - Relationships: many-to-one with NewsSource, one-to-one with analysis models

- **UserSavedArticle**: Tracks user-saved articles with notes
  - Fields: user, article, saved_at, notes
  - Relationships: many-to-one with User and NewsArticle

### News Analysis Models

- **BiasAnalysis**: Political bias detection results
  - Fields: article, political_leaning, bias_score, confidence
  - Choices: left, center-left, center, center-right, right

- **SentimentAnalysis**: Emotional tone analysis
  - Fields: article, sentiment_score, positive_score, negative_score, neutral_score

- **FactCheckResult**: Fact-checking of specific claims
  - Fields: article, claim, rating, explanation, sources
  - Choices: true, mostly_true, half_true, mostly_false, false, pants_on_fire

- **MisinformationAlert**: System-wide warnings about misinformation trends
  - Fields: title, description, severity, detected_at, is_active, resolution_details, resolved_at, related_articles
  - Choices for severity: low, medium, high, critical

### Accounts Models

- **UserProfile**: Extended user information
  - Fields: user, bio, avatar, preferred_sources
  - Relationships: one-to-one with User, many-to-many with NewsSource

- **UserPreferences**: User-specific settings for content filtering
  - Fields: user, political_filter, show_politics, show_business, show_tech, show_health, show_entertainment, email_newsletter, etc.
  - Relationships: one-to-one with User

## Processing Pipelines

### News Collection Pipeline

1. **Source Management**: Database of reliable and diverse news sources
2. **Article Fetching**: Using newspaper3k for automated content extraction
3. **Preprocessing**: HTML cleaning, content extraction, metadata parsing
4. **Storage**: Persistence of articles with normalized metadata

### Analysis Pipeline

1. **Content Preparation**: Text cleaning and normalization
2. **Bias Analysis**: 
   - Model-based political leaning detection
   - Language pattern analysis for bias indicators
3. **Sentiment Analysis**: 
   - VADER sentiment scoring
   - Emotional tone classification
4. **Fact Checking**: 
   - Claim extraction
   - Verification against trusted sources
5. **Source Credibility**: Historical accuracy rating of publishers

## Utility Modules

### News Aggregator Utilities (news_aggregator/utils.py)

- **clean_html(html_content)**: Removes scripts, styles, and unwanted HTML elements
- **extract_article_content(url, timeout)**: Extracts article content using newspaper3k
- **get_domain_from_url(url)**: Extracts domain name from URL
- **check_url_accessibility(url, timeout)**: Verifies URL is accessible
- **extract_main_image(html_content, base_url)**: Finds the primary image in HTML content
- **summarize_text(text, max_sentences)**: Generates extractive summaries of article content

### News Analysis Utilities (news_analysis/utils.py)

- **analyze_sentiment(text)**: Performs sentiment analysis using VADER
- **extract_named_entities(text, entity_types)**: Identifies named entities using spaCy
- **extract_main_topics(text, top_n)**: Extracts key topics through frequency analysis
- **calculate_readability_score(text)**: Computes readability metrics (Flesch Reading Ease, etc.)

## Management Commands

### Fetch News (news_aggregator/management/commands/fetch_news.py)

- Fetches articles from configured sources using newspaper3k
- Handles rate limiting, error recovery, and duplicate detection
- Implements smart scheduling to prioritize frequently updated sources

### Analyze Articles (news_analysis/management/commands/analyze_articles.py)

- Processes unanalyzed articles through the analysis pipeline
- Generates bias, sentiment, and readability metrics
- Batched processing to handle large article volumes efficiently

### Generate Test Data (news_aggregator/management/commands/generate_test_data.py)

- Creates sample data for development and testing
- Generates sources with varied political leanings
- Produces articles with realistic bias and sentiment distributions
- Simulates user interactions and saved articles

## User Interface

### News Analysis Templates

- **article_analysis.html**: Comprehensive article analysis view with visualization of bias, sentiment, and reliability metrics
- **misinformation_tracker.html**: Real-time dashboard of potentially misleading content
- **alert_detail.html**: Detailed view of individual misinformation alerts

### Accounts Templates

- **profile.html**: User profile with activity summary and preferences
- **preferences.html**: Settings interface for content filtering and notifications
- **saved_articles.html**: Management of user's saved articles collection

## Setup & Installation

### Prerequisites

- Python 3.8+
- pip
- spaCy english model: `python -m spacy download en_core_web_sm`

### Dependencies

- Django 5.2
- newspaper3k
- nltk
- spaCy
- scikit-learn
- transformers (optional for advanced NLP)
- pillow
- requests
- beautifulsoup4
- Faker (for test data generation)

### Installation Process

1. Clone repository
2. Create virtual environment
3. Install dependencies
4. Download NLP resources
   ```
   python -m nltk.downloader vader_lexicon punkt stopwords
   python -m spacy download en_core_web_sm
   ```
5. Run migrations
6. Create superuser
7. Start development server

## Development Commands

### Generate Test Data

```
python manage.py generate_test_data --sources 10 --articles 30 --users 5 --clear
```

Parameters:
- `--sources`: Number of news sources to generate
- `--articles`: Number of articles per source
- `--users`: Number of test users to create
- `--clear`: Whether to clear existing data before generation

### News Fetching

```
python manage.py fetch_news --sources all --limit 10
```

Parameters:
- `--sources`: Source IDs or 'all' for all configured sources
- `--limit`: Maximum articles to fetch per source

### Article Analysis

```
python manage.py analyze_articles --unanalyzed-only --batch-size 20
```

Parameters:
- `--unanalyzed-only`: Process only articles not yet analyzed
- `--batch-size`: Number of articles to process in each batch

## Testing Strategy

- Unit tests for utility functions
- Integration tests for analysis pipelines
- View tests with Django test client
- End-to-end tests with Selenium

## Performance Considerations

- Asynchronous processing for long-running analysis tasks
- Caching layer for frequently accessed analysis results
- Pagination and lazy loading for article listings
- Batch processing for analysis pipelines

## Future Development Plans

1. **Advanced NLP Models**:
   - Fine-tuned BERT models for bias detection
   - Transformer-based summarization

2. **API Development**:
   - RESTful API for third-party integration
   - OAuth2 authentication

3. **Content Expansion**:
   - Video content analysis
   - Social media integration

4. **Performance Optimizations**:
   - Celery for background tasks
   - Redis for caching
   - PostgreSQL full-text search