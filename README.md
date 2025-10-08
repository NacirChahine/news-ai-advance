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


### Health Check

Run environment diagnostics to verify your setup:

```bash
python manage.py health_check
# Verbose mode (shows extra details and hints)
python manage.py health_check --verbose
```

What it checks:
- Python version (supported range 3.8–3.12; recommended 3.11/3.12)
- Virtual environment usage
- Core dependencies: Django, BeautifulSoup4 (`bs4`), `sgmllib` (from `sgmllib3k`), Newspaper3k (`newspaper`), NLTK, spaCy, Transformers
- Database connectivity (simple query)
- NLTK data availability (`punkt`, `vader_lexicon`)
- spaCy English model availability (`en_core_web_sm`)
- Ollama connectivity (optional; only if `OLLAMA_ENDPOINT` is set)
- Static files presence (static/css, static/js)

Interpreting results:
- "OK" means the check passed
- "WARN" indicates an optional or environment-specific issue; the project should still run
- "FAIL" indicates a problem to fix; the command exits with a non-zero status when any failures occur

Notes:
- Newspaper3k and lxml cleaner: With lxml>=5, the HTML cleaner was split out. If you see a warning like:
  "lxml.html.clean module is now a separate project lxml_html_clean", you can install either `lxml[html_clean]` or `lxml_html_clean`. This is treated as a WARN by default since Newspaper3k is optional in this project.

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

   # To toggle AI usage (defaults to on)
   python manage.py analyze_articles --use-ai


3. **Verify the Results**
   - Return to the admin panel
   - Check that your article now has `is_analyzed` set to True
   - Navigate to "Bias analyses" and "Sentiment analyses" under the "News_analysis" section
   - You should see entries for your article with the analysis results

   - On the article page, a “Key Insights” collapsible section appears below the summary when insights are available.

#### Using Test Data Generator

For testing with multiple articles at once:

```bash
python manage.py generate_test_data --sources 5 --articles 10 --users 2
```


## Comment Voting (Upvote/Downvote)

Community voting helps surface the most valuable comments. Each user can upvote or downvote a comment, change their vote, or remove it.

Setup/migration:

- Run migrations to create `CommentVote` and add `cached_score` to comments:
  ```bash
  python manage.py migrate
  ```

Behavior:
- One vote per user per comment (up or down)
- Users can toggle the same vote to remove it
- Comment score is cached on the comment (`cached_score = upvotes - downvotes`)
- Comments and replies are ordered by score (then by recency)
- The UI highlights your current vote and updates instantly via AJAX


Rate limiting:
- Voting is rate-limited to one action per user every 2 seconds. Exceeding the limit returns HTTP 429 with a JSON error message ("Too many requests. Please slow down.").

API endpoints:
- Create/Update vote
  - POST /news/comments/<comment_id>/vote/ with `value=1` or `value=-1`
  - PUT   /news/comments/<comment_id>/vote/ with `value=1` or `value=-1` (used when switching from the opposite vote)
- Remove vote
  - DELETE /news/comments/<comment_id>/vote/

Examples:
```bash
# Upvote
curl -X POST -b cookiejar -d "value=1" http://127.0.0.1:8000/news/comments/42/vote/

# Switch to downvote
curl -X PUT -b cookiejar -d "value=-1" http://127.0.0.1:8000/news/comments/42/vote/

# Remove current vote
curl -X DELETE -b cookiejar http://127.0.0.1:8000/news/comments/42/vote/
```

Frontend:
- Vote buttons and score appear next to each comment
- Active state is indicated by color; counts update without page reload
- Requires the existing comments bundle `static/js/comments.js` and CSS in `static/css/site.css`

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


### Sources Overview
- Browse all sources at `/news/sources/` with reliability scores, political bias indicators (Left/Center/Right), and article counts.
- Click a source to view its articles (`/news/source/<id>/`).
- Also accessible from the navbar under Analysis Tools → Sources Overview.

