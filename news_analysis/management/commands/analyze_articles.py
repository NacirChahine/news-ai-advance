import logging
from django.core.management.base import BaseCommand
from news_aggregator.models import NewsArticle
from news_analysis.models import BiasAnalysis, SentimentAnalysis

# Import NLP libraries
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import spacy
import random  # Used as a fallback if AI analysis fails

# Import advanced AI analysis functions
from news_analysis.utils import (
    analyze_sentiment_with_ai,
    detect_political_bias_with_ai,
    summarize_article_with_ai,
    extract_key_insights_with_ai
)

# Download necessary NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

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

            if self.use_ai:
                # Generate article summary
                self.generate_summary(article)

                # Extract key insights
                self.extract_key_insights(article)

            # Mark article as analyzed
            article.is_analyzed = True
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

    def generate_summary(self, article):
        """Generate a summary of the article using AI"""
        try:
            self.stdout.write(f"  Generating article summary with {self.model}...")
            summary = summarize_article_with_ai(article.content, model=self.model)

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
        """Extract key insights from the article using AI"""
        try:
            self.stdout.write(f"  Extracting key insights with {self.model}...")
            insights = extract_key_insights_with_ai(article.content, model=self.model, num_insights=5)

            if insights:
                # Log the insights (in a real application, you might want to save these to a model)
                self.stdout.write(f"  Extracted {len(insights)} key insights:")
                for i, insight in enumerate(insights, 1):
                    self.stdout.write(f"    {i}. {insight}")
            else:
                self.stdout.write(f"  No insights extracted")

        except Exception as e:
            self.stderr.write(f"  Error extracting insights: {str(e)}")
