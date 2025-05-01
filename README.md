<!-- 🔄 Synced with AI_PROJECT_DOCS.md → Keep parity for AI/human consistency. -->  
# News Advance

An AI-powered news credibility analyzer built with Django.

## Project Overview

News Advance is a web application that aggregates news articles and applies AI-driven analysis tools to assess their credibility. The system includes:

- **Bias & Sentiment Analysis** – Detects political and emotional bias in news articles
- **AI-Powered Summarization & Fact-Checking** – Generates concise summaries and verifies key claims
- **Real-Time Misinformation Tracker** – Flags potentially misleading trending news

## Tech Stack

- **Backend**: Django 5.2
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **NLP/AI**: NLTK, spaCy, scikit-learn, Transformers, Ollama (local LLMs)
- **Frontend**: Bootstrap 5, HTML/CSS, JavaScript
- **Data Gathering**: Newspaper3k, Requests, BeautifulSoup4

## Project Structure

The project is organized into the following Django apps:

- **news_aggregator**: Handles news article collection and storage
- **news_analysis**: Performs AI analysis of news content (bias detection, sentiment analysis)
- **accounts**: Manages user authentication, saved articles, and user preferences

## Setup & Installation

### Prerequisites

- Python 3.8+
- pip
- spaCy english model: `python -m spacy download en_core_web_sm`

### Installation Steps

1. Clone the repository
   ```
   git clone https://github.com/NacirChahine/news-advance.git
   cd newsAdvance
   ```

2. Set up a virtual environment
   ```
   python -m venv venv
   ```

3. Activate the virtual environment
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies
   ```
   pip install -r requirements.txt
   ```

5. Download NLP (Natural Language Processing) resources
   ```
   python -m nltk.downloader vader_lexicon punkt stopwords
   python -m spacy download en_core_web_sm
   ```

6. Run migrations
   ```
   python manage.py migrate
   ```

7. Create a superuser (for admin access)
   ```
   python manage.py createsuperuser
   ```

8. Start the development server
   ```
   python manage.py runserver
   ```

9. Access the site at http://127.0.0.1:8000

## Running the Project

After installation, you can run the project using:

```
python manage.py runserver
```

### Generating Test Data

To populate the site with test data for development purposes:

```
python manage.py generate_test_data --sources 10 --articles 30 --users 5
```

### News Fetching

To fetch news articles from configured sources:

```
python manage.py fetch_news
```

### Analyzing Articles

To add and analyze articles for bias and sentiment:

1. **Add an Article via Admin Panel**
   - Go to the admin panel at `/admin/`
   - Log in with your admin credentials
   - Navigate to "News articles" under the "News_aggregator" section
   - Click "Add News article" and fill in the required fields
   - Make sure to leave `is_analyzed` unchecked
   - Save the article

2. **Run the Analysis Command**
   ```
   python manage.py analyze_articles
   ```

   Options:
   ```
   # To analyze a specific article by ID
   python manage.py analyze_articles --article_id 123

   # To limit the number of articles processed
   python manage.py analyze_articles --limit 10

   # To force reanalysis of previously analyzed articles
   python manage.py analyze_articles --force
   
   # To chose an AI model for analysis
   python manage.py analyze_articles --model llama3
   python manage.py analyze_articles --model qwen3:1.7b
   python manage.py analyze_articles --model deepseek-r1:8b
   ```

3. **Verify the Results**
   - Return to the admin panel
   - Check that your article now has `is_analyzed` set to True
   - Navigate to "Bias analyses" and "Sentiment analyses" under the "News_analysis" section
   - You should see entries for your article with the analysis results

#### Using Test Data Generator

For testing with multiple articles at once:

```
python manage.py generate_test_data --sources 5 --articles 10 --users 2
```

This will create:
- 5 news sources
- 10 articles per source (50 total)
- 2 test users
- Analysis data for most articles


## Features

### News Aggregation
- Collection and storage of news articles from multiple sources
- Source credibility ratings and filtering
- Personalized news feed based on topics of interest
- Save articles to your personal collection with notes

### News Analysis
- Political bias detection and visualization using advanced NLP techniques
- Sentiment analysis to detect emotional tone (positive, negative, neutral)
- Named entity recognition and extraction
- Readability scoring and complexity analysis
- Visual indicators for source reliability and content bias
- Advanced AI analysis using local LLMs via Ollama integration

### User System
  - User authentication and profile management
  - Personalized news preferences
  - Saved articles with notes

### Misinformation Tracking
  - Real-time alerts for misleading content
  - Fact-checking of claims
  - Source reliability scoring

## Ollama Integration

News Advance now supports integration with [Ollama](https://ollama.ai/) for advanced AI analysis using local large language models (LLMs). This integration provides:

- Enhanced article summarization
- More nuanced sentiment analysis
- Advanced political bias detection
- Key insights extraction from articles

### Setting Up Ollama

1. Install Ollama from [https://ollama.ai/download](https://ollama.ai/download)
2. Download recommended models (e.g., `ollama pull llama3`)
3. Start the Ollama service

For detailed instructions on setting up and using Ollama with News Advance, see the [OLLAMA_INTEGRATION.md](OLLAMA_INTEGRATION.md) documentation.