### News Analysis
- Political bias detection and visualization using advanced NLP techniques
- Sentiment analysis to detect emotional tone (positive, negative, neutral)
- Named entity recognition and extraction
- Readability scoring and complexity analysis
- Visual indicators for source reliability and content bias
- Logical fallacy reference and detection (catalog + admin + per-article detections with user toggle and public reference page). Catalog now includes anchor links and dedicated detail pages for each fallacy.

- Advanced AI analysis using local LLMs via Ollama integration
- Key insights extraction and display (collapsible panel on article pages)


### Display Preferences (Summary & Key Insights)
- New user preference toggles in Accounts → Preferences:
  - enable_summary_display (default: True)
  - enable_key_insights (default: True)
- Behavior on article pages:
  - Visitors (not logged in): AI Summary and Key Insights are shown by default
  - Logged-in users: Sections are shown only if the corresponding toggle is enabled

### Key Insights UI
- The Key Insights section is expanded by default and uses a collapse toggle with an arrow:
  - ▲ when expanded, ▼ when collapsed
- Implemented via static/js/article_detail.js; styling via static/css/article_detail.css

### Static Assets
- Inline CSS/JS moved to static files:
  - CSS: static/css/site.css, static/css/article_detail.css
  - JS: static/js/article_detail.js, static/js/preferences.js
- Templates now include `{% load static %}` and reference these files (see base.html and article_detail.html)

### Source Reliability Scoring
- NewsSource.reliability_score is automatically updated after article analysis and can be recalculated in bulk:
  - Per-article update occurs at the end of `analyze_articles`
  - Bulk recalculation:
    ```bash
    python manage.py recalculate_reliability
    # or only sources with zero score
    python manage.py recalculate_reliability --only-zero
    ```
- Scoring considers:
  - Fact-check ratings (weighted) ~60%
  - Bias consistency (lower variance is better) ~20%
  - Logical fallacy frequency (fewer per article is better) ~20%
- On article pages, source reliability is displayed rounded to 3 decimals (e.g., 87.679/100)


#### Logical Fallacies
- Public reference page: visit `/analysis/fallacies/` for the catalog (name, description, example, detection counts). Each item has a URL anchor and a link icon for easy sharing.
- Detail pages: `/analysis/fallacies/<slug>/` show the fallacy details and a paginated list of articles where it was detected.
- User preference: Accounts → Preferences → "Enable Logical Fallacy Analysis" controls visibility on article pages
- Article pages:
  - Interactions: From the catalog detail page, each detection entry links directly to the highlighted location within the article. On article pages, hovering over an evidence excerpt glows the corresponding text; clicking scrolls smoothly and highlights for a few seconds.
  - Article Detail: shows detected fallacies when enabled (with confidence and evidence excerpt); each detection links directly to the catalog anchor and has a Details link
  - Analysis View: includes a "Logical Fallacies" card listing detections with anchor and Details links
