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
from .models import PasswordResetOTP

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

    context = {
        'user': user,
        'profile': profile,
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

    # Get sources for filter dropdown
    from news_aggregator.models import NewsSource
    sources = NewsSource.objects.all()

    # Paginate results
    from django.core.paginator import Paginator
    paginator = Paginator(saved_articles, 10)  # Show 10 saved articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'saved_articles': page_obj,
        'sources': sources,
        'date_filter': date_filter,
        'source_filter': source_filter,
        'sort_by': sort_by,
        'search_query': search_query,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
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
