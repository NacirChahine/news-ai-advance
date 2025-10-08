<!-- 🔄 Synced with README.md → Maintain human-readable summaries here.
**AI NOTE**: This file contains extended technical context for the AI. -->

# News Advance: Technical Documentation

An AI-powered news credibility analyzer built with Django. This document provides detailed technical information for AI context.

## Project Architecture

The News Advance system is built on Django 5.2 with a modular architecture organized into specialized apps:

- **news_aggregator**: News collection, storage, and management
- **news_analysis**: AI analysis pipelines and algorithms (bias detection, sentiment analysis, ML summarization)
- **accounts**: User authentication, profiles, saved articles, and preference management

## Data Models

### News Aggregator Models

- **NewsSource**: Represents news publishers with reliability and bias metrics
  - Fields: name, url, description, reliability_score (0-100), political_bias (-1 left .. +1 right), logo, created_at, updated_at
  - Relationships: one-to-many with NewsArticle

- **NewsArticle**: Core content model for news articles
  - Fields: title, content, author, published_date, url, summary, image_url, is_analyzed, is_summarized
  - Relationships: many-to-one with NewsSource, one-to-one with analysis models

- **UserSavedArticle**: Tracks user-saved articles with notes
  - Fields: user, article, saved_at, notes
  - Relationships: many-to-one with User and NewsArticle

- **ArticleLike**: Tracks user likes/dislikes on articles
  - Fields: user, article, is_like (boolean: True=like, False=dislike), created_at, updated_at
  - Relationships: many-to-one with User and NewsArticle
  - Constraints: unique_together on (user, article) - one reaction per user per article
  - Indexes: (article, is_like), (user, created_at)

### News Analysis Models

- **BiasAnalysis**: Political bias detection results
  - Fields: article, political_leaning, bias_score, confidence
  - Choices: left, center-left, center, center-right, right

- **SentimentAnalysis**: Emotional tone analysis
  - Fields: article, sentiment_score, positive_score, negative_score, neutral_score


- **ArticleInsight**: Key insights extracted for an article (ordered)
  - Fields: article (FK), text, rank (0-based), created_at
  - Indexes: (article, rank); Unique per (article, rank)

- **FactCheckResult**: Fact-checking of specific claims
  - Fields: article, claim, rating, explanation, sources
  - Choices: true, mostly_true, half_true, mostly_false, false, pants_on_fire

- **MisinformationAlert**: System-wide warnings about misinformation trends
  - Fields: title, description, severity, detected_at, is_active, resolution_details, resolved_at, related_articles
  - Choices for severity: low, medium, high, critical


- **LogicalFallacy**: Catalog of logical fallacies (reference data)
  - Fields: name (unique), slug (unique), description, example, created_at
  - Notes: Slugs used for anchors/links in the public reference page

- **LogicalFallacyDetection**: Article-level detections of logical fallacies
  - Fields: article (FK), fallacy (FK), confidence (0..1), evidence_excerpt, start_char, end_char, detected_at
  - Indexes: (article, fallacy)

### Accounts Models

- **UserProfile**: Extended user information
  - Fields: user, bio, avatar, preferred_sources
  - Relationships: one-to-one with User, many-to-many with NewsSource

- **UserPreferences**: User-specific settings for content filtering and analysis visibility
  - Fields: user, political_filter, show_politics, show_business, show_tech, show_health, show_entertainment, email_newsletter, enable_logical_fallacy_analysis, etc.
  - Relationships: one-to-one with User


### Commenting System

- Models (news_aggregator.models):
  - Comment(article, user, parent=null, content, created_at, updated_at, depth, is_edited, edited_at, is_deleted_by_user, is_removed_moderator, cached_score=int)
  - CommentFlag(comment, user, reason, created_at)
  - CommentVote(comment, user, value in {-1, 1}, created_at, updated_at)
