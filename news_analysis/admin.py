from django.contrib import admin
from .models import BiasAnalysis, SentimentAnalysis, FactCheckResult, MisinformationAlert

@admin.register(BiasAnalysis)
class BiasAnalysisAdmin(admin.ModelAdmin):
    list_display = ('article', 'political_leaning', 'bias_score', 'confidence', 'analyzed_at')
    list_filter = ('political_leaning', 'analyzed_at')
    search_fields = ('article__title',)

@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    list_display = ('article', 'sentiment_score', 'positive_score', 'negative_score', 'analyzed_at')
    list_filter = ('analyzed_at',)
    search_fields = ('article__title',)

@admin.register(FactCheckResult)
class FactCheckResultAdmin(admin.ModelAdmin):
    list_display = ('article', 'claim', 'rating', 'checked_at')
    list_filter = ('rating', 'checked_at')
    search_fields = ('article__title', 'claim', 'explanation')

@admin.register(MisinformationAlert)
class MisinformationAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'is_active', 'detected_at')
    list_filter = ('severity', 'is_active', 'detected_at')
    search_fields = ('title', 'description')
