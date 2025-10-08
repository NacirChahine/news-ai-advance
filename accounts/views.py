from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from news_aggregator.models import UserSavedArticle
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import PasswordResetOTP, UserPreferences

def signup(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('accounts:login')
    else:
        form = UserCreationForm()

    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def profile(request):
    """User profile view"""
    user = request.user
    profile = user.profile
    # Comment statistics
    from news_aggregator.models import Comment, ArticleLike
    comment_count = Comment.objects.filter(user=user).count()

    # Liked articles count
    liked_articles_count = ArticleLike.objects.filter(user=user, is_like=True).count()

    # Preferred sources
    preferred_sources = profile.preferred_sources.all()

    context = {
        'user': user,
        'profile': profile,
        'comment_count': comment_count,
        'liked_articles_count': liked_articles_count,
        'preferred_sources': preferred_sources,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def preferences(request):
    """User preferences view"""
    user = request.user
    preferences = user.preferences

    if request.method == 'POST':
        # Update preferences based on form submission
        preferences.enable_fact_check = 'enable_fact_check' in request.POST
        preferences.enable_bias_analysis = 'enable_bias_analysis' in request.POST
        preferences.enable_sentiment_analysis = 'enable_sentiment_analysis' in request.POST
        preferences.enable_logical_fallacy_analysis = 'enable_logical_fallacy_analysis' in request.POST

        preferences.enable_key_insights = 'enable_key_insights' in request.POST
        preferences.enable_summary_display = 'enable_summary_display' in request.POST

        # Comments settings
        preferences.show_comments = 'show_comments' in request.POST
        preferences.notify_on_comment_reply = 'notify_on_comment_reply' in request.POST

        # Only update political_filter if it's not disabled
        if 'political_filter' in request.POST:
            preferences.political_filter = request.POST.get('political_filter', 'balanced')

        preferences.save()
        messages.success(request, 'Your preferences have been updated successfully!')
        return redirect('accounts:preferences')

    context = {
        'user': user,
        'preferences': preferences,
    }
    return render(request, 'accounts/preferences.html', context)

@login_required
@require_POST
def auto_save_preferences(request):
    """AJAX endpoint for auto-saving user preferences"""
    try:
        data = json.loads(request.body)
        user = request.user
        preferences = user.preferences

        # Update the specific preference that was changed
        field_name = data.get('field')
        field_value = data.get('value')

        if field_name == 'enable_fact_check':
            preferences.enable_fact_check = field_value
        elif field_name == 'enable_bias_analysis':
            preferences.enable_bias_analysis = field_value
        elif field_name == 'enable_sentiment_analysis':
            preferences.enable_sentiment_analysis = field_value
        elif field_name == 'enable_logical_fallacy_analysis':
            preferences.enable_logical_fallacy_analysis = field_value
        elif field_name == 'enable_key_insights':
            preferences.enable_key_insights = field_value
        elif field_name == 'enable_summary_display':
            preferences.enable_summary_display = field_value
        elif field_name == 'show_comments':
            preferences.show_comments = field_value
        elif field_name == 'notify_on_comment_reply':
            preferences.notify_on_comment_reply = field_value
        elif field_name == 'public_profile':
            preferences.public_profile = field_value
        elif field_name == 'political_filter':
            preferences.political_filter = field_value
        elif field_name == 'receive_misinformation_alerts':
            preferences.receive_misinformation_alerts = field_value
        else:
            return JsonResponse({'success': False, 'error': 'Invalid field name'})

        preferences.save()
        return JsonResponse({'success': True, 'message': 'Preference saved successfully'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def liked_articles(request):
    """View for user's liked articles"""
    user = request.user
    from news_aggregator.models import ArticleLike, Comment
    from django.core.paginator import Paginator

    # Get all articles the user has liked
    liked_article_objs = ArticleLike.objects.filter(
        user=user, is_like=True
    ).select_related(
        'article', 'article__source', 'article__bias_analysis', 'article__sentiment_analysis'
    ).order_by('-created_at')

    # Extract articles and annotate with necessary data
    articles = []
    saved_article_ids = set(user.saved_articles.values_list('article_id', flat=True))

    # Get preferred source IDs
    try:
        preferred_source_ids = set(user.profile.preferred_sources.values_list('id', flat=True))
    except:
        preferred_source_ids = set()

    for liked_obj in liked_article_objs:
        article = liked_obj.article

        # Annotate article with additional data
        article.is_saved = article.id in saved_article_ids
        article.user_like_status = 'like'  # We know they liked it
        article.like_count = ArticleLike.objects.filter(article=article, is_like=True).count()
        article.dislike_count = ArticleLike.objects.filter(article=article, is_like=False).count()
        article.comment_count = Comment.objects.filter(article=article, is_approved=True).count()
        article.is_from_preferred_source = article.source.id in preferred_source_ids

        articles.append(article)

    # Paginate the results
    paginator = Paginator(articles, 12)  # Show 12 articles per page (3x4 grid)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_count': len(articles),
    }
    return render(request, 'accounts/liked_articles.html', context)


@login_required
def saved_articles(request):
    """View for user's saved articles"""
    user = request.user

    # Get filter parameters
    date_filter = request.GET.get('date_filter', 'all')
    source_filter = request.GET.get('source_filter', 'all')
    sort_by = request.GET.get('sort_by', 'saved_newest')
    search_query = request.GET.get('search_query', '')

    # Start with all saved articles for this user
    saved_articles = UserSavedArticle.objects.filter(user=user)

    # Apply date filter
    from django.utils import timezone
    import datetime
    if date_filter == 'today':
        today = timezone.now().date()
        saved_articles = saved_articles.filter(saved_at__date=today)
    elif date_filter == 'week':
        week_ago = timezone.now() - datetime.timedelta(days=7)
        saved_articles = saved_articles.filter(saved_at__gte=week_ago)
    elif date_filter == 'month':
        month_ago = timezone.now() - datetime.timedelta(days=30)
        saved_articles = saved_articles.filter(saved_at__gte=month_ago)
    elif date_filter == 'quarter':
        quarter_ago = timezone.now() - datetime.timedelta(days=90)
        saved_articles = saved_articles.filter(saved_at__gte=quarter_ago)
    elif date_filter == 'year':
        year_ago = timezone.now() - datetime.timedelta(days=365)
        saved_articles = saved_articles.filter(saved_at__gte=year_ago)

    # Apply source filter
    if source_filter != 'all':
        saved_articles = saved_articles.filter(article__source_id=source_filter)

    # Apply search filter
    if search_query:
        from django.db.models import Q
        saved_articles = saved_articles.filter(
            Q(article__title__icontains=search_query) |
            Q(article__content__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # Apply sorting
    if sort_by == 'saved_newest':
        saved_articles = saved_articles.order_by('-saved_at')
    elif sort_by == 'saved_oldest':
        saved_articles = saved_articles.order_by('saved_at')
    elif sort_by == 'published_newest':
        saved_articles = saved_articles.order_by('-article__published_date')
    elif sort_by == 'published_oldest':
        saved_articles = saved_articles.order_by('article__published_date')
    elif sort_by == 'alphabetical':
        saved_articles = saved_articles.order_by('article__title')

    # Select related fields for efficiency
    saved_articles = saved_articles.select_related(
        'article', 'article__source', 'article__bias_analysis', 'article__sentiment_analysis'
    )

    # Get sources for filter dropdown
    from news_aggregator.models import NewsSource, ArticleLike, Comment
    sources = NewsSource.objects.all()

    # Get preferred source IDs
    try:
        preferred_source_ids = set(user.profile.preferred_sources.values_list('id', flat=True))
    except:
        preferred_source_ids = set()

    # Get user's likes/dislikes
    article_ids = [saved.article.id for saved in saved_articles]
    user_likes = ArticleLike.objects.filter(user=user, article_id__in=article_ids)
    user_likes_dict = {like.article_id: ('like' if like.is_like else 'dislike') for like in user_likes}

    # Annotate articles with additional data
    articles = []
    for saved_obj in saved_articles:
        article = saved_obj.article

        # Annotate article with additional data
        article.is_saved = True  # We know it's saved
        article.user_like_status = user_likes_dict.get(article.id, None)
        article.like_count = ArticleLike.objects.filter(article=article, is_like=True).count()
        article.dislike_count = ArticleLike.objects.filter(article=article, is_like=False).count()
        article.comment_count = Comment.objects.filter(article=article, is_approved=True).count()
        article.is_from_preferred_source = article.source.id in preferred_source_ids

        articles.append(article)

    # Paginate results
    from django.core.paginator import Paginator
    paginator = Paginator(articles, 12)  # Show 12 saved articles per page (3x4 grid)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'sources': sources,
        'date_filter': date_filter,
        'source_filter': source_filter,
        'sort_by': sort_by,
        'search_query': search_query,
        'is_paginated': paginator.num_pages > 1,
        'total_count': len(articles),
    }
    return render(request, 'accounts/saved_articles.html', context)


@login_required
def update_saved_notes(request):
    """View to update notes for a saved article"""
    if request.method != 'POST':
        return redirect('accounts:saved_articles')

    saved_id = request.POST.get('saved_id')
    notes = request.POST.get('notes', '')

    try:
        saved_article = UserSavedArticle.objects.get(id=saved_id, user=request.user)
        saved_article.notes = notes
        saved_article.save()
        messages.success(request, 'Notes updated successfully.')
    except UserSavedArticle.DoesNotExist:
        messages.error(request, 'Saved article not found.')

    return redirect('accounts:saved_articles')


@login_required
def delete_saved(request):
    """View to delete a saved article"""
    if request.method != 'POST':
        return redirect('accounts:saved_articles')

    saved_id = request.POST.get('saved_id')

    try:
        saved_article = UserSavedArticle.objects.get(id=saved_id, user=request.user)
        saved_article.delete()
        messages.success(request, 'Article removed from saved list.')
    except UserSavedArticle.DoesNotExist:
        messages.error(request, 'Saved article not found.')

    return redirect('accounts:saved_articles')


@login_required
def bulk_delete_saved(request):
    """View to delete multiple saved articles at once"""
    if request.method != 'POST':
        return redirect('accounts:saved_articles')

    selected_articles = request.POST.getlist('selected_articles')

    if not selected_articles:
        messages.warning(request, 'No articles were selected.')
        return redirect('accounts:saved_articles')

    # Delete selected articles
    deleted_count = UserSavedArticle.objects.filter(
        id__in=selected_articles,
        user=request.user
    ).delete()[0]

    messages.success(request, f'{deleted_count} articles removed from saved list.')
    return redirect('accounts:saved_articles')

@login_required
def edit_profile(request):
    """View for editing user profile"""
    user = request.user
    user_profile = user.profile

    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        bio = request.POST.get('bio', '')

        # Update user information
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        # Update profile information
        user_profile.bio = bio

        # Handle profile picture upload
        if request.FILES.get('avatar'):
            # Delete the old profile picture if it exists
            if user_profile.profile_picture:
                try:
                    default_storage.delete(user_profile.profile_picture.path)
                except:
                    pass  # File might not exist

            # Save the new profile picture
            avatar = request.FILES['avatar']
            filename = f"profile_pics/{user.username}_{avatar.name}"
            user_profile.profile_picture = default_storage.save(filename, avatar)

        user_profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')

    context = {
        'user': user,
        'profile': user_profile,
    }
    return render(request, 'accounts/edit_profile.html', context)

def logout_view(request):
    """Custom logout view that supports both GET and POST requests"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')

@login_required
def change_password(request):
    """View for changing user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update session to prevent user from being logged out
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/password_change.html', {'form': form})

def forgot_password(request):
    """View for initiating password reset process"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        User = get_user_model()

        # Check if user with this email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return render(request, 'accounts/forgot_password.html')

        # Generate OTP
        otp_obj = PasswordResetOTP.generate_otp(user)

        # Send email with OTP
        subject = 'Password Reset OTP'
        message = f'Your OTP for password reset is: {otp_obj.otp}\n\nThis OTP will expire in 10 minutes.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        try:
            send_mail(subject, message, from_email, recipient_list)
            messages.success(request, 'An OTP has been sent to your email address.')
            return redirect('accounts:verify_otp', user_id=user.id)
        except Exception as e:
            messages.error(request, f'Failed to send OTP email. Please try again later. Error: {str(e)}')
            return render(request, 'accounts/forgot_password.html')

    return render(request, 'accounts/forgot_password.html')

def verify_otp(request, user_id):
    """View for verifying OTP"""
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()

        # Find the latest valid OTP for this user
        try:
            otp_obj = PasswordResetOTP.objects.filter(
                user=user,
                otp=otp,
                is_used=False
            ).latest('created_at')

            if otp_obj.is_valid():
                # Mark OTP as used
                otp_obj.is_used = True
                otp_obj.save()

                # Redirect to password reset page
                return redirect('accounts:reset_password', user_id=user.id, otp_id=otp_obj.id)
            else:
                messages.error(request, 'OTP has expired. Please request a new one.')
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'accounts/verify_otp.html', {'user_id': user_id})

def reset_password(request, user_id, otp_id):
    """View for setting new password after OTP verification"""
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    otp_obj = get_object_or_404(PasswordResetOTP, id=otp_id, user=user, is_used=True)

    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SetPasswordForm(user)

    return render(request, 'accounts/reset_password.html', {'form': form})


@login_required
def comment_history(request):
    """List the user's comment history with pagination and simple stats."""
    from news_aggregator.models import Comment
    qs = (Comment.objects.filter(user=request.user)
          .select_related('article')
          .order_by('-created_at'))
    from django.core.paginator import Paginator
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Stats
    from django.utils import timezone
    from datetime import timedelta
    total_count = qs.count()
    last_30 = qs.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()

    context = {
        'page_obj': page_obj,
        'total_count': total_count,
        'last_30_days': last_30,
    }
    return render(request, 'accounts/comment_history.html', context)


def public_user_profile(request, username):
    """Public user profile view"""
    from django.core.paginator import Paginator
    from news_aggregator.models import Comment, ArticleLike, NewsArticle
    from datetime import timedelta
    from django.utils import timezone

    User = get_user_model()
    profile_user = get_object_or_404(User, username=username)

    # Check if profile is public - MUST happen before loading any profile data
    # Allow user to view their own profile regardless of privacy setting
    if request.user != profile_user:
        try:
            preferences = profile_user.preferences
            # Explicitly check if public_profile is False
            if preferences.public_profile is False:
                return render(request, 'accounts/public_profile.html', {
                    'profile_user': profile_user,
                    'is_private': True,
                })
        except UserPreferences.DoesNotExist:
            # If preferences don't exist, default to public
            pass

    # Get user profile
    try:
        user_profile = profile_user.profile
    except:
        user_profile = None

    # Get statistics
    total_comments = Comment.objects.filter(user=profile_user, is_approved=True).count()
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_comments = Comment.objects.filter(
        user=profile_user,
        is_approved=True,
        created_at__gte=thirty_days_ago
    ).count()

    # Get liked articles (paginated)
    liked_article_ids = ArticleLike.objects.filter(
        user=profile_user,
        is_like=True
    ).values_list('article_id', flat=True)

    liked_articles = NewsArticle.objects.filter(
        id__in=liked_article_ids
    ).select_related('source').order_by('-published_date')

    liked_paginator = Paginator(liked_articles, 10)
    liked_page = request.GET.get('liked_page', 1)
    liked_page_obj = liked_paginator.get_page(liked_page)

    # Get user comments (paginated)
    comments = Comment.objects.filter(
        user=profile_user,
        is_approved=True,
        is_deleted_by_user=False,
        is_removed_moderator=False
    ).select_related('article', 'article__source').order_by('-created_at')

    comments_paginator = Paginator(comments, 10)
    comments_page = request.GET.get('comments_page', 1)
    comments_page_obj = comments_paginator.get_page(comments_page)

    # Get preferred sources
    preferred_sources = user_profile.preferred_sources.all() if user_profile else []

    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'is_private': False,
        'is_own_profile': request.user == profile_user,
        'total_comments': total_comments,
        'recent_comments': recent_comments,
        'liked_page_obj': liked_page_obj,
        'comments_page_obj': comments_page_obj,
        'member_since': profile_user.date_joined,
        'preferred_sources': preferred_sources,
    }

    return render(request, 'accounts/public_profile.html', context)


@login_required
@require_POST
def toggle_preferred_source(request):
    """Toggle a news source as preferred/not preferred for the current user"""
    try:
        data = json.loads(request.body)
        source_id = data.get('source_id')

        if not source_id:
            return JsonResponse({'success': False, 'error': 'Source ID is required'}, status=400)

        from news_aggregator.models import NewsSource
        source = get_object_or_404(NewsSource, pk=source_id)
        user_profile = request.user.profile

        # Toggle the preference
        if source in user_profile.preferred_sources.all():
            user_profile.preferred_sources.remove(source)
            is_preferred = False
            message = f'{source.name} removed from preferred sources'
        else:
            user_profile.preferred_sources.add(source)
            is_preferred = True
            message = f'{source.name} added to preferred sources'

        return JsonResponse({
            'success': True,
            'is_preferred': is_preferred,
            'message': message
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def upload_profile_picture(request):
    """Upload a profile picture for the current user"""
    try:
        if 'profile_picture' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)

        file = request.FILES['profile_picture']

        # Validate file type
        valid_types = ['image/jpeg', 'image/png', 'image/gif']
        if file.content_type not in valid_types:
            return JsonResponse({'success': False, 'error': 'Invalid file type'}, status=400)

        # Validate file size (2MB max)
        if file.size > 2 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File size must be less than 2MB'}, status=400)

        # Delete old profile picture if exists
        profile = request.user.profile
        if profile.profile_picture:
            profile.profile_picture.delete(save=False)

        # Save new profile picture
        profile.profile_picture = file
        profile.save()

        return JsonResponse({
            'success': True,
            'avatar_url': profile.profile_picture.url,
            'message': 'Profile picture updated successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def remove_profile_picture(request):
    """Remove the profile picture for the current user"""
    try:
        profile = request.user.profile
        if profile.profile_picture:
            profile.profile_picture.delete(save=True)
            return JsonResponse({
                'success': True,
                'message': 'Profile picture removed successfully'
            })
        else:
            return JsonResponse({'success': False, 'error': 'No profile picture to remove'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