- Indexes: (article, created_at), (parent, created_at), (cached_score)
- Depth enforcement: computed on save, true depth stored without capping
  - **UPDATED**: Model now stores true depth (unlimited), MAX_DEPTH=5 used only for display indentation
  - **UPDATED**: `get_display_depth()` method returns depth capped at MAX_DEPTH for UI rendering
  - **NEW**: Replies beyond MAX_DEPTH are displayed in a flat list structure (no further indentation)
  - **NEW**: ALL replies (depth >= 1) show a visual indicator with "↩️ Replying to @username"
  - **NEW**: Reply indicator has two clickable parts:
    - Icon/text: highlights immediate parent comment only
    - @username: navigates to user's public profile page
- Soft deletion: user deletes => content replaced with "[deleted]"; moderator removes => hidden to non-staff
- Preferences (accounts.models.UserPreferences):
  - show_comments: bool (controls visibility on article pages)
  - notify_on_comment_reply: bool (optional email notifications)
  - **NEW**: public_profile: bool (controls public profile visibility, default: True)
- Views (news_aggregator.views):
  - comments_list_create(article_id): GET paginated top-level comments (+ eager replies), POST create
    - **NEW**: Returns `total_comments` field with count of all comments (not just top-level)
  - comment_reply(comment_id): POST create child
    - **NEW**: No longer rejects replies at MAX_DEPTH (allows unlimited depth, displayed flat)
  - comment_replies(comment_id): GET paginated replies for a specific comment (10 per page)
  - comment_edit(comment_id): POST owner-only edit
  - comment_delete(comment_id): POST owner-only soft-delete
  - comment_moderate(comment_id): POST staff remove/restore
  - comment_flag(comment_id): POST user flag/report
  - comment_vote(comment_id): POST/PUT/DELETE create/update/remove user vote; returns { success, score, user_vote }
  - article_like_toggle(): POST like/dislike/remove article reaction; returns { success, like_count, dislike_count, user_action }
  - **NEW**: latest_news and article_detail views now include comment_count in context
- URLs (news_aggregator/urls.py): named routes under namespace `news_aggregator`
  - article-like-toggle/: POST endpoint for like/dislike actions
  - comments/<comment_id>/replies/: GET endpoint for paginated replies
- Rate limiting: cache-backed throttle per user+endpoint; voting limited to one action per 2 seconds. Excess attempts return HTTP 429 with JSON `{ "error": "Too many requests. Please slow down." }`.
- Serialization: lightweight dicts (id, content, user, created_at ISO, flags, permissions, score, user_vote, depth, replies[])
  - **NEW**: Includes `parent_username` field for displaying reply indicators
- Templates: `templates/news_aggregator/partials/comments.html` (included in `article_detail.html` when allowed)
  - **NEW**: Comment section header shows total comment count: "Comments (N)"
  - **NEW**: Article detail page shows clickable comment counter near like/dislike buttons
  - **NEW**: Article listing cards show clickable comment counter next to like/dislike buttons
- Frontend (static/js/comments.js + static/css/site.css):
  - **NEW**: MAX_DEPTH centralized via data attribute (data-max-depth="5") on comments section
  - Authentication-based controls: when `data-authenticated="false"`, no action buttons render. Logged-in users see actions below the comment text.
    - Reply button available at all depths (no longer hidden at MAX_DEPTH)
    - All other actions (Edit, Delete, Flag, Moderate when permitted) live in a dropdown across all screen sizes and depths
  - Voting UI: vertical up/down caret buttons with live score; active selection is colored (upvote green, downvote red); unauthenticated users see disabled icons with tooltips.
  - Threading UX: Reddit-style visual nesting with depth-specific left borders and indentation; capped indentation to avoid overflow; per-thread collapse/expand toggle.
    - **UPDATED**: Reply indicators shown for ALL replies (depth >= 1), not just at max depth
    - **UPDATED**: Reply indicator has two separate clickable elements:
      - Icon + "Replying to" text: highlights immediate parent comment only (not all ancestors)
      - @username link: navigates to user's public profile (/accounts/user/<username>/)
    - **NEW**: Comment highlight animation uses WCAG AA compliant colors (blue theme)
    - **NEW**: Load more replies functionality with pagination support (infrastructure in place)
  - Time display: relative "time ago" labels with a tooltip (`title`) containing the absolute timestamp.
  - Accessibility: interactive elements have aria-labels; dropdowns use Bootstrap JS; keyboard focus states preserved.
  - **NEW**: Comment counters use WCAG AA compliant colors for both light and dark themes
  - **NEW**: Smooth scroll behavior when clicking comment counters to navigate to comments section
