import logging
from django.core.management.base import BaseCommand
from news_aggregator.models import NewsArticle
from news_analysis.models import BiasAnalysis, SentimentAnalysis

# Import NLP libraries
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import spacy
import random  # todo:nc - Only for demo purposes - real implementation would use trained models

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

    def handle(self, *args, **options):
        article_id = options.get('article_id')
        limit = options.get('limit')
        force = options.get('force')
        
        # Initialize analyzers
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.stdout.write("Downloading Spacy model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
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
        """Analyze a single article for bias and sentiment"""
        try:
            self.stdout.write(f"Analyzing: {article.title}")
            
            # Perform sentiment analysis
            self.analyze_sentiment(article)
            
            # Perform bias analysis
            self.analyze_bias(article)
            
            # Mark article as analyzed
            article.is_analyzed = True
            article.save()
            
            self.stdout.write(self.style.SUCCESS(f"  Analysis complete for article ID {article.id}"))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error analyzing article {article.id}: {str(e)}"))
    
    def analyze_sentiment(self, article):
        """Perform sentiment analysis on the article content"""
        # Get VADER sentiment scores
        scores = self.sentiment_analyzer.polarity_scores(article.content)
        
        # Calculate sentiment score (-1 to 1)
        sentiment_score = scores['compound']
        
        # Create or update sentiment analysis
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
            
        except Exception as e:
            self.stderr.write(f"  Error saving sentiment analysis: {str(e)}")
    
    def analyze_bias(self, article):
        """Perform bias analysis on the article content"""
        # NOTE: This is a simplified demo implementation
        # In a real application, you would use a trained model for political bias detection
        
        # For demo purposes, we'll use a random bias score
        # In a real implementation, this would be based on a trained model
        
        # Extract some basic features 
        doc = self.nlp(article.content[:5000])  # Limit text length for performance
        
        # In a real app, you would extract meaningful lexical and semantic features here
        # and feed them to a trained model
        
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
            
        except Exception as e:
            self.stderr.write(f"  Error saving bias analysis: {str(e)}")
