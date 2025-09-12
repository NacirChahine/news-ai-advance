<!-- 🔄 Synced with AI_PROJECT_DOCS.md → Keep parity for AI/human consistency. -->
# News Advance

An AI-powered news credibility analyzer built with Django.

## Project Overview

News Advance is a web application that aggregates news articles and applies AI-driven analysis tools to assess their credibility. The system includes:

- **Bias & Sentiment Analysis** – Detects political and emotional bias in news articles
- **AI-Powered Summarization & Fact-Checking** – Generates concise summaries and verifies key claims
- **Real-Time Misinformation Tracker** – Flags potentially misleading trending news

- **Logical Fallacy Reference & Detection** – Catalog of logical fallacies with admin management and per-article detections with AI integration

## Tech Stack

- **Backend**: Django 5.2
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **NLP/AI**: NLTK, spaCy, Transformers, PyTorch, Ollama (local LLMs)
- **Frontend**: Bootstrap 5, HTML/CSS, JavaScript
- **Data Gathering**: Newspaper3k, Requests, BeautifulSoup4

## Project Structure

The project is organized into the following Django apps:

- **news_aggregator**: Handles news article collection and storage
- **news_analysis**: Performs AI analysis of news content (bias detection, sentiment analysis, ML summarization)
- **accounts**: Manages user authentication, saved articles, and user preferences

## Setup & Installation

### Prerequisites

- Python 3.8+
- pip
- spaCy english model: `python -m spacy download en_core_web_sm`

### Installation Steps

1. Clone the repository
   ```bash
   git clone https://github.com/NacirChahine/news-ai-advance.git
   cd newsAdvance
   ```

2. Set up a virtual environment
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables
   ```bash
   # The .env file is already configured with working email settings
   # You can modify it if needed for your specific configuration
   # For new setups, you can copy from the template:
   # cp .env.example .env
   ```

6. Download NLP (Natural Language Processing) resources
   ```bash
   python -m nltk.downloader vader_lexicon punkt stopwords
   python -m spacy download en_core_web_sm
   ```

7. Run migrations
   ```bash
   python manage.py migrate
   ```

8. Create a superuser (for admin access)
   ```bash
   python manage.py createsuperuser
   ```

9. Start the development server
   ```bash
   python manage.py runserver
   ```

10. Access the site at http://127.0.0.1:8000

## Running the Project

After installation, you can run the project using:

```bash
python manage.py runserver
```

### Generating Test Data

To populate the site with test data for development purposes:

```bash
python manage.py generate_test_data --sources 10 --articles 30 --users 5
```

### News Fetching

To fetch news articles from configured sources:

```bash
python manage.py fetch_news
```

### Analyzing Articles

To analyze articles for bias, sentiment, and generate summaries:

1. **Add an Article via Admin Panel**
   - Go to the admin panel at `/admin/`
   - Log in with your admin credentials
   - Navigate to "News articles" under the "News_aggregator" section
   - Click "Add News article" and fill in the required fields
   - Make sure to leave `is_analyzed` unchecked
   - Save the article

2. **Run the Analysis Command**
   ```bash
   python manage.py analyze_articles
   ```

   Options:
   ```bash
   # To analyze a specific article by ID
   python manage.py analyze_articles --article_id 123

   # To limit the number of articles processed
   python manage.py analyze_articles --limit 10

   # To force reanalysis of previously analyzed articles
   python manage.py analyze_articles --force

   # To choose an AI model for analysis (requires Ollama)
   python manage.py analyze_articles --model llama3
   python manage.py analyze_articles --model qwen2:1.5b
   python manage.py analyze_articles --model deepseek-r1:8b
   ```

3. **Verify the Results**
   - Return to the admin panel
   - Check that your article now has `is_analyzed` set to True
   - Navigate to "Bias analyses" and "Sentiment analyses" under the "News_analysis" section
   - You should see entries for your article with the analysis results

#### Using Test Data Generator

For testing with multiple articles at once:

```bash
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
- Logical fallacy reference and detection (catalog + admin + per-article detections with user toggle and public reference page)

- Advanced AI analysis using local LLMs via Ollama integration

#### Logical Fallacies
- Public reference page: visit `/analysis/fallacies/` for the catalog (name, description, example, detection counts)
- User preference: Accounts → Preferences → "Enable Logical Fallacy Analysis" controls visibility on article pages
- Article pages:
  - Article Detail: shows detected fallacies when enabled (with confidence and evidence excerpt)
  - Analysis View: includes a "Logical Fallacies" card listing detections and a link to the reference page
- Pipeline: `analyze_articles` runs fallacy detection with Ollama when available; unknown labels are skipped unless added to the catalog (Admin > News Analysis > Logical fallacies)


### User System
  - User authentication and profile management
  - Personalized news preferences
  - Saved articles with notes

### Misinformation Tracking
  - **Models & Infrastructure**: Complete database models for alerts and fact-checking
  - **Manual Fact-Checking**: Admin interface for creating fact-check results
  - **Source Reliability**: Basic reliability scoring system
  - **Automated Detection**: *In development* - Real-time misinformation detection pipeline


### Misinformation Alerts (Manual Management and Email Notifications)

- Manage alerts in Django Admin: Admin > News Analysis > Misinformation alerts
  - Actions: Mark resolved, Mark active, Send alert email to opted-in users
  - Link related articles via the ManyToMany field on the alert

- Send email notifications to users who enabled alerts in their preferences:
  - From Admin: select alert(s) > action "Send alert email to opted-in users"
  - From CLI:
    ```bash
    python manage.py send_misinformation_alerts --active-only --since 2025-01-01
    python manage.py send_misinformation_alerts --alert-id 123
    python manage.py send_misinformation_alerts --dry-run --since 2025-01-01
    ```

- Article analysis integration
  - During analyze_articles, the system matches articles to active alerts using keyword overlap and links them (no new alerts are created automatically)
  - Article Analysis page shows a "Misinformation Alerts" card when related active alerts exist
  - AI summary prompts can include a brief list of related alerts as context (non-breaking)


## Fact-Checking

- Fact-check results are displayed on the article detail page in a dedicated accordion.
- Automated pipeline:
  - Claim extraction: up to 3–5 verifiable claims are extracted from article content using NLP heuristics (entities, numbers, quotes, reporting verbs).
  - LLM verification: Each claim is verified via Ollama, producing a rating (true/mostly_true/half_true/mostly_false/false/pants_on_fire/unverified), an explanation, sources, and a confidence score. Rate-limited to avoid API saturation.
  - Stored fields now include confidence and last_verified timestamps. The UI shows ratings and explanations; sources are listed when provided.
- Users can control visibility:
  - Go to Accounts > Preferences and toggle “Enable Fact-Checking”.
  - If disabled, the article page shows a hint with a link back to Preferences to enable it.
- For visitors who aren’t logged in, the article page shows a helpful prompt with links to sign up or log in to access fact-checks.

CLI tips:

```bash
# Analyze one article (extract + verify claims)
python manage.py analyze_articles --article_id <ID> --force

