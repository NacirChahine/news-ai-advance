from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class NewsSource(models.Model):
    """Model for news sources (publications, websites, etc.)"""
    name = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='source_logos/', blank=True, null=True)
    reliability_score = models.FloatField(default=0.0)  # 0-100 score
    political_bias = models.FloatField(
        default=0.0,
        help_text='Average political bias score from -1 (left) to +1 (right)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class NewsArticle(models.Model):
    """Model for news articles collected from various sources"""
    title = models.CharField(max_length=255)
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='articles')
    url = models.URLField(unique=True)
    author = models.CharField(max_length=200, blank=True)
    published_date = models.DateTimeField(default=timezone.now)
    content = models.TextField()
    summary = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    # Political bias score (-1 to +1, where -1 is left, 0 is neutral, +1 is right)
    political_bias = models.FloatField(
        null=True,
        blank=True,
        help_text='Political bias score from -1 (left) to +1 (right)'
    )

    # Flags for processing status
    is_analyzed = models.BooleanField(default=False)
    is_summarized = models.BooleanField(default=False)

    class Meta:
        ordering = ['-published_date']

    def __str__(self):
        return self.title

class UserSavedArticle(models.Model):
    """Model for articles saved by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_articles')
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('user', 'article')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} - {self.article.title}"


# --- Comments ---

class Comment(models.Model):
    """Threaded comments on NewsArticle with moderation flags."""
    MAX_DEPTH = 5

    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    depth = models.PositiveSmallIntegerField(default=0)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    # Moderation/visibility
    is_removed_moderator = models.BooleanField(default=False)
    is_deleted_by_user = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [
            models.Index(fields=['article', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.article.title}"

    def save(self, *args, **kwargs):
        # Compute depth from parent
        if self.parent:
            self.depth = (self.parent.depth or 0) + 1
            if self.depth > self.MAX_DEPTH:
                # Cap depth to MAX_DEPTH (children beyond max will attach at max depth)
                self.depth = self.MAX_DEPTH
        else:
            self.depth = 0
        super().save(*args, **kwargs)


class CommentFlag(models.Model):
    """User reports/flags on comments for moderation."""
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('abuse', 'Abusive/Harassment'),
        ('hate', 'Hate Speech'),
        ('other', 'Other'),
    ]

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='flags')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_flags')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='other')
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')
        indexes = [
            models.Index(fields=['comment']),
        ]

    def __str__(self):
        return f"Flag by {self.user.username} on Comment #{self.comment_id} ({self.reason})"
