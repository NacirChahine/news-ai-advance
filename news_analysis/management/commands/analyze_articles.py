import logging
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from news_aggregator.models import NewsArticle
from news_analysis.models import BiasAnalysis, SentimentAnalysis, FactCheckResult, LogicalFallacy, LogicalFallacyDetection, ArticleInsight

# Import NLP libraries
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import spacy
import random  # Used as a fallback if AI analysis fails

import re

from typing import Optional, Tuple, List

# Import advanced AI analysis functions
from news_analysis.utils import (
    analyze_sentiment_with_ai,
    detect_political_bias_with_ai,
    summarize_article_with_ai,
    extract_key_insights_with_ai,
    extract_claims,
    verify_claim_with_ai,
    detect_logical_fallacies_with_ai,
)
from news_aggregator.utils import update_source_reliability

from news_analysis.match_utils import find_related_alerts_for_article

# Download necessary NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

# --- Helpers for robust text position finding ---

def _tokens(text: str) -> List[str]:
    """Split into alphanumeric tokens for tolerant matching."""
    return re.findall(r"[A-Za-z0-9]+", text or "")


def _build_fuzzy_pattern(excerpt: str) -> Optional[re.Pattern]:
    """Build a case-insensitive regex that tolerates whitespace/punctuation variations between tokens.
    Example: "It’s false!" -> tokens ["It", "s", "false"] => pattern: It[\W_]+s[\W_]+false
    """
    toks = _tokens(excerpt)
    if not toks:
        return None
    pat = r"[\W_]+".join(re.escape(t) for t in toks)
    try:
        return re.compile(pat, re.IGNORECASE)
    except re.error:
        return None


def _robust_find_positions(content: str, excerpt: str, ai_start: Optional[int], ai_end: Optional[int]) -> Tuple[Optional[int], Optional[int], str]:
    """Return best-effort (start, end, strategy) positions of excerpt in content.
    Strategy indicates which method succeeded: 'ai', 'exact', 'ci', 'fuzzy', or 'none'.
    """
    text = content or ""
    ex = (excerpt or "").strip()

    # 1) Trust AI if plausible and matches substring
    if isinstance(ai_start, int) and isinstance(ai_end, int) and 0 <= ai_start < ai_end <= len(text):
        span = text[ai_start:ai_end]
        if ex and (ex.lower() in span.lower() or span.lower() in ex.lower()):
            return ai_start, ai_end, "ai"

    # 2) Exact search (case-sensitive)
    if ex:
        idx = text.find(ex)
        if idx != -1:
            return idx, idx + len(ex), "exact"

    # 3) Case-insensitive search
    if ex:
        low = text.lower()
        idx = low.find(ex.lower())
        if idx != -1:
            return idx, idx + len(ex), "ci"

    # 4) Fuzzy token-based search (tolerate punctuation/whitespace)
    rx = _build_fuzzy_pattern(ex)
    if rx:
        m = rx.search(text)
        if m:
            return m.start(), m.end(), "fuzzy"


# Normalize raw article text to approximate DOM-visible text produced by Django's `linebreaks` filter
# (linebreaks removes CR/LF by converting them into <p>/<br> elements; text nodes no longer contain newlines)
def _to_display_text(text: str) -> str:
    if not text:
        return ""
    # Normalize CRLF to LF, then remove LF and CR entirely
    t = text.replace("\r\n", "\n")
    t = t.replace("\r", "")
    t = t.replace("\n", "")
    return t


