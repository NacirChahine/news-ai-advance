from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from news_aggregator.models import UserSavedArticle

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
    
    context = {
        'user': user,
        'preferences': preferences,
    }
    return render(request, 'accounts/preferences.html', context)

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

def logout_view(request):
    """Custom logout view that supports both GET and POST requests"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')
