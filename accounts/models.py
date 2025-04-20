from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import random
import string
from datetime import timedelta

class UserProfile(models.Model):
    """Extended user profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    preferred_sources = models.ManyToManyField('news_aggregator.NewsSource', blank=True, related_name='preferred_by')

    def __str__(self):
        return f"{self.user.username}'s profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile instance when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile instance when the User is saved"""
    instance.profile.save()

class UserPreferences(models.Model):
    """User preferences for news content and analysis"""
    POLITICAL_FILTER_CHOICES = [
        ('all', 'Show All'),
        ('balanced', 'Balanced Mix'),
        ('neutral_only', 'Neutral Sources Only'),
        ('diverse', 'Diverse Viewpoints'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    political_filter = models.CharField(max_length=15, choices=POLITICAL_FILTER_CHOICES, default='balanced')
    enable_fact_check = models.BooleanField(default=True)
    enable_bias_analysis = models.BooleanField(default=True)
    enable_sentiment_analysis = models.BooleanField(default=True)
    receive_misinformation_alerts = models.BooleanField(default=True)
    daily_digest_email = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s preferences"

@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Create a UserPreferences instance when a new User is created"""
    if created:
        UserPreferences.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_preferences(sender, instance, **kwargs):
    """Save the UserPreferences instance when the User is saved"""
    try:
        instance.preferences.save()
    except UserPreferences.DoesNotExist:
        UserPreferences.objects.create(user=instance)

class PasswordResetOTP(models.Model):
    """Model to store OTP for password reset"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.username}"

    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        return not self.is_used and self.expires_at > timezone.now()

    @classmethod
    def generate_otp(cls, user, expiry_minutes=10):
        """Generate a new OTP for the given user"""
        # Generate a 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))

        # Calculate expiry time
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        # Create and return the OTP object
        return cls.objects.create(
            user=user,
            otp=otp,
            expires_at=expires_at
        )