- Placement: comments section is included full-width below the article and sidebar in `article_detail.html`.
- Backend serialization/loading:
  - **UPDATED**: `comments_list_create` recursively prefetches and serializes replies up to depth 20 (reasonable limit) and includes current-user vote mapping for all loaded comments.
  - Replies endpoint (`comment_replies`) includes user vote mapping for the page of replies returned and parent user info.
- **NEW**: Comment deep linking:
  - URL anchors like `#comment-40` automatically scroll to and highlight the target comment
  - Handled by `handleCommentDeepLink()` function in `static/js/comments.js`
  - Works on page load and hash change events
  - Highlights only comment content (not entire comment div) for subtle emphasis
- Depth handling:
  - **UPDATED**: Backend stores true depth without capping (unlimited nesting)
  - **UPDATED**: Model provides `get_display_depth()` method that caps at MAX_DEPTH for UI
  - Frontend displays replies beyond MAX_DEPTH in flat list with visual reply indicators
  - Reply indicators show parent username with two clickable parts (parent highlight vs profile navigation)

### Public User Profiles
- **NEW**: Public user profile system at `/accounts/user/<username>/`
- Profile visibility controlled by `public_profile` preference (default: True)
- Profile displays:
  - Account information: username, full name, bio, profile picture/letter avatar, member since date
  - Statistics: total comments, last 30 days comments, liked articles count
  - Liked articles tab: paginated list of articles user has liked
  - Comments tab: paginated list of user's public comments
- Privacy:
  - When `public_profile=False`, shows "This Profile is Private" message to others
  - User can always view their own profile regardless of privacy setting
  - Only approved, non-deleted, non-removed comments are shown
- Integration:
  - Reply indicators link to user profiles via @username
  - Profile accessible from comment author names throughout the site

- Profile integration: `accounts.views.comment_history` at `/accounts/comments/` with pagination and stats (total, last 30 days). Profile page shows total comment count and a "View My Comments" button.

#### Voting Logic Details
- Data integrity:
  - Unique constraint on (comment, user) in `CommentVote`
  - Check constraint restricts `value` to -1 or 1
- Cached score:
  - `Comment.cached_score` stores net score; updated atomically via `F('cached_score') + delta` during vote changes
  - Scenarios:
    - New vote (+1/-1): delta = value
    - Change vote (e.g., -1 -> +1): delta = new - old (e.g., +2)
    - Remove vote: delta = -old (e.g., +1 if removing -1)
- Ordering:
  - Top-level and replies are ordered by `-cached_score, -created_at, -id`
- API behavior:
  - POST or PUT with `value` in {-1, 1} creates or updates a vote; DELETE removes it
  - Returns updated `score` and the caller's `user_vote` for immediate UI update
- Frontend behavior:
  - Buttons toggle active class based on `user_vote`; score updates via AJAX without reload
  - Guests see disabled caret icons and are prompted to log in when attempting to vote

#### Migration
- Ensure migrations are applied:
  - `python manage.py migrate`
- Backfill is not required; existing comments start at score 0.

### Article Likes/Dislikes

- **Model**: `ArticleLike` (news_aggregator.models)
  - Fields: user, article, is_like (boolean: True=like, False=dislike), created_at, updated_at
  - Constraints: unique_together on (user, article) - one reaction per user per article
  - Indexes: (article, is_like), (user, created_at)

- **API Endpoint**: `/news/article-like-toggle/` (POST, requires authentication)
  - Parameters: article_id (required), action (required: 'like', 'dislike', or 'remove')
  - Behavior:
    - 'like': Creates a like or toggles off existing like; converts dislike to like
    - 'dislike': Creates a dislike or toggles off existing dislike; converts like to dislike
    - 'remove': Removes any existing like/dislike
  - Returns: { success, like_count, dislike_count, user_action }

