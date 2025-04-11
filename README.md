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
- **NLP/AI**: NLTK, spaCy, scikit-learn, Transformers
- **Frontend**: Bootstrap 5, HTML/CSS, JavaScript
- **Data Gathering**: Newspaper3k, Requests, BeautifulSoup4

## Project Structure

The project is organized into the following Django apps:

- **news_aggregator**: Handles news article collection and storage
- **news_analysis**: Performs AI analysis of news content
- **accounts**: Manages user authentication and preferences

## Setup & Installation

### Prerequisites

- Python 3.8+
- pip

### Installation Steps

1. Clone the repository
   ```
   git clone <repository-url>
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

5. Run migrations
   ```
   python manage.py migrate
   ```

6. Create a superuser (for admin access)
   ```
   python manage.py createsuperuser
   ```

7. Start the development server
   ```
   python manage.py runserver
   ```

8. Access the site at http://127.0.0.1:8000

## Running the Project

After installation, you can run the project using:

```
python manage.py runserver
```

Access the admin interface at http://127.0.0.1:8000/admin to add news sources and articles.

## Features

- User authentication and profile management
- News aggregation from various sources
- AI analysis of news articles for bias and sentiment
- Fact-checking of claims in articles
- Misinformation tracking and alerts
- User preferences for personalized news experience

## License

This project is licensed under the MIT License.
