import re
from typing import List
from django.db.models import Q
from news_aggregator.models import NewsArticle
from .models import MisinformationAlert


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    text = text.lower()
    # simple tokenization
    return re.findall(r"[a-z0-9']+", text)


def simple_keyword_overlap(a_tokens: List[str], b_tokens: List[str]) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    a_set = set(a_tokens)
    b_set = set(b_tokens)
    inter = a_set & b_set
    union = a_set | b_set
    return len(inter) / max(1, len(union))


def find_related_alerts_for_article(article: NewsArticle, min_overlap: float = 0.06, limit: int = 5) -> List[MisinformationAlert]:
    """
    Heuristic matcher: find active alerts with token overlap to article title/content.
    min_overlap is a light threshold; tune as needed.
    """
    title_tokens = tokenize(article.title)
    content_tokens = tokenize(article.content[:8000])  # cap for performance

    best: List[tuple[MisinformationAlert, float]] = []

    alerts = MisinformationAlert.objects.filter(is_active=True)
    for alert in alerts:
        alert_tokens = tokenize(alert.title) + tokenize(alert.description)
        score_title = simple_keyword_overlap(title_tokens, alert_tokens)
        score_content = simple_keyword_overlap(content_tokens, alert_tokens)
        score = max(score_title, score_content)
        if score >= min_overlap:
            best.append((alert, score))

    best.sort(key=lambda x: x[1], reverse=True)
    return [a for a, _ in best[:limit]]

