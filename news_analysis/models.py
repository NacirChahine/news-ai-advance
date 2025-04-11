from django.db import models
from news_aggregator.models import NewsArticle

class BiasAnalysis(models.Model):
    """Model for storing bias analysis results"""
    BIAS_CHOICES = [
        ('left', 'Left'),
        ('center-left', 'Center-Left'),
        ('center', 'Center'),
        ('center-right', 'Center-Right'),
        ('right', 'Right'),
        ('unknown', 'Unknown'),
    ]
    
    article = models.OneToOneField(NewsArticle, on_delete=models.CASCADE, related_name='bias_analysis')
    political_leaning = models.CharField(max_length=20, choices=BIAS_CHOICES, default='unknown')
    bias_score = models.FloatField()  # -1.0 (far left) to 1.0 (far right)
    confidence = models.FloatField()  # 0.0 to 1.0
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Bias Analysis for {self.article.title}"

class SentimentAnalysis(models.Model):
    """Model for storing sentiment analysis results"""
    article = models.OneToOneField(NewsArticle, on_delete=models.CASCADE, related_name='sentiment_analysis')
    sentiment_score = models.FloatField()  # -1.0 (negative) to 1.0 (positive)
    positive_score = models.FloatField()  # 0.0 to 1.0
    negative_score = models.FloatField()  # 0.0 to 1.0
    neutral_score = models.FloatField()  # 0.0 to 1.0
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Sentiment Analysis for {self.article.title}"

class FactCheckResult(models.Model):
    """Model for storing fact-checking results"""
    RATING_CHOICES = [
        ('true', 'True'),
        ('mostly_true', 'Mostly True'),
        ('half_true', 'Half True'),
        ('mostly_false', 'Mostly False'),
        ('false', 'False'),
        ('pants_on_fire', 'Pants on Fire'),
        ('unverified', 'Unverified'),
    ]
    
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='fact_checks')
    claim = models.TextField()  # The specific claim being fact-checked
    rating = models.CharField(max_length=20, choices=RATING_CHOICES, default='unverified')
    explanation = models.TextField()  # Explanation of the fact-check result
    sources = models.TextField(blank=True)  # Sources used to verify the claim
    checked_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Fact Check for claim: {self.claim[:50]}..."

class MisinformationAlert(models.Model):
    """Model for tracking trending misinformation"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    related_articles = models.ManyToManyField(NewsArticle, related_name='misinformation_alerts')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    detected_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    resolution_details = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-detected_at']
    
    def __str__(self):
        return self.title
