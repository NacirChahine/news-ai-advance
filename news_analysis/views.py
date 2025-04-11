from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from news_aggregator.models import NewsArticle
from .models import BiasAnalysis, SentimentAnalysis, FactCheckResult, MisinformationAlert

def misinformation_tracker(request):
    """View to display the misinformation tracker dashboard"""
    # Get active misinformation alerts
    alerts = MisinformationAlert.objects.filter(is_active=True).order_by('-detected_at')
    
    context = {
        'alerts': alerts,
    }
    return render(request, 'news_analysis/misinformation_tracker.html', context)

def bias_analysis(request, article_id):
    """View to display bias analysis for a specific article"""
    article = get_object_or_404(NewsArticle, pk=article_id)
    
    # Check if bias analysis exists, or redirect to article detail
    try:
        bias_analysis = article.bias_analysis
    except BiasAnalysis.DoesNotExist:
        return redirect('news_aggregator:article_detail', article_id=article.id)
    
    context = {
        'article': article,
        'bias_analysis': bias_analysis,
    }
    return render(request, 'news_analysis/bias_analysis.html', context)

def sentiment_analysis(request, article_id):
    """View to display sentiment analysis for a specific article"""
    article = get_object_or_404(NewsArticle, pk=article_id)
    
    # Check if sentiment analysis exists, or redirect to article detail
    try:
        sentiment_analysis = article.sentiment_analysis
    except SentimentAnalysis.DoesNotExist:
        return redirect('news_aggregator:article_detail', article_id=article.id)
    
    context = {
        'article': article,
        'sentiment_analysis': sentiment_analysis,
    }
    return render(request, 'news_analysis/sentiment_analysis.html', context)

def fact_check(request, article_id):
    """View to display fact check results for a specific article"""
    article = get_object_or_404(NewsArticle, pk=article_id)
    
    # Get all fact checks for this article
    fact_checks = article.fact_checks.all()
    
    if not fact_checks.exists():
        return redirect('news_aggregator:article_detail', article_id=article.id)
    
    context = {
        'article': article,
        'fact_checks': fact_checks,
    }
    return render(request, 'news_analysis/fact_check.html', context)