def _map_indices_raw_to_display(text: str, start: Optional[int], end: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
    if start is None or end is None:
        return start, end
    if start < 0 or end < 0 or end < start:
        return start, end
    # Count newline chars before start/end to compute the shift
    prefix_start = text[:start]
    prefix_end = text[:end]
    # Count both CR and LF. CRLF pairs will count as 2, which matches full removal of both.
    rm_start = prefix_start.count("\n") + prefix_start.count("\r")
    rm_end = prefix_end.count("\n") + prefix_end.count("\r")
    return start - rm_start, end - rm_end


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Analyzes news articles for bias and sentiment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article_id',
            type=int,
            help='ID of a specific article to analyze (optional)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of unanalyzed articles to process'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reanalysis of previously analyzed articles'
        )
        parser.add_argument(
            '--model',
            type=str,
            default='llama3',
            help='AI model to use for analysis (default: llama3)'
        )
        parser.add_argument(
            '--use-ai',
            action='store_true',
            default=True,
            help='Use AI models for analysis (default: True)'
        )

    def handle(self, *args, **options):
        article_id = options.get('article_id')
        limit = options.get('limit')
        force = options.get('force')
        self.force = force
        self.model = options.get('model')
        self.use_ai = options.get('use_ai')

        # Initialize analyzers (used as fallback if AI analysis fails)
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.stdout.write("Downloading Spacy model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        if self.use_ai:
            self.stdout.write(f"Using AI model: {self.model} for analysis")

        if article_id:
            try:
                articles = [NewsArticle.objects.get(id=article_id)]
                self.stdout.write(f"Analyzing article: {articles[0].title}")
            except NewsArticle.DoesNotExist:
                self.stderr.write(f"Error: Article with ID {article_id} does not exist")
                return
        else:
            # Get unanalyzed articles or all articles if force flag is set
            if force:
                articles = NewsArticle.objects.all()[:limit]
            else:
                articles = NewsArticle.objects.filter(is_analyzed=False)[:limit]

            article_count = len(articles)
            self.stdout.write(f"Analyzing {article_count} articles")

        for article in articles:
            self.analyze_article(article)

        self.stdout.write(self.style.SUCCESS('Analysis completed!'))

    def analyze_article(self, article):
        """Analyze a single article for bias, sentiment, and other metrics"""
        try:
            self.stdout.write(f"Analyzing: {article.title}")

            # Perform sentiment analysis
            self.analyze_sentiment(article)

            # Perform bias analysis
            self.analyze_bias(article)

            # Detect logical fallacies
            self.analyze_fallacies(article)

            if self.use_ai:
                # Generate article summary
                self.generate_summary(article)

                # Extract key insights
                self.extract_key_insights(article)

            # Generate placeholder fact-check records (non-destructive; skips if already present)
            self.generate_fact_checks(article)

            # Link related misinformation alerts (no creation, just association)
            try:
                related_alerts = find_related_alerts_for_article(article)
                if related_alerts:
                    for alert in related_alerts:
                        alert.related_articles.add(article)
                    self.stdout.write(f"  Linked {len(related_alerts)} misinformation alert(s)")
                else:
                    self.stdout.write("  No related misinformation alerts found")
            except Exception as e:
                self.stderr.write(f"  Error linking misinformation alerts: {str(e)}")

            # Mark article as analyzed
            article.is_analyzed = True

            # Recalculate source reliability based on updated analyses
            try:
                new_score = update_source_reliability(article.source)
                self.stdout.write(f"  Updated source reliability: {new_score:.3f}/100 for '{article.source.name}'")
            except Exception as e:
                self.stderr.write(f"  Failed to update source reliability: {e}")

            article.save()

            self.stdout.write(self.style.SUCCESS(f"  Analysis complete for article ID {article.id}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error analyzing article {article.id}: {str(e)}"))

    def analyze_sentiment(self, article):
        """Perform sentiment analysis on the article content"""
        try:
            if self.use_ai:
                # Use advanced AI sentiment analysis
                self.stdout.write(f"  Performing AI sentiment analysis with {self.model}...")
                result = analyze_sentiment_with_ai(article.content, model=self.model)

                # Extract scores from AI analysis result
                sentiment_score = result.get('score', 0)

                # For compatibility with the SentimentAnalysis model, we need to estimate
                # positive, negative, and neutral scores based on the AI sentiment score
                if sentiment_score > 0:
                    pos_score = sentiment_score
                    neg_score = 0
                    neu_score = 1 - pos_score
                elif sentiment_score < 0:
                    neg_score = abs(sentiment_score)
                    pos_score = 0
                    neu_score = 1 - neg_score
                else:
                    pos_score = 0
                    neg_score = 0
                    neu_score = 1

                self.stdout.write(f"  AI sentiment classification: {result.get('classification', 'neutral')}")
            else:
                # Fallback to VADER sentiment analysis
                scores = self.sentiment_analyzer.polarity_scores(article.content)
                sentiment_score = scores['compound']
                pos_score = scores['pos']
                neg_score = scores['neg']
                neu_score = scores['neu']

            # Create or update sentiment analysis
            sentiment, created = SentimentAnalysis.objects.update_or_create(
                article=article,
                defaults={
                    'sentiment_score': sentiment_score,
                    'positive_score': pos_score,
                    'negative_score': neg_score,
                    'neutral_score': neu_score,
                }
            )

            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} sentiment analysis (score: {sentiment_score:.2f})")

        except Exception as e:
            self.stderr.write(f"  Error in sentiment analysis: {str(e)}")
            # Fallback to VADER if AI analysis fails
            self.stdout.write("  Falling back to VADER sentiment analysis...")
            scores = self.sentiment_analyzer.polarity_scores(article.content)
            sentiment_score = scores['compound']

            try:
                sentiment, created = SentimentAnalysis.objects.update_or_create(
                    article=article,
                    defaults={
                        'sentiment_score': sentiment_score,
                        'positive_score': scores['pos'],
                        'negative_score': scores['neg'],
                        'neutral_score': scores['neu'],
                    }
                )

                action = "Created" if created else "Updated"
                self.stdout.write(f"  {action} sentiment analysis (score: {sentiment_score:.2f})")
            except Exception as e2:
                self.stderr.write(f"  Error saving sentiment analysis: {str(e2)}")

    def analyze_bias(self, article):
        """Perform bias analysis on the article content"""
        try:
            if self.use_ai:
                # Use advanced AI bias detection
                self.stdout.write(f"  Performing AI bias analysis with {self.model}...")
                result = detect_political_bias_with_ai(article.content, model=self.model)

                # Extract values from AI analysis result
                political_leaning = result.get('political_leaning', 'unknown')
                bias_score = result.get('bias_score', 0)
                confidence = result.get('confidence', 0.7)

                self.stdout.write(f"  AI bias detection: {political_leaning} (confidence: {confidence:.2f})")
                if 'explanation' in result:
                    self.stdout.write(f"  Explanation: {result['explanation'][:100]}...")
            else:
                # Fallback to random bias generation (for demo purposes)
                self.stdout.write("  Using random bias generation (demo mode)...")

                # Extract some basic features
                doc = self.nlp(article.content[:5000])  # Limit text length for performance

                # For demo purposes, generate a random bias score between -1 and 1
                # -1 = far left, 0 = center, 1 = far right
                bias_score = random.uniform(-1, 1)

                # Set the political leaning based on the score
                if bias_score < -0.5:
                    political_leaning = 'left'
                elif bias_score < -0.1:
                    political_leaning = 'center-left'
                elif bias_score < 0.1:
                    political_leaning = 'center'
                elif bias_score < 0.5:
                    political_leaning = 'center-right'
                else:
                    political_leaning = 'right'

                # Confidence score (would be provided by the model in a real implementation)
                confidence = random.uniform(0.6, 0.95)

            # Create or update bias analysis
            bias, created = BiasAnalysis.objects.update_or_create(
                article=article,
                defaults={
                    'political_leaning': political_leaning,
                    'bias_score': bias_score,
                    'confidence': confidence,
                }
            )

            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} bias analysis (leaning: {political_leaning}, score: {bias_score:.2f})")

        except Exception as e:
            self.stderr.write(f"  Error in bias analysis: {str(e)}")
            # Fallback to random bias generation if AI analysis fails
            self.stdout.write("  Falling back to random bias generation...")

            # Generate a random bias score between -1 and 1
            bias_score = random.uniform(-1, 1)

            # Set the political leaning based on the score
            if bias_score < -0.5:
                political_leaning = 'left'
            elif bias_score < -0.1:
                political_leaning = 'center-left'
            elif bias_score < 0.1:
                political_leaning = 'center'
            elif bias_score < 0.5:
                political_leaning = 'center-right'
            else:
                political_leaning = 'right'

            # Confidence score
            confidence = random.uniform(0.6, 0.95)

            try:
                bias, created = BiasAnalysis.objects.update_or_create(
                    article=article,
                    defaults={
                        'political_leaning': political_leaning,
                        'bias_score': bias_score,
                        'confidence': confidence,
                    }
                )

                action = "Created" if created else "Updated"
                self.stdout.write(f"  {action} bias analysis (leaning: {political_leaning}, score: {bias_score:.2f})")
            except Exception as e2:
                self.stderr.write(f"  Error saving bias analysis: {str(e2)}")


    def analyze_fallacies(self, article):
        """Detect logical fallacies in the article content using AI.
        Idempotent: if detections exist and not forced, skip. If forced, replace.
        """
        try:
            content = (article.content or "").strip()
            if not content:
                self.stdout.write("  No content available for fallacy detection; skipping")
                return

            # Idempotency controls
            existing_qs = LogicalFallacyDetection.objects.filter(article=article)
            if existing_qs.exists() and not getattr(self, 'force', False):
                self.stdout.write("  Fallacy detections already exist; skipping (use --force to regenerate)")
                return
            if getattr(self, 'force', False) and existing_qs.exists():
                count = existing_qs.count()
                existing_qs.delete()
                self.stdout.write(f"  Removed {count} existing fallacy detection(s) due to --force")

            if not self.use_ai:
                self.stdout.write("  AI disabled; skipping fallacy detection")
                return

            self.stdout.write(f"  Detecting logical fallacies with {self.model}...")
            detections = detect_logical_fallacies_with_ai(content, model=self.model) or []

            if not detections:
                self.stdout.write("  No logical fallacies detected")
                return

            created = 0
            for det in detections:
                name = det.get("name") or ""
                if not name:
                    continue
                # Match to catalog by name or slug
                lf = LogicalFallacy.objects.filter(name__iexact=name).first()
                if not lf:
                    slug = slugify(name)
                    lf = LogicalFallacy.objects.filter(slug=slug).first()
                if not lf:
                    self.stderr.write(f"  Unknown fallacy label from AI: '{name}' — skipping (add to catalog if desired)")
                    continue

                # Compute robust positions and map to display-space indices (no CR/LF) to match DOM indexing
                ex = (det.get("evidence_excerpt") or "")[:500]
                ai_s = det.get("start_char")
                ai_e = det.get("end_char")
                start_idx, end_idx, strategy = _robust_find_positions(content, ex, ai_s, ai_e)
                disp_start, disp_end = _map_indices_raw_to_display(content, start_idx, end_idx)

                # Temporary detailed diagnostics to root-cause offset issues
                # try:
                #     raw_before = content[max(0, (start_idx or 0) - 20): (start_idx or 0)]
                #     raw_match = content[(start_idx or 0): (end_idx or 0)]
                #     raw_after = content[(end_idx or 0): min(len(content), (end_idx or 0) + 20)]
                #     disp_text = _to_display_text(content)
                #     disp_before = disp_text[max(0, (disp_start or 0) - 20): (disp_start or 0)]
                #     disp_match = disp_text[(disp_start or 0): (disp_end or 0)]
                #     disp_after = disp_text[(disp_end or 0): min(len(disp_text), (disp_end or 0) + 20)]
                #     self.stdout.write(
                #         "  Span debug → name='%s' ai=(%s,%s) raw=(%s,%s) disp=(%s,%s) strat=%s\n"
                #         "    ex=\"%s\"\n"
                #         "    raw:  ...%s[%s]%s...\n"
                #         "    disp: ...%s[%s]%s..." % (
                #             name,
                #             str(ai_s), str(ai_e), str(start_idx), str(end_idx), str(disp_start), str(disp_end), strategy,
                #             ex,
                #             raw_before, raw_match, raw_after,
                #             disp_before, disp_match, disp_after,
                #         )
                #     )
                # except Exception:
                #     pass

                if strategy != "ai":
                    self.stdout.write(f"  Adjusted fallacy span via {strategy} search for '{name}'")

                LogicalFallacyDetection.objects.create(
                    article=article,
                    fallacy=lf,
                    confidence=det.get("confidence"),
                    evidence_excerpt=ex,
                    start_char=disp_start,
                    end_char=disp_end,
                    detected_at=timezone.now(),
                )
                created += 1

            self.stdout.write(f"  Created {created} logical fallacy detection(s)")
        except Exception as e:
            self.stderr.write(f"  Error in logical fallacy detection: {str(e)}")


    def generate_summary(self, article):
        """Generate a summary of the article using AI"""
        try:
            self.stdout.write(f"  Generating article summary with {self.model}...")
            # Build optional alert context for the prompt
            related_alerts = list(article.misinformation_alerts.filter(is_active=True)[:3])
            alert_context = None
            if related_alerts:
                lines = [f"- {a.title} ({a.severity})" for a in related_alerts]
                alert_context = "\n".join(lines)

            summary = summarize_article_with_ai(article.content, model=self.model, alert_context=alert_context)

            if summary:
                # Update the article's summary field
                if not article.summary or len(article.summary) < 10:
                    article.summary = summary
                    article.is_summarized = True
                    article.save(update_fields=['summary', 'is_summarized'])
                    self.stdout.write(f"  Created article summary ({len(summary)} chars)")
                else:
                    self.stdout.write(f"  Article already has a summary, not overwriting")
            else:
                self.stdout.write(f"  Failed to generate summary")

        except Exception as e:
            self.stderr.write(f"  Error generating summary: {str(e)}")

    def extract_key_insights(self, article):
        """Extract key insights from the article using AI, clean them, and persist to DB.
        Idempotent: if insights exist and are not forced, skip. If forced, replace it.
        """
        try:
            content = (article.content or '').strip()
            if not content:
                self.stdout.write("  No content available for insights; skipping")
                return

            # Idempotency controls
            existing_qs = ArticleInsight.objects.filter(article=article)
            if existing_qs.exists() and not getattr(self, 'force', False):
                self.stdout.write("  Insights already exist; skipping (use --force to regenerate)")
                return
            if getattr(self, 'force', False) and existing_qs.exists():
                count = existing_qs.count()
                existing_qs.delete()
                self.stdout.write(f"  Removed {count} existing insight(s) due to --force")

            self.stdout.write(f"  Extracting key insights with {self.model}...")
            raw_insights = extract_key_insights_with_ai(content, model=self.model, num_insights=5) or []

            # Cleaning logic to remove headers/preambles/brackets and normalize list items
            cleaned = []
            seen = set()
            header_patterns = [
                r"^extract(ed|ing)?\b.*key insight",  # e.g., "Extracted 5 key insights:"
                r"^here (are|'re) the \d+ (most )?important insight",  # e.g., "Here are the 5 most important insights..."
                r"^key insight(s)?\b",
                r"^insight(s)?\s*:?$",
                r"^summary\s*:?$",
            ]
            header_rx = re.compile("|".join(header_patterns), re.IGNORECASE)

            def normalize_line(s: str) -> str:
                x = (s or '').strip()
                # Strip code fences and brackets-only lines
                if x in ('[', ']', '[[', ']]', '[...', '...]', '...', '""', "''"):
                    return ''
                # Drop lines that are just brackets/commas
                if re.fullmatch(r"^[\[\]\{\}\,]+$", x):
                    return ''
                # Remove markdown/number bullets ("- ", "* ", "1. ", "1) ", "1: ")
                x = re.sub(r"^[-*\u2022]\s+", '', x)
                x = re.sub(r"^\d+\s*[\.)\]:-]\s*", '', x)
                # Trim wrapping quotes
                x = x.strip().strip('"').strip("'")
                # Remove trailing commas/semicolons leftover from JSON-ish lists
                x = re.sub(r"[,;]+$", '', x).strip()
                return x

            for line in raw_insights:
                if not isinstance(line, str):
                    continue
                t = normalize_line(line)
                if not t:
                    continue
                # Filter generic headers/preambles
                if header_rx.search(t):
                    continue
                # Remove extremely short or punctuation-only strings
                if len(t) < 3 or re.fullmatch(r"^[^A-Za-z0-9]+$", t):
                    continue
                # Deduplicate while preserving order (case-insensitive key)
                key = t.lower()
                if key in seen:
                    continue
                seen.add(key)
                cleaned.append(t)

            if not cleaned:
                self.stdout.write("  No substantive insights extracted")
                return

            # Persist cleaned insights in ranked order
            created = 0
            for idx, text in enumerate(cleaned[:10]):  # safety cap
                ArticleInsight.objects.create(article=article, text=text[:1000], rank=idx)
                created += 1

            self.stdout.write(f"  Saved {created} cleaned insight(s)")
        except Exception as e:
            self.stderr.write(f"  Error extracting insights: {str(e)}")


    def generate_fact_checks(self, article):
        """Extract claims and verify them using an LLM. Skips if any fact-checks already exist.
        Applies simple rate limiting between calls.
        """
        try:
            # Skip if fact checks already exist for this article
            if article.fact_checks.exists():
                self.stdout.write("  Fact-checks already exist; skipping generation")
                return

            content = (article.content or "").strip()
            title = (article.title or "").strip()

            # Extract up to 5 candidate claims
            claims = extract_claims(content, max_claims=5)
            # Ensure we include headline if meaningful and not duplicate
            if title and all(title not in c for c in claims):
                claims = [f"Headline claim: {title}"] + claims

            if not claims:
                self.stdout.write("  No suitable claims found for fact-checking")
                return

            created_count = 0
            # Rate limiting: 1s delay between verification calls
            for claim in claims[:5]:
                try:
                    result = verify_claim_with_ai(claim, context_text=content, model=self.model)
                except Exception as ve:
                    self.stderr.write(f"  Verification error: {ve}")
                    result = {"rating": "unverified", "confidence": 0.0, "explanation": "Verification failed", "sources": ""}

                fc = FactCheckResult.objects.create(
                    article=article,
                    claim=claim,
                    rating=result.get('rating', 'unverified'),
                    explanation=result.get('explanation', '')[:2000],
                    sources=str(result.get('sources', ''))[:1000],
                    confidence=result.get('confidence'),
                    last_verified=timezone.now(),
                )
                created_count += 1
                time.sleep(1)

            self.stdout.write(f"  Created {created_count} fact-check(s)")
        except Exception as e:
            self.stderr.write(f"  Error generating fact-checks: {str(e)}")
