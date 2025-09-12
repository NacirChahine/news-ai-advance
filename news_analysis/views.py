from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from news_aggregator.models import NewsArticle, UserSavedArticle
from .models import BiasAnalysis, SentimentAnalysis, FactCheckResult, MisinformationAlert, LogicalFallacy, LogicalFallacyDetection
from .utils import analyze_sentiment, extract_named_entities, calculate_readability_score, extract_main_topics

def misinformation_tracker(request):
    """View to display the misinformation tracker dashboard"""
    # Check if we should show resolved alerts
    show_resolved = request.GET.get('show_resolved', '0') == '1'
    # Get active alerts
    active_alerts = MisinformationAlert.objects.filter(is_active=True).order_by('-severity', '-detected_at')

    # Get recently resolved alerts if requested
    resolved_alerts = []
    if show_resolved:
        resolved_alerts = MisinformationAlert.objects.filter(
            is_active=False
        ).order_by('-resolved_at')[:10]

    # Count alerts by severity
    critical_count = MisinformationAlert.objects.filter(severity='critical', is_active=True).count()
    high_count = MisinformationAlert.objects.filter(severity='high', is_active=True).count()
    medium_count = MisinformationAlert.objects.filter(severity='medium', is_active=True).count()
    low_count = MisinformationAlert.objects.filter(severity='low', is_active=True).count()

    context = {
        'active_alerts': active_alerts,
        'resolved_alerts': resolved_alerts,
        'show_resolved': show_resolved,
        'critical_count': critical_count,
        'high_count': high_count,
        'medium_count': medium_count,
        'low_count': low_count,
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


def article_analysis(request, article_id):
    """Comprehensive view to display all analysis for a specific article"""
    article = get_object_or_404(NewsArticle, pk=article_id)

    # Get analysis data if it exists
    try:
        bias_analysis = BiasAnalysis.objects.get(article=article)
    except BiasAnalysis.DoesNotExist:
        bias_analysis = None

    try:
        sentiment_analysis = SentimentAnalysis.objects.get(article=article)
    except SentimentAnalysis.DoesNotExist:
        sentiment_analysis = None

    # Get fact checks if they exist
    fact_checks = FactCheckResult.objects.filter(article=article)

    # Check if user has saved this article
    is_saved = False
    if request.user.is_authenticated:
        is_saved = UserSavedArticle.objects.filter(user=request.user, article=article).exists()

    # Get related articles (same source, similar topics)
    related_articles = NewsArticle.objects.filter(
        Q(source=article.source) |
        Q(title__icontains=article.title.split()[0]) |
        Q(title__icontains=article.title.split()[-1])
    ).exclude(id=article.id).distinct()[:5]

    # Get related misinformation alerts (active or any?)
    related_alerts = article.misinformation_alerts.filter(is_active=True)

    context = {
        'article': article,
        'bias_analysis': bias_analysis,
        'sentiment_analysis': sentiment_analysis,
        'fact_checks': fact_checks,
        'is_saved': is_saved,
        'related_articles': related_articles,
        'misinformation_alerts': related_alerts,
    }
    return render(request, 'news_analysis/article_analysis.html', context)


def alert_detail(request, alert_id):
    """View to return alert details for AJAX requests"""
    alert = get_object_or_404(MisinformationAlert, pk=alert_id)

    context = {
        'alert': alert,
    }
    return render(request, 'news_analysis/alert_detail.html', context)



def fallacies_reference(request):
    """Public reference page listing logical fallacies."""
    fallacies = LogicalFallacy.objects.all().order_by('name').annotate(num_detections=Count('detections'))
    context = {
        'fallacies': fallacies,
    }
    return render(request, 'news_analysis/fallacies.html', context)