- **Views**:
  - article_detail and latest_news: Include like/dislike counts and user's current reaction status
  - accounts.views.liked_articles: Displays all articles the user has liked with pagination
  - accounts.views.profile: Shows liked articles count in stats section

- **Frontend**:
  - Like/dislike buttons on article detail pages and article cards
  - Real-time count updates via AJAX (static/js/article_likes.js)
  - Active state styling for user's current reaction
  - Non-authenticated users see counts but cannot interact
  - **NEW**: Article cards are fully clickable with hover effects (lift, shadow, image zoom)
  - **NEW**: Save/unsave button positioned as floating overlay on article image
  - **NEW**: Red styling (btn-danger) for "Unsave" action per user preference
  - **NEW**: Placeholder image (SVG) for articles without images
  - **NEW**: All interactive elements (like, comment, save) work independently via z-index layering

- **Profile Integration**:
  - Profile stats show "Liked Articles" count (replaces "Topic Following")
  - "View Liked Articles" button navigates to `/accounts/liked-articles/`
  - Liked articles page displays articles in table format with pagination

## Processing Pipelines

### News Collection Pipeline

1. **Source Management**: Database of reliable and diverse news sources
2. **Article Fetching**: Using newspaper3k for automated content extraction
3. **Preprocessing**: HTML cleaning, content extraction, metadata parsing
4. **Storage**: Persistence of articles with normalized metadata

### Analysis Pipeline

1. **Content Preparation**: Text cleaning and normalization
2. **Bias Analysis**:
   - AI-powered political leaning detection using Ollama LLMs
   - Language pattern analysis for bias indicators
   - Fallback to random generation for demo purposes
3. **Logical Fallacy Detection**:
   - AI-powered fallacy detection via `detect_logical_fallacies_with_ai`
   - Matches AI labels to `LogicalFallacy` by name/slug; unknown labels are skipped
   - Idempotent: cleans and re-creates detections on `--force`
   - Highlighting UX (robust multi-tier):
     1) Use `start_char`/`end_char` when valid
     2) Fallback to case-insensitive exact search of `evidence_excerpt`
     3) Fuzzy token-based search tolerating punctuation/whitespace variations
     4) Graceful degrade: if no match, sidebar still shows excerpts/links
   - Interactive spans: highlighted text is clickable and keyboard-activatable (role=link, tabindex=0). Bootstrap tooltips announce “<name> — <desc> • Click to learn more”. Clicking navigates to `/analysis/fallacies/<slug>/`.
   - Backend position correction: `analyze_articles` uses `_robust_find_positions()` to validate/repair AI-provided spans. Strategies: 'ai' (trusted), 'exact', 'ci', 'fuzzy'. Adjustments are logged to stdout for traceability.
   - Index space: stored `start_char`/`end_char` are saved in display-space indices (CR/LF removed) to match DOM text produced by the `linebreaks` filter for precise highlighting.
4. **Sentiment Analysis**:
   - Primary: AI-enhanced sentiment analysis via Ollama
   - Fallback: VADER sentiment scoring
4. **Summarization**:
   - Primary: Fine-tuned BART model trained on BBC News Summary dataset
   - Fallback: Ollama-based summarization
5. **Key Insights**:
   - AI-powered extraction of important points via `extract_key_insights_with_ai`
   - Post-processing cleans non-substantive lines (e.g., headers like "Extracted 5 key insights:", preambles like "Here are the...", stray brackets)
   - Deduplicates, trims bullets/numbering/quotes, and filters very short/punctuation-only entries
   - Persisted as `ArticleInsight` rows (ordered by `rank`); idempotent with `--force` (replaces existing)
   - Frontend: collapsible "Key Insights" panel on article pages lists insights as bullet points
6. **Source Credibility**: Historical accuracy rating of publishers

## ML Models

### Text Summarization (news_analysis/ml_models/summarization)