- Pipeline: `analyze_articles` runs fallacy detection with Ollama when available; unknown labels are skipped unless added to the catalog (Admin > News Analysis > Logical fallacies)
- Seed data: catalog seeded with 25+ common fallacies (e.g., Appeal to Authority, Bandwagon, Slippery Slope, Red Herring, Circular Reasoning, Appeal to Emotion, Hasty Generalization, Begging the Question, Appeal to Ignorance, Cherry Picking, Gambler's Fallacy, etc.)


  - Robust highlighting: When character positions are missing/inaccurate, the article page falls back to searching the evidence excerpt within the rendered text (case-insensitive, then fuzzy token match) and highlights the first match; otherwise, it gracefully degrades (excerpt shown in sidebar only).
  - Clickable highlights: Highlighted spans are accessible links with tooltips (name + brief description) that navigate to the fallacy detail page for deeper context.
  - Exact alignment: Stored positions are saved in display-space indices (CR/LF removed) to match the DOM text produced by the `linebreaks` filter.


### User System
  - User authentication and profile management
  - Personalized news preferences
  - Saved articles with notes
  - Article likes/dislikes with dedicated liked articles page

### Misinformation Tracking
  - **Models & Infrastructure**: Complete database models for alerts and fact-checking
  - **Manual Fact-Checking**: Admin interface for creating fact-check results
  - **Source Reliability**: Basic reliability scoring system
  - **Automated Detection**: *In development* - Real-time misinformation detection pipeline



### Comments
- Threaded comments on article pages (login required to post)
- Placement/layout:
  - Full-width comments section positioned below the main article and sidebar (under the article content)
  - Responsive threading layout; uses available horizontal space on wide screens
  - **NEW**: Comment counters displayed on article cards in listing view and in article detail view
  - **NEW**: Clickable comment counters navigate directly to the comments section with smooth scrolling
- Authentication-based UI:
  - Visitors (not logged in): see comment content and metadata only (author, time-ago, edited); no Reply/Flag/action buttons
  - Logged-in users: actions appear below the comment text
    - Reply is a standalone button (available at all depths)
    - All other actions (Edit, Delete, Flag, Moderate when permitted) are in a dropdown menu across all screen sizes
- Actions (permissions-aware):
  - Reply (nested threading with unlimited depth)
  - Edit/Delete own comments
  - Flag/report (logged-in users)
  - Staff moderation remove/restore (staff only)
- UI/UX enhancements:
  - Reddit-style threading: colored left borders and indentation per depth, capped indentation to prevent overflow, per-thread collapse/expand toggle
  - **UPDATED**: Reply indicators shown for ALL replies (depth >= 1), not just at maximum depth
  - **UPDATED**: Reply indicators have two clickable parts:
    - Icon + "Replying to" text: highlights immediate parent comment only
    - @username link: navigates to user's public profile page
  - **NEW**: Smooth highlight animation when navigating to parent comments (WCAG AA compliant colors)
  - **NEW**: Load more replies functionality with pagination support for long threads
  - Relative timestamps (e.g., "2 hours ago") with tooltip showing absolute time
  - **UPDATED**: Depth handling: true depth stored in database (unlimited), MAX_DEPTH=5 used only for display indentation
  - Maximum depth handling: replies beyond depth 5 are displayed flat with reply indicators instead of further indentation

- Rate limiting to prevent spam (per-user, short rolling window)
- Preferences: Accounts → Preferences (auto-saves via AJAX)
  - Show comments (show_comments) controls visibility on article pages
  - Email me on replies (notify_on_comment_reply) [optional]
- Profile: My Comments at `/accounts/comments/` with pagination and quick stats (total, last 30 days)
- **NEW**: Public user profiles at `/accounts/user/<username>/` with:
  - Profile visibility preference (default: enabled)
  - Account information, statistics, liked articles, and comments
  - Privacy controls: private profiles show "This Profile is Private" message
  - Integration with comment system via @username links
- Frontend: `templates/news_aggregator/partials/comments.html`, `static/js/comments.js`, and styles in `static/css/site.css`
- Accessibility: All color choices maintain WCAG AA contrast compliance (4.5:1 for normal text, 3:1 for large text) across both light and dark themes
- **NEW**: MAX_DEPTH centralized via data attribute, single source of truth from backend


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
# IMPORTANT: Set DJANGO_DEBUG=True for local development
# This enables proper static file serving and debug features
DJANGO_DEBUG=True

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

**Important**: For local development, ensure `DJANGO_DEBUG=True` is set in your `.env` file. This enables Django's development server to properly serve static files (CSS, JavaScript, images). In production, use a proper web server like nginx or Apache to serve static files.

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
- [UI_UX_IMPROVEMENTS.md](UI_UX_IMPROVEMENTS.md) - Recent UI/UX improvements and fixes

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
