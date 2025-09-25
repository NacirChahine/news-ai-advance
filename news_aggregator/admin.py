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


from .models import Comment, CommentFlag

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'article', 'user', 'parent', 'depth', 'is_removed_moderator', 'is_deleted_by_user', 'created_at')
    list_filter = ('is_removed_moderator', 'is_deleted_by_user', 'created_at', 'article')
    search_fields = ('content', 'user__username', 'article__title')
    autocomplete_fields = ('article', 'user', 'parent')
    actions = ['mark_removed', 'restore_removed']

    def mark_removed(self, request, queryset):
        queryset.update(is_removed_moderator=True)
    mark_removed.short_description = 'Mark selected comments as removed by moderator'

    def restore_removed(self, request, queryset):
        queryset.update(is_removed_moderator=False)
    restore_removed.short_description = 'Restore selected comments (remove moderator flag)'

@admin.register(CommentFlag)
class CommentFlagAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'user', 'reason', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('comment__content', 'user__username')