The project includes a fine-tuned BART transformer model for summarizing news articles, trained on the [BBC News Summary dataset](https://huggingface.co/datasets/gopalkalpande/bbc-news-summary).

#### Architecture

- **Base Model**: BART (facebook/bart-base) sequence-to-sequence transformer model
- **Training Dataset**: BBC News Summary dataset with document-summary pairs
- **Tokenization**: Maximum input length of 1024 tokens, maximum summary length of 128 tokens
- **Performance Metrics**: Evaluated using ROUGE-1, ROUGE-2, and ROUGE-L scores

#### Training Configuration

- **Epochs**: 3 (default)
- **Batch Size**: 4 (default)
- **Learning Rate**: 5e-5
- **Max Input Length**: 1024 tokens
- **Max Target Length**: 128 tokens
- **Beam Search**: 4 beams for generation

#### Performance Metrics

- ROUGE-1: ~40-45%
- ROUGE-2: ~20-25%
- ROUGE-L: ~35-40%

#### Integration

The summarization model is integrated through:

- **summarize_article_with_ml_model()**: Primary function for ML-based summarization
- **summarize_article_with_ai()**: Enhanced to support both ML model and Ollama LLM fallback
- **SummarizationModel class**: Handles model loading and inference
- **Django integration**: Automatic model loading via `django_integration.py`

#### Configuration

Summarization model behavior is controlled through settings:

```python
# In settings.py
SUMMARIZATION_MODEL_DIR = BASE_DIR / 'news_analysis' / 'ml_models' / 'summarization' / 'trained_model'
SUMMARIZATION_BASE_MODEL = 'facebook/bart-base'  # Fallback if trained model not available
USE_ML_SUMMARIZATION = True  # Set to False to always use Ollama instead
```

## Utility Modules

### News Aggregator Utilities (news_aggregator/utils.py)

- **clean_html(html_content)**: Removes scripts, styles, and unwanted HTML elements
- **extract_article_content(url, timeout)**: Extracts article content using newspaper3k
- **get_domain_from_url(url)**: Extracts domain name from URL
- **check_url_accessibility(url, timeout)**: Verifies URL is accessible
- **extract_main_image(html_content, base_url)**: Finds the primary image in HTML content
- **summarize_text(text, max_sentences)**: Generates extractive summaries of article content

### News Analysis Utilities (news_analysis/utils.py)

#### Core Analysis Functions
- **analyze_sentiment(text)**: Performs sentiment analysis using VADER
- **extract_named_entities(text, entity_types)**: Identifies named entities using spaCy
- **extract_main_topics(text, top_n)**: Extracts key topics through frequency analysis
- **calculate_readability_score(text)**: Computes readability metrics (Flesch Reading Ease, etc.)

#### AI-Enhanced Functions (Ollama Integration)
- **query_ollama(prompt, model, system_prompt, max_tokens)**: Core function for Ollama API communication
- **summarize_article_with_ai(text, model, use_ml_model)**: AI-powered summarization with ML/Ollama fallback
- **analyze_sentiment_with_ai(text, model)**: Enhanced sentiment analysis using Ollama
- **detect_political_bias_with_ai(text, model)**: Political bias detection using Ollama
- **extract_key_insights_with_ai(text, model, num_insights)**: Key insights extraction using Ollama
- **detect_logical_fallacies_with_ai(text, model)**: Detects logical fallacies with structured outputs (name, confidence, evidence excerpt, span)

#### ML Model Integration
- **summarize_article_with_ml_model(text, max_length)**: Wrapper for fine-tuned BART model

## Management Commands

### Fetch News (news_aggregator/management/commands/fetch_news.py)

- Fetches articles from configured sources using newspaper3k
- Handles rate limiting, error recovery, and duplicate detection
- Implements smart scheduling to prioritize frequently updated sources
- Parameters: `--sources`, `--limit`

### Analyze Articles (news_analysis/management/commands/analyze_articles.py)

- Processes unanalyzed articles through the analysis pipeline
- Generates bias, logical fallacy detections, sentiment, and readability metrics
- Supports AI-enhanced analysis with configurable models
- Batched processing to handle large article volumes efficiently
- Parameters: `--article_id`, `--limit`, `--force`, `--model`, `--use-ai`

### Generate Test Data (news_aggregator/management/commands/generate_test_data.py)

- Creates sample data for development and testing
- Generates sources with varied political leanings
- Produces articles with realistic bias and sentiment distributions
- Simulates user interactions and saved articles
- Parameters: `--sources`, `--articles`, `--users`, `--clear`

- **news_aggregator/article_detail.html**: Article detail page; renders AI Summary and a collapsible Key Insights panel (when available), plus logical fallacies and fact checks

## User Interface

### News Analysis Templates

- **article_analysis.html**: Comprehensive article analysis view with visualization of bias, sentiment, logical fallacies, and reliability metrics
- **fallacies.html**: Public reference catalog of logical fallacies with descriptions and examples
- **misinformation_tracker.html**: Real-time dashboard of potentially misleading content
- **fallacy_detail.html**: Detail page for a single logical fallacy; shows description, example, and paginated list of related article detections
- **news_aggregator/source_list.html**: Sources overview with reliability scores, political bias badges, and per-source article counts


### Display Preference Controls (Summary & Key Insights)
- accounts.models.UserPreferences now includes:
  - enable_key_insights: bool = True
  - enable_summary_display: bool = True
- accounts.views.preferences persists these via POST and an AJAX auto-save endpoint (`accounts:auto_save_preferences`).
- Template logic (templates/news_aggregator/article_detail.html):
  - Summary and Key Insights sections render when:
    - User is not authenticated (default ON for visitors), OR
    - Authenticated and `request.user.preferences.<flag>` is True
- Frontend auto-save JS extracted to static/js/preferences.js.

### Key Insights UI & Assets
- Collapsible panel defaults to expanded (`.collapse.show`) with arrow button toggling:
  - ▲ when expanded (aria-expanded=true), ▼ when collapsed
- JS: static/js/article_detail.js updates the arrow on show/hide events and contains robust fallacy highlight logic (moved from inline script).
- CSS: static/css/article_detail.css styles the highlight states.
- Base stylesheet: static/css/site.css (moved navbar/footer styles from base.html; also removes underline from all `.breadcrumb a`).
- All templates use `{% load static %}` and reference static files via `<link>`/`<script src>`.

## Source Reliability Scoring
- Implemented in `news_aggregator.utils`:
  - `compute_source_reliability(source) -> float` (0..100)
    - Fact-check component (~60%): rating mapped to [0..1] with a gentle confidence weighting; averaged and scaled to 0..100.
    - Bias consistency (~20%): 1 - stdev(bias_score) (bounded [0..1]) → higher is better. Defaults to 85 with one data point, 60 when none.
    - Fallacy component (~20%): penalty up to 20 points when avg fallacies/article ≥ 3; component = 100 - penalty.
    - Final score is a weighted aggregate, clamped to [0, 100]. Safe fallback returns existing score on exceptions.
  - `update_source_reliability(source) -> float`: computes and persists only if materially changed (epsilon 1e-6).
- Management Command: `news_aggregator/management/commands/recalculate_reliability.py`
  - Usage: `python manage.py recalculate_reliability [--only-zero]`
- Pipeline Integration:
  - `news_analysis.management.commands.analyze_articles` calls `update_source_reliability(article.source)` after completing analysis for each article; logs the updated score with 3-decimal precision.
- UI Formatting:
  - On the article detail page, source reliability displayed with Django `floatformat:3` (rounding): e.g., `87.679/100`.

- **alert_detail.html**: Detailed view of individual misinformation alerts

### Accounts Templates

### Navigation
- Top navbar uses Bootstrap 5.3 with a modernized design (hover/active states, rounded links).
- "Analysis Tools" is a dropdown containing:
  - Misinformation Tracker (`news_analysis:misinformation_tracker`)
  - Logical Fallacies Catalog (`news_analysis:fallacies`) and detail pages (`news_analysis:fallacy_detail`)
  - Sources Overview (`news_aggregator:source_list`)
- Active state highlighting applied based on `request.resolver_match` (url_name/namespace) for clear context.


- **profile.html**: User profile with activity summary and preferences

## Misinformation Alerts: Architecture & Integration

### Manual Management (Admin)
- Model: `MisinformationAlert(title, description, severity, is_active, detected_at, resolution_details, resolved_at, related_articles)`
- Admin Enhancements:
  - list_display includes `related_count`
  - Actions: `mark_resolved`, `mark_active`, `send_alert_email`

### Email Notification Flow
- User opt-in: `accounts.UserPreferences.receive_misinformation_alerts` (bool)
- Recipient selection: users with the flag enabled and valid email (deduped)
- Templates: `templates/emails/misinformation_alert.txt` (HTML optional)
- Send paths:
  - Admin action on selected alerts
  - Management command: `send_misinformation_alerts` with options:
    - `--alert-id`, `--since YYYY-MM-DD`, `--active-only`, `--dry-run`

### Article Scanning Integration
- Utility: `news_analysis.match_utils.find_related_alerts_for_article(article)`
  - Heuristic keyword overlap on tokenized article and alert fields
  - Threshold configurable (default ~0.06), limited to top N
- Pipeline hook: `analyze_articles` command
  - After bias/sentiment/summary/insights, attempts to link existing active alerts to the article
  - Idempotent association via M2M; no auto-creation of alerts
- UI: `article_analysis.html`
  - Renders a "Misinformation Alerts" card listing active related alerts with severity badges and links

### AI Prompt Context Injection (Non-breaking)
- `summarize_article_with_ai(..., alert_context=None)` accepts an optional context string
- `analyze_articles.generate_summary()` passes a short list of related alert titles/severities if present
- Keeps function signature backward-compatible; ML model path unaffected

### API (Optional)
- JSON endpoint: `GET /analysis/api/articles/<id>/misinformation-alerts/`
- Response: `{ article_id, alerts: [{id, title, severity, detected_at}] }`

### Edge Cases & Notes
- If spaCy model unavailable, matching still works via token overlap
- Email sending aggregates recipients into a single message (per send) for simplicity; can batch if needed
- Admin actions handle toggling `is_active` and `resolved_at` consistently
- No schema changes added yet for automated ingestion (external_id, source meta, etc.) per current scope

- **preferences.html**: Settings interface for content filtering and notifications
- **saved_articles.html**: Management of user's saved articles collection

## Setup & Installation

### Prerequisites

- Python 3.8+
- pip
- spaCy english model: `python -m spacy download en_core_web_sm`
- Ollama (optional, for AI-enhanced analysis)

### Dependencies

- Django 5.2
- newspaper3k
- nltk
- spaCy

- transformers (for ML summarization model)
- torch (for ML model inference)
- datasets (for model training)
- evaluate (for model evaluation)
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

### Optional: Ollama Setup

1. Install Ollama from https://ollama.ai/download
2. Download recommended models:
   ```
   ollama pull llama3
   ollama pull mistral
   ollama pull phi
   ```
3. Start Ollama service

## Development Commands

### Generate Test Data

```
python manage.py generate_test_data --sources 10 --articles 30 --users 5 --clear
```

### News Fetching

```
python manage.py fetch_news --sources all --limit 10
```

### Article Analysis

```
python manage.py analyze_articles --unanalyzed-only --batch-size 20 --model llama3
```

### ML Model Training

```
cd news_analysis/ml_models/summarization
python train_summarization_model.py --model_name facebook/bart-base --output_dir ./trained_model
```

## Configuration

### Django Settings

```python
# Ollama Configuration
OLLAMA_ENDPOINT = 'http://localhost:11434/api/generate'

# ML Models Configuration
SUMMARIZATION_MODEL_DIR = BASE_DIR / 'news_analysis' / 'ml_models' / 'summarization' / 'trained_model'
SUMMARIZATION_BASE_MODEL = 'facebook/bart-base'
USE_ML_SUMMARIZATION = True
```

## Fact-Checking UX & Logic

- Creation & Verification:
  - During `analyze_articles`, if an article has no `FactCheckResult` rows yet, the command extracts 3–5 claims from content using NLP heuristics (entities, numbers, quotes, reporting verbs) and verifies each with an LLM via Ollama.
  - Each verification returns: `rating` (true/mostly_true/half_true/mostly_false/false/pants_on_fire/unverified), `confidence` (0..1), `explanation`, and `sources`.
  - Idempotent: skipped if any fact-checks already exist for that article.
- Re-verification:
  - `reverify_fact_checks` management command updates older entries (by last_verified) with fresh ratings/sources; includes rate limiting.
- Model fields:
  - FactCheckResult now tracks `confidence` (float) and `last_verified` (datetime). DB indexes on `rating` and `(article, last_verified)`.
- Display conditions on Article Detail (`templates/news_aggregator/article_detail.html`):
  - Authenticated + `request.user.preferences.enable_fact_check = True`:
    - Renders a Fact Checks accordion. If none exist, shows a neutral info alert that no fact-checks are available yet.
  - Authenticated + pref disabled:
    - Renders a secondary alert with a link to `accounts:preferences` prompting user to enable.
  - Not authenticated:
    - Renders a secondary alert with links to `accounts:signup` and `accounts:login`.
- Preferences UI (`accounts/templates/accounts/preferences.html`):
  - Fact-Checking toggle is enabled and persisted.
  - `accounts/views.preferences` now saves `enable_fact_check` from POST.

CLI tips:

```bash
python manage.py analyze_articles --article_id <ID> --force
python manage.py reverify_fact_checks --older-than-days 14 --limit 50
```

- Configuration:
  - OLLAMA_ENDPOINT default: http://localhost:11434/api/generate (overridable via env)
  - Model default: llama3 (configurable); ensure a local Ollama model is available


## Testing Strategy

- Unit tests for utility functions
- Integration tests for analysis pipelines
- View tests with Django test client
- End-to-end tests with Selenium
- ML model evaluation using ROUGE metrics

## Performance Considerations

- Asynchronous processing for long-running analysis tasks
- Caching layer for frequently accessed analysis results
- Pagination and lazy loading for article listings
- Batch processing for analysis pipelines
- Model caching for ML inference
- GPU acceleration support for ML models

## Static Files Configuration

### Overview
The project uses Django's static files system to serve CSS, JavaScript, and images. Static files are organized in the `static/` directory at the project root.

### Directory Structure
```
static/
├── css/
│   ├── site.css           # Global styles (navbar, footer, buttons, etc.)
│   └── article_detail.css # Article-specific styles
├── js/
│   ├── theme.js           # Dark/light theme toggling
│   ├── article_actions.js # Save/unsave article functionality
│   ├── article_detail.js  # Article page interactions
│   ├── article_likes.js   # Like/dislike functionality
│   ├── comments.js        # Comment system
│   └── preferences.js     # User preferences auto-save
└── images/
    └── favicon.ico
```

### Settings Configuration
In `news_advance/settings.py`:
```python
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # For collectstatic in production
STATICFILES_DIRS = [BASE_DIR / 'static']  # Development static files
```

### URL Configuration
In `news_advance/urls.py`:
- Static files are served via `staticfiles_urlpatterns()` for development
- Media files are served via `static()` helper when `DEBUG=True`
- In production, use nginx/Apache to serve static files from `STATIC_ROOT`

### Development Setup
**IMPORTANT**: For local development, ensure `DJANGO_DEBUG=True` is set in your `.env` file:
```env
DJANGO_DEBUG=True
```

This enables:
- Django's development server to serve static files
- Debug toolbar and error pages
- Automatic template reloading

### Troubleshooting Static Files

**Problem**: CSS/JS files return 404 or wrong MIME type ('text/html' instead of 'text/css')

**Common Causes**:
1. `DJANGO_DEBUG=False` in `.env` file (should be `True` for development)
2. Missing `staticfiles_urlpatterns()` in `urls.py`
3. Static files not in correct directory structure
4. Browser caching old responses

**Solutions**:
1. Check `.env` file has `DJANGO_DEBUG=True`
2. Clear browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)
3. Verify files exist in `static/css/` and `static/js/` directories
4. Restart Django development server
5. Check browser console for specific error messages

**Production Deployment**:
1. Run `python manage.py collectstatic` to gather all static files
2. Configure web server (nginx/Apache) to serve from `STATIC_ROOT`
3. Set `DJANGO_DEBUG=False` in production `.env`
4. Never use Django to serve static files in production

## Future Development Plans

1. **Advanced NLP Models**:
   - Fine-tuned BERT models for bias detection
   - Enhanced transformer-based text analysis

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