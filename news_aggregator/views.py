from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import NewsArticle, NewsSource, UserSavedArticle

def latest_news(request):
    """View to display the latest news articles with filters"""
    # Get filter parameters from request
    source_id = request.GET.get('source')
    search_query = request.GET.get('q')
    
    # Start with all articles
    articles = NewsArticle.objects.all()
    
    # Apply filters if provided
    if source_id:
        articles = articles.filter(source_id=source_id)
    if search_query:
        articles = articles.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
    
    # Get all sources for the filter dropdown
    sources = NewsSource.objects.all()
    
    # Paginate the results
    paginator = Paginator(articles, 12)  # Show 12 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'sources': sources,
        'selected_source': source_id,
        'search_query': search_query,
    }
    return render(request, 'news_aggregator/latest_news.html', context)

def article_detail(request, article_id):
    """View to display a single news article with analysis"""
    article = get_object_or_404(NewsArticle, pk=article_id)
    
    # Check if the user has saved this article
    user_saved = False
    if request.user.is_authenticated:
        user_saved = UserSavedArticle.objects.filter(user=request.user, article=article).exists()
    
    # Get related articles from the same source
    related_articles = NewsArticle.objects.filter(source=article.source)\
        .exclude(pk=article.pk).order_by('-published_date')[:5]
    
    context = {
        'article': article,
        'user_saved': user_saved,
        'related_articles': related_articles,
    }
    return render(request, 'news_aggregator/article_detail.html', context)

def source_list(request):
    """View to display a list of all news sources"""
    sources = NewsSource.objects.all().order_by('name')
    
    context = {
        'sources': sources,
    }
    return render(request, 'news_aggregator/source_list.html', context)

def source_detail(request, source_id):
    """View to display a single news source with its articles"""
    source = get_object_or_404(NewsSource, pk=source_id)
    
    # Get all articles from this source
    articles = source.articles.all().order_by('-published_date')
    
    # Paginate the results
    paginator = Paginator(articles, 12)  # Show 12 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'source': source,
        'page_obj': page_obj,
    }
    return render(request, 'news_aggregator/source_detail.html', context)

@login_required
def save_article(request, article_id):
    """View to save or unsave an article for the logged-in user"""
    article = get_object_or_404(NewsArticle, pk=article_id)
    
    # Check if the article is already saved
    saved_article = UserSavedArticle.objects.filter(user=request.user, article=article)
    
    if saved_article.exists():
        # If it exists, remove it (unsave)
        saved_article.delete()
        messages.success(request, f'Article "{article.title}" removed from your saved articles.')
    else:
        # If it doesn't exist, create it (save)
        UserSavedArticle.objects.create(user=request.user, article=article)
        messages.success(request, f'Article "{article.title}" saved to your collection.')
    
    # Redirect back to the referring page or article detail
    next_url = request.GET.get('next', 'news_aggregator:article_detail')
    if next_url == 'article_detail':
        return redirect('news_aggregator:article_detail', article_id=article.id)
    return redirect(next_url)


@login_required
def save_article_ajax(request):
    """AJAX view to save or unsave an article for the logged-in user"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    # Get the article ID from the request
    article_id = request.POST.get('article_id')
    if not article_id:
        return JsonResponse({'error': 'Article ID is required'}, status=400)
    
    try:
        article = NewsArticle.objects.get(pk=article_id)
    except NewsArticle.DoesNotExist:
        return JsonResponse({'error': 'Article not found'}, status=404)
    
    # Check if the article is already saved
    saved_article = UserSavedArticle.objects.filter(user=request.user, article=article)
    
    if saved_article.exists():
        # If it exists, remove it (unsave)
        saved_article.delete()
        return JsonResponse({'saved': False, 'message': 'Article removed from your saved list'})
    else:
        # If it doesn't exist, create it (save)
        UserSavedArticle.objects.create(user=request.user, article=article)
        return JsonResponse({'saved': True, 'message': 'Article saved to your collection'})
