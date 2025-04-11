import random
import datetime
from faker import Faker
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from news_aggregator.models import NewsSource, NewsArticle, UserSavedArticle
from news_analysis.models import BiasAnalysis, SentimentAnalysis, FactCheckResult, MisinformationAlert

class Command(BaseCommand):
    help = 'Generates test data for the News Advance application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sources',
            type=int,
            default=10,
            help='Number of news sources to generate'
        )
        parser.add_argument(
            '--articles',
            type=int,
            default=50,
            help='Number of articles per source to generate'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of test users to generate'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data'
        )

    def handle(self, *args, **options):
        num_sources = options.get('sources')
        num_articles_per_source = options.get('articles')
        num_users = options.get('users')
        clear_data = options.get('clear')
        
        # Initialize Faker
        fake = Faker()
        
        if clear_data:
            self.clear_existing_data()
            
        # Generate test users
        users = self.generate_test_users(num_users, fake)
        
        # Generate news sources
        sources = self.generate_news_sources(num_sources, fake)
        
        # Generate articles
        articles = self.generate_articles(sources, num_articles_per_source, fake)
        
        # Generate analysis data
        self.generate_analysis_data(articles, fake)
        
        # Generate user interactions
        self.generate_user_interactions(users, articles, fake)
        
        # Generate misinformation alerts
        self.generate_misinformation_alerts(articles, fake)
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated test data: '
            f'{len(users)} users, '
            f'{len(sources)} sources, '
            f'{len(articles)} articles'
        ))
    
    def clear_existing_data(self):
        """Clear existing data from the database"""
        self.stdout.write('Clearing existing data...')
        
        # Clear user-generated content first (foreign key constraints)
        UserSavedArticle.objects.all().delete()
        BiasAnalysis.objects.all().delete()
        SentimentAnalysis.objects.all().delete()
        FactCheckResult.objects.all().delete()
        MisinformationAlert.objects.all().delete()
        
        # Then clear main content
        NewsArticle.objects.all().delete()
        NewsSource.objects.all().delete()
        
        # Remove test users
        User.objects.filter(username__startswith='testuser').delete()
        
        self.stdout.write(self.style.SUCCESS('Existing data cleared.'))
    
    def generate_test_users(self, num_users, fake):
        """Generate test users"""
        self.stdout.write(f'Generating {num_users} test users...')
        
        users = []
        for i in range(num_users):
            username = f'testuser{i+1}'
            
            # Skip if user already exists
            if User.objects.filter(username=username).exists():
                users.append(User.objects.get(username=username))
                continue
            
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                password='testpassword',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            
            # Update profile
            user.profile.bio = fake.paragraph()
            user.profile.save()
            
            # Update preferences
            user.preferences.political_filter = random.choice(['all', 'balanced', 'neutral_only', 'diverse'])
            user.preferences.save()
            
            users.append(user)
            
        return users
    
    def generate_news_sources(self, num_sources, fake):
        """Generate news sources"""
        self.stdout.write(f'Generating {num_sources} news sources...')
        
        sources = []
        
        # Define a mix of political leanings for more realistic test data
        news_types = [
            ('left', 'Liberal News', 'Progressive Tribune', 'Left Journal', 'Blue State Report'),
            ('center-left', 'Daily Progress', 'Modern Observer', 'Progressive Herald'),
            ('center', 'Neutral Times', 'Balanced View', 'Center Daily', 'Fact Chronicle'),
            ('center-right', 'Traditional Herald', 'Conservative Observer', 'Heritage Daily'),
            ('right', 'Right Review', 'Conservative Tribune', 'Red State Report'),
        ]
        
        for i in range(num_sources):
            # Determine political leaning for this source
            leaning_idx = min(i % len(news_types), len(news_types) - 1)
            leaning, *name_options = news_types[leaning_idx]
            
            name = random.choice(name_options)
            if NewsSource.objects.filter(name=name).exists():
                sources.append(NewsSource.objects.get(name=name))
                continue
            
            # Generate a reliability score based on political leaning
            # Center sources get higher reliability scores than more extreme ones
            if leaning in ['center', 'center-left', 'center-right']:
                reliability = random.uniform(65, 95)
            else:
                reliability = random.uniform(40, 85)
            
            source = NewsSource.objects.create(
                name=name,
                url=f"https://www.{name.lower().replace(' ', '')}.com",
                description=fake.paragraph(),
                reliability_score=reliability
            )
            
            sources.append(source)
            
        return sources
    
    def generate_articles(self, sources, num_articles_per_source, fake):
        """Generate news articles for each source"""
        self.stdout.write(f'Generating {num_articles_per_source} articles per source...')
        
        articles = []
        
        # Topics for more realistic article generation
        topics = [
            "Politics", "Economy", "Health", "Technology", "Environment", 
            "Education", "International", "Science", "Sports", "Culture"
        ]
        
        for source in sources:
            for i in range(num_articles_per_source):
                # Generate a random topic
                topic = random.choice(topics)
                
                # Generate a title based on the topic
                title = fake.sentence().rstrip('.')
                if random.random() < 0.7:  # 70% chance to include topic in title
                    title = f"{topic}: {title}"
                
                # Determine published date (within last 30 days)
                days_ago = random.randint(0, 30)
                published_date = timezone.now() - datetime.timedelta(days=days_ago)
                
                # Generate unique URL
                url = f"{source.url}/news/{published_date.strftime('%Y/%m/%d')}/{fake.slug()}"
                
                # Skip if article with this URL already exists
                if NewsArticle.objects.filter(url=url).exists():
                    continue
                
                # Generate content
                paragraphs = []
                for _ in range(random.randint(5, 15)):
                    paragraphs.append(fake.paragraph())
                content = "\n\n".join(paragraphs)
                
                # Create summary (first paragraph)
                summary = paragraphs[0]
                
                article = NewsArticle.objects.create(
                    title=title,
                    source=source,
                    url=url,
                    author=fake.name(),
                    published_date=published_date,
                    content=content,
                    summary=summary,
                    image_url=f"https://picsum.photos/id/{random.randint(1, 1000)}/800/600",
                    is_analyzed=False,
                    is_summarized=True
                )
                
                articles.append(article)
                
        return articles
    
    def generate_analysis_data(self, articles, fake):
        """Generate analysis data for articles"""
        self.stdout.write('Generating analysis data for articles...')
        
        for article in articles:
            # Skip 10% of articles to simulate unanalyzed content
            if random.random() < 0.1:
                continue
                
            # Bias analysis
            # For realistic data, base the bias on the source's typical leaning
            source_name = article.source.name.lower()
            if 'liberal' in source_name or 'progressive' in source_name or 'blue' in source_name:
                bias_score = random.uniform(-1.0, -0.3)
                if bias_score < -0.7:
                    political_leaning = 'left'
                else:
                    political_leaning = 'center-left'
            elif 'conservative' in source_name or 'traditional' in source_name or 'red' in source_name:
                bias_score = random.uniform(0.3, 1.0)
                if bias_score > 0.7:
                    political_leaning = 'right'
                else:
                    political_leaning = 'center-right'
            else:
                bias_score = random.uniform(-0.3, 0.3)
                political_leaning = 'center'
            
            BiasAnalysis.objects.create(
                article=article,
                political_leaning=political_leaning,
                bias_score=bias_score,
                confidence=random.uniform(0.6, 0.95)
            )
            
            # Sentiment analysis
            sentiment_score = random.uniform(-0.8, 0.8)
            positive_score = max(0, sentiment_score) if sentiment_score > 0 else random.uniform(0, 0.4)
            negative_score = max(0, -sentiment_score) if sentiment_score < 0 else random.uniform(0, 0.4)
            neutral_score = 1.0 - positive_score - negative_score
            
            SentimentAnalysis.objects.create(
                article=article,
                sentiment_score=sentiment_score,
                positive_score=positive_score,
                negative_score=negative_score,
                neutral_score=neutral_score
            )
            
            # Fact checks (20% chance of having fact checks)
            if random.random() < 0.2:
                # Number of fact checks for this article
                num_facts = random.randint(1, 3)
                
                for _ in range(num_facts):
                    claim = fake.sentence()
                    rating = random.choice([
                        'true', 'mostly_true', 'half_true', 'mostly_false', 'false', 'pants_on_fire'
                    ])
                    
                    FactCheckResult.objects.create(
                        article=article,
                        claim=claim,
                        rating=rating,
                        explanation=fake.paragraph(),
                        sources=fake.url() if random.random() < 0.7 else ''
                    )
            
            # Mark article as analyzed
            article.is_analyzed = True
            article.save()
    
    def generate_user_interactions(self, users, articles, fake):
        """Generate user interactions with articles"""
        self.stdout.write('Generating user interactions...')
        
        for user in users:
            # Each user saves 5-15 random articles
            num_saved = random.randint(5, 15)
            random_articles = random.sample(articles, min(num_saved, len(articles)))
            
            for article in random_articles:
                # Skip if already saved
                if UserSavedArticle.objects.filter(user=user, article=article).exists():
                    continue
                    
                # Random save date within last 30 days
                days_ago = random.randint(0, 30)
                saved_at = timezone.now() - datetime.timedelta(days=days_ago)
                
                # 30% chance of adding notes
                notes = fake.paragraph() if random.random() < 0.3 else ''
                
                UserSavedArticle.objects.create(
                    user=user,
                    article=article,
                    saved_at=saved_at,
                    notes=notes
                )
    
    def generate_misinformation_alerts(self, articles, fake):
        """Generate misinformation alerts"""
        self.stdout.write('Generating misinformation alerts...')
        
        # Generate 3-5 misinformation alerts
        num_alerts = random.randint(3, 5)
        
        for i in range(num_alerts):
            title = fake.sentence()
            description = fake.paragraph()
            severity = random.choice(['low', 'medium', 'high', 'critical'])
            
            # Random detection date within last 14 days
            days_ago = random.randint(0, 14)
            detected_at = timezone.now() - datetime.timedelta(days=days_ago)
            
            # 70% chance of being active
            is_active = random.random() < 0.7
            
            # If not active, add resolution details and date
            if not is_active:
                resolution_details = fake.paragraph()
                resolved_at = detected_at + datetime.timedelta(days=random.randint(1, 3))
            else:
                resolution_details = ''
                resolved_at = None
            
            alert = MisinformationAlert.objects.create(
                title=title,
                description=description,
                severity=severity,
                detected_at=detected_at,
                is_active=is_active,
                resolution_details=resolution_details,
                resolved_at=resolved_at
            )
            
            # Add random related articles (2-5)
            num_related = random.randint(2, 5)
            related_articles = random.sample(articles, min(num_related, len(articles)))
            
            for article in related_articles:
                alert.related_articles.add(article)
