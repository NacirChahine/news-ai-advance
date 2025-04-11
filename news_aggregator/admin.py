from django.contrib import admin
from .models import NewsSource, NewsArticle, UserSavedArticle

@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'reliability_score', 'created_at')
    list_filter = ('reliability_score',)
    search_fields = ('name', 'url', 'description')

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_date', 'is_analyzed', 'is_summarized')
    list_filter = ('source', 'published_date', 'is_analyzed', 'is_summarized')
    search_fields = ('title', 'content', 'author')
    date_hierarchy = 'published_date'

@admin.register(UserSavedArticle)
class UserSavedArticleAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('user__username', 'article__title', 'notes')