# Periodically re-verify older fact checks
python manage.py reverify_fact_checks --older-than-days 14 --limit 50
```

Configuration:
- Set OLLAMA_ENDPOINT (default http://localhost:11434/api/generate) if needed.
- Ensure an Ollama model (default: llama3) is available locally.

## ML-Powered News Summarization

News Advance includes a fine-tuned BART model specifically trained on the BBC News Summary dataset for high-quality article summarization. This provides more accurate and consistent summaries compared to general-purpose models.

### Features

- **High-Quality Summaries**: Trained on professional news writing from BBC dataset
- **Fast Inference**: Optimized for quick summarization
- **Configurable Length**: Control summary length and detail level
- **Seamless Fallback**: Automatically falls back to Ollama if the ML model isn't available

### Training the Model

To train your own summarization model:

1. Install the required dependencies:
   ```bash
   cd news_analysis/ml_models
   pip install -r requirements.txt
   ```

2. Run the training script:
   ```bash
   cd summarization
   train_model.bat  # On Windows
   # OR
   python train_summarization_model.py --model_name facebook/bart-base --output_dir ./trained_model
   ```

3. Training parameters (adjust in `train_model.bat` or pass as arguments):
   - `--model_name`: Base model (default: facebook/bart-base)
   - `--output_dir`: Where to save the trained model
   - `--num_train_epochs`: Training epochs (default: 3)
   - `--batch_size`: Batch size (default: 4)
   - `--learning_rate`: Learning rate (default: 5e-5)
   - `--max_input_length`: Max input tokens (default: 1024)
   - `--max_target_length`: Max summary tokens (default: 128)

### Using the ML Summarizer

The ML-based summarizer is automatically used when available. You can control its behavior in `news_advance/settings.py`:

```python
# ML Models Configuration
SUMMARIZATION_MODEL_DIR = BASE_DIR / 'news_analysis' / 'ml_models' / 'summarization' / 'trained_model'
SUMMARIZATION_BASE_MODEL = 'facebook/bart-base'  # Fallback if trained model not available
USE_ML_SUMMARIZATION = True  # Set to False to always use Ollama instead
```

### Performance

The model is evaluated using ROUGE metrics:
- ROUGE-1: ~40-45%
- ROUGE-2: ~20-25%
- ROUGE-L: ~35-40%

## Ollama Integration

News Advance supports integration with [Ollama](https://ollama.ai/) for advanced AI analysis using local large language models (LLMs). This integration provides:

- Enhanced article summarization (fallback when ML model not used)
- More nuanced sentiment analysis
- Advanced political bias detection
- Key insights extraction from articles

### Setting Up Ollama

1. Install Ollama from [https://ollama.ai/download](https://ollama.ai/download)
2. Download recommended models:
   ```bash
   ollama pull llama3
   ollama pull mistral
   ollama pull phi
   ```
3. Start the Ollama service

For detailed instructions on setting up and using Ollama with News Advance, see the [OLLAMA_INTEGRATION.md](OLLAMA_INTEGRATION.md) documentation.

## Configuration

### Environment Variables

The project includes a pre-configured `.env` file with working email settings. For production or custom setups, you can modify the values as needed:

```env
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Ollama Configuration
OLLAMA_ENDPOINT=http://localhost:11434/api/generate

# ML Models Configuration
USE_ML_SUMMARIZATION=True
```

**Security Note**: The `.env` file is excluded from version control to protect sensitive credentials. Use `.env.example` as a template for new setups.

### Django Settings

Key configuration options in `news_advance/settings.py`:

```python
# Ollama Configuration
OLLAMA_ENDPOINT = 'http://localhost:11434/api/generate'

# ML Models Configuration
SUMMARIZATION_MODEL_DIR = BASE_DIR / 'news_analysis' / 'ml_models' / 'summarization' / 'trained_model'
SUMMARIZATION_BASE_MODEL = 'facebook/bart-base'
USE_ML_SUMMARIZATION = True
```

## Documentation

- [AI_PROJECT_DOCS.md](AI_PROJECT_DOCS.md) - Detailed technical documentation for AI context
- [OLLAMA_INTEGRATION.md](OLLAMA_INTEGRATION.md) - Complete guide for Ollama setup and usage
- [ML_SUMMARIZATION.md](ML_SUMMARIZATION.md) - Documentation for the custom-trained summarization model

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please open an issue on GitHub or contact the development team.
