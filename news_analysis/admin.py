from django.contrib import admin, messages
from django.utils import timezone
from .models import BiasAnalysis, SentimentAnalysis, FactCheckResult, MisinformationAlert
from .email_utils import send_misinformation_alert_email

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
    list_display = ('title', 'severity', 'is_active', 'detected_at', 'related_count')
    list_filter = ('severity', 'is_active', 'detected_at')
    search_fields = ('title', 'description')
    actions = ['mark_resolved', 'mark_active', 'send_alert_email']

    def related_count(self, obj):
        return obj.related_articles.count()
    related_count.short_description = 'Related Articles'

    @admin.action(description='Mark selected alerts as resolved')
    def mark_resolved(self, request, queryset):
        updated = 0
        now = timezone.now()
        for alert in queryset:
            if alert.is_active:
                alert.is_active = False
                alert.resolved_at = now
                alert.save(update_fields=['is_active', 'resolved_at'])
                updated += 1
        self.message_user(request, f"Marked {updated} alert(s) as resolved.", level=messages.SUCCESS)

    @admin.action(description='Mark selected alerts as active')
    def mark_active(self, request, queryset):
        updated = 0
        for alert in queryset:
            if not alert.is_active:
                alert.is_active = True
                alert.resolved_at = None
                alert.save(update_fields=['is_active', 'resolved_at'])
                updated += 1
        self.message_user(request, f"Marked {updated} alert(s) as active.", level=messages.SUCCESS)

    @admin.action(description='Send alert email to opted-in users')
    def send_alert_email(self, request, queryset):
        sent_total = 0
        errors_total = []
        for alert in queryset:
            result = send_misinformation_alert_email(alert)
            sent_total += result.get('sent', 0)
            errors_total.extend(result.get('errors', []))
        if errors_total:
            self.message_user(request, f"Sent {sent_total} email(s) with errors: {', '.join(errors_total)}", level=messages.WARNING)
        else:
            self.message_user(request, f"Sent {sent_total} email(s) successfully.", level=messages.SUCCESS)
