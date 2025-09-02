from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from news_aggregator.models import NewsArticle

@require_GET
def article_misinformation_alerts(request, article_id: int):
    try:
        article = NewsArticle.objects.get(pk=article_id)
    except NewsArticle.DoesNotExist:
        raise Http404()

    alerts = article.misinformation_alerts.filter(is_active=True).order_by('-detected_at')
    data = [
        {
            'id': a.id,
            'title': a.title,
            'severity': a.severity,
            'detected_at': a.detected_at.isoformat(),
        }
        for a in alerts
    ]
    return JsonResponse({'article_id': article.id, 'alerts': data})

