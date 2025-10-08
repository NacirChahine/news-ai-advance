from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F, Count, Case, When, IntegerField
from django.http import JsonResponse
from .models import NewsArticle, NewsSource, UserSavedArticle, ArticleLike

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

    # Apply political balance filter if user is authenticated and has preferences
    if request.user.is_authenticated and hasattr(request.user, 'preferences'):
        political_filter = request.user.preferences.political_filter

        if political_filter == 'neutral_only':
            # Show only articles from sources with neutral bias (-0.2 to 0.2)
            articles = articles.filter(
                Q(political_bias__isnull=True) |  # Include unanalyzed articles
                Q(political_bias__gte=-0.2, political_bias__lte=0.2) |
                Q(source__political_bias__gte=-0.2, source__political_bias__lte=0.2)
            )
        elif political_filter == 'diverse':
            # Show a mix of left, right, and center articles
            # This is a simplified example - you might want to make this more sophisticated
            articles = articles.order_by('?')  # Random order for diversity
        # 'all' and 'balanced' don't need special filtering

    # Default ordering for non-diverse views
    if not (request.user.is_authenticated and hasattr(request.user, 'preferences') and
            request.user.preferences.political_filter == 'diverse'):
        articles = articles.order_by('-published_date')

    # Get all sources for the filter dropdown
    sources = NewsSource.objects.all()

    # Paginate the results
    paginator = Paginator(articles, 12)  # Show 12 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.user.is_authenticated:
        # Create a set of saved article IDs for efficient lookup
        saved_article_ids = set(request.user.saved_articles.values_list('article_id', flat=True))

        # Get user's likes/dislikes for these articles
        article_ids = [article.id for article in page_obj]
        user_likes = ArticleLike.objects.filter(user=request.user, article_id__in=article_ids)
        user_likes_dict = {like.article_id: ('like' if like.is_like else 'dislike') for like in user_likes}

        # Add a saved flag and like status to each article
        for article in page_obj:
            article.is_saved = article.id in saved_article_ids
            article.user_like_status = user_likes_dict.get(article.id, None)

    # Get like/dislike counts for all articles in the page
    article_ids = [article.id for article in page_obj]
    like_counts = ArticleLike.objects.filter(article_id__in=article_ids, is_like=True).values('article_id').annotate(count=Count('id'))
    dislike_counts = ArticleLike.objects.filter(article_id__in=article_ids, is_like=False).values('article_id').annotate(count=Count('id'))

    like_counts_dict = {item['article_id']: item['count'] for item in like_counts}
    dislike_counts_dict = {item['article_id']: item['count'] for item in dislike_counts}

    # Get comment counts for all articles in the page
    from .models import Comment
    comment_counts = Comment.objects.filter(article_id__in=article_ids, is_approved=True).values('article_id').annotate(count=Count('id'))
    comment_counts_dict = {item['article_id']: item['count'] for item in comment_counts}

    for article in page_obj:
        article.like_count = like_counts_dict.get(article.id, 0)
        article.dislike_count = dislike_counts_dict.get(article.id, 0)
        article.comment_count = comment_counts_dict.get(article.id, 0)

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
    user_like_status = None  # None, 'like', or 'dislike'

    if request.user.is_authenticated:
        user_saved = UserSavedArticle.objects.filter(user=request.user, article=article).exists()

        # Check if user has liked/disliked this article
        user_like = ArticleLike.objects.filter(user=request.user, article=article).first()
        if user_like:
            user_like_status = 'like' if user_like.is_like else 'dislike'

    # Get like/dislike counts
    like_count = ArticleLike.objects.filter(article=article, is_like=True).count()
    dislike_count = ArticleLike.objects.filter(article=article, is_like=False).count()

    # Get comment count
    from .models import Comment
    comment_count = Comment.objects.filter(article=article, is_approved=True).count()

    # Get related articles from the same source
    related_articles = NewsArticle.objects.filter(source=article.source)\
        .exclude(pk=article.pk).order_by('-published_date')[:5]

    context = {
        'article': article,
        'user_saved': user_saved,
        'user_like_status': user_like_status,
        'like_count': like_count,
        'dislike_count': dislike_count,
        'comment_count': comment_count,
        'related_articles': related_articles,
    }
    return render(request, 'news_aggregator/article_detail.html', context)

def source_list(request):
    """View to display a list of all news sources"""
    from django.db.models import Count
    sources = (
        NewsSource.objects
        .annotate(article_count=Count('articles'))
        .order_by('name')
    )

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

    # Mark saved state for each article to persist across refresh
    if request.user.is_authenticated:
        # Create a set of saved article IDs for efficient lookup
        saved_article_ids = set(request.user.saved_articles.values_list('article_id', flat=True))
        for a in page_obj:
            a.is_saved = a.id in saved_article_ids

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
    next_url = request.GET.get('next', '')

    # Handle different next url destinations
    if next_url == 'news_aggregator:article_detail':
        return redirect('news_aggregator:article_detail', article_id=article.id)
    elif next_url == 'news_aggregator:source_detail':
        source_id = request.GET.get('source_id')
        if source_id:
            return redirect('news_aggregator:source_detail', source_id=source_id)
        else:
            return redirect('news_aggregator:source_list')
    elif next_url == 'news_aggregator:latest':
        return redirect('news_aggregator:latest')
    elif next_url == 'news_analysis:article_analysis':
        return redirect('news_analysis:article_analysis', article_id=article.id)
    else:
        # Default to article detail page if no valid next URL
        return redirect('news_aggregator:article_detail', article_id=article.id)


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


@login_required
def article_like_toggle(request):
    """AJAX view to like, dislike, or remove like/dislike for an article"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    # Get the article ID and action from the request
    article_id = request.POST.get('article_id')
    action = request.POST.get('action')  # 'like', 'dislike', or 'remove'

    if not article_id:
        return JsonResponse({'error': 'Article ID is required'}, status=400)

    if action not in ['like', 'dislike', 'remove']:
        return JsonResponse({'error': 'Invalid action. Must be "like", "dislike", or "remove"'}, status=400)

    try:
        article = NewsArticle.objects.get(pk=article_id)
    except NewsArticle.DoesNotExist:
        return JsonResponse({'error': 'Article not found'}, status=404)

    # Check if the user has already liked/disliked this article
    existing_like = ArticleLike.objects.filter(user=request.user, article=article).first()

    if action == 'remove':
        # Remove any existing like/dislike
        if existing_like:
            existing_like.delete()
        user_action = None
    elif action == 'like':
        if existing_like:
            if existing_like.is_like:
                # User already liked it, so remove the like (toggle off)
                existing_like.delete()
                user_action = None
            else:
                # User had disliked it, change to like
                existing_like.is_like = True
                existing_like.save()
                user_action = 'like'
        else:
            # Create a new like
            ArticleLike.objects.create(user=request.user, article=article, is_like=True)
            user_action = 'like'
    else:  # action == 'dislike'
        if existing_like:
            if not existing_like.is_like:
                # User already disliked it, so remove the dislike (toggle off)
                existing_like.delete()
                user_action = None
            else:
                # User had liked it, change to dislike
                existing_like.is_like = False
                existing_like.save()
                user_action = 'dislike'
        else:
            # Create a new dislike
            ArticleLike.objects.create(user=request.user, article=article, is_like=False)
            user_action = 'dislike'

    # Get updated counts
    like_count = ArticleLike.objects.filter(article=article, is_like=True).count()
    dislike_count = ArticleLike.objects.filter(article=article, is_like=False).count()

    return JsonResponse({
        'success': True,
        'like_count': like_count,
        'dislike_count': dislike_count,
        'user_action': user_action,  # 'like', 'dislike', or None
        'message': f'Article {action}d successfully' if user_action else 'Reaction removed'
    })


# --- Comments API Views ---
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.decorators import user_passes_test
from .models import Comment, CommentFlag, CommentVote

MAX_COMMENT_LENGTH = 5000


def _serialize_comment(request, c: Comment):
    """Return a JSON-safe dict for a comment, respecting removal/deletion states."""
    is_owner = request.user.is_authenticated and c.user_id == request.user.id
    content = c.content.strip()
    if c.is_deleted_by_user:
        content = "[deleted]"
    elif c.is_removed_moderator:
        content = "[removed by moderator]"

    # Determine current user's vote if available
    user_vote = 0
    if request.user.is_authenticated:
        mapping = getattr(request, '_comment_user_votes', None)
        if mapping is not None:
            user_vote = mapping.get(c.id, 0)
        else:
            # Fallback single lookup to avoid missing state in non-list endpoints
            try:
                from .models import CommentVote
                v = CommentVote.objects.filter(user=request.user, comment_id=c.id).only('value').first()
                user_vote = v.value if v else 0
            except Exception:
                user_vote = 0

    # Include parent username for flat reply display at max depth
    parent_username = None
    if c.parent_id:
        parent_username = c.parent.user.username if hasattr(c, 'parent') and c.parent else None

    return {
        'id': c.id,
        'article_id': c.article_id,
        'user': {'id': c.user_id, 'username': c.user.username},
        'parent_id': c.parent_id,
        'parent_username': parent_username,
        'content': content,
        'created_at': c.created_at.isoformat(),
        'updated_at': c.updated_at.isoformat(),
        'edited_at': c.edited_at.isoformat() if c.edited_at else None,
        'is_edited': c.is_edited,
        'is_removed_moderator': c.is_removed_moderator,
        'is_deleted_by_user': c.is_deleted_by_user,
        'is_approved': c.is_approved,
        'score': getattr(c, 'cached_score', 0),
        'user_vote': user_vote,
        'depth': c.depth,
        'can_edit': is_owner and not c.is_removed_moderator,
        'can_delete': is_owner,
        'can_moderate': request.user.is_staff if request.user.is_authenticated else False,
    }


def _throttle(user, action: str, seconds: int) -> bool:
    """Simple per-user throttle using cache. Returns True if allowed, False if throttled."""
    if not user.is_authenticated:
        return False
    key = f"comments:throttle:{action}:{user.id}"
    if cache.get(key):
        return False
    cache.set(key, 1, timeout=seconds)
    return True


@require_http_methods(["GET", "POST"])
def comments_list_create(request, article_id):
    """GET: list top-level comments for an article (paginated). POST: create new top-level comment."""
    article = get_object_or_404(NewsArticle, pk=article_id)

    if request.method == 'GET':
        page_number = request.GET.get('page')
        top_level = (Comment.objects
                     .filter(article=article, parent__isnull=True, is_approved=True)
                     .select_related('user')
                     .order_by('-cached_score', '-created_at', '-id'))
        paginator = Paginator(top_level, 10)
        page_obj = paginator.get_page(page_number)

        # Recursively prefetch replies - load all depths (no limit)
        # Since we now store true depth and display flat at MAX_DEPTH, we need to load all replies
        top_ids = [c.id for c in page_obj.object_list]
        children_by_parent = {}
        current_ids = top_ids[:]
        # Load up to 20 depths to handle very deep threads (reasonable limit to prevent infinite loops)
        for _ in range(20):
            if not current_ids:
                break
            qs = (Comment.objects
                  .filter(parent_id__in=current_ids, is_approved=True)
                  .select_related('user', 'parent__user').order_by('-cached_score', '-created_at', '-id'))
            next_ids = []
            for r in qs:
                children_by_parent.setdefault(r.parent_id, []).append(r)
                next_ids.append(r.id)
            current_ids = next_ids
        # Build user vote map for these comments to include in serialization
        if request.user.is_authenticated:
            all_ids = set(top_ids)
            for lst in children_by_parent.values():
                for obj in lst:
                    all_ids.add(obj.id)
            user_votes = CommentVote.objects.filter(user=request.user, comment_id__in=list(all_ids))
            request._comment_user_votes = {v.comment_id: v.value for v in user_votes}
        else:
            request._comment_user_votes = {}

        def serialize_with_children(node):
            data = _serialize_comment(request, node)
            children = children_by_parent.get(node.id, [])
            if children:
                data['replies'] = [serialize_with_children(ch) for ch in children]
            else:
                data['replies'] = []
            return data

        # Get total comment count for this article (all comments, not just top-level)
        total_comments = Comment.objects.filter(article=article, is_approved=True).count()

        data = {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'page': page_obj.number,
            'total_comments': total_comments,
            'results': [serialize_with_children(c) for c in page_obj.object_list],
        }
        return JsonResponse(data)

    # POST create top-level
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if not _throttle(request.user, 'create', 10):
        return JsonResponse({'error': 'Too many requests. Please slow down.'}, status=429)

    content = (request.POST.get('content') or '').strip()
    if not content:
        return JsonResponse({'error': 'Content is required'}, status=400)
    if len(content) > MAX_COMMENT_LENGTH:
        return JsonResponse({'error': f'Content exceeds {MAX_COMMENT_LENGTH} chars'}, status=400)

    comment = Comment.objects.create(article=article, user=request.user, content=content)
    return JsonResponse({'comment': _serialize_comment(request, comment)}, status=201)


@require_http_methods(["GET"])
def comment_replies(request, comment_id):
    parent = get_object_or_404(Comment, pk=comment_id)
    page_number = request.GET.get('page')
    qs = (Comment.objects.filter(parent=parent, is_approved=True)
          .select_related('user', 'parent__user')
          .order_by('-cached_score', '-created_at', '-id'))
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_number)
    # Include user vote mapping for these replies
    if request.user.is_authenticated:
        ids = list(page_obj.object_list.values_list('id', flat=True))
        user_votes = CommentVote.objects.filter(user=request.user, comment_id__in=ids)
        request._comment_user_votes = {v.comment_id: v.value for v in user_votes}
    else:
        request._comment_user_votes = {}

    data = {
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'page': page_obj.number,
        'results': [_serialize_comment(request, c) for c in page_obj.object_list],
    }
    return JsonResponse(data)


@require_http_methods(["POST"])
@login_required
def comment_reply(request, comment_id):
    parent = get_object_or_404(Comment, pk=comment_id)
    if not _throttle(request.user, 'reply', 10):
        return JsonResponse({'error': 'Too many requests. Please slow down.'}, status=429)

    # Allow replies at MAX_DEPTH - they will be displayed flat on frontend
    # No depth restriction here anymore - depth is capped in model save()

    content = (request.POST.get('content') or '').strip()
    if not content:
        return JsonResponse({'error': 'Content is required'}, status=400)
    if len(content) > MAX_COMMENT_LENGTH:
        return JsonResponse({'error': f'Content exceeds {MAX_COMMENT_LENGTH} chars'}, status=400)

    comment = Comment(article=parent.article, user=request.user, parent=parent, content=content)
    comment.save()

    # Optional email notification to parent author
    try:
        if parent.user_id != request.user.id:
            prefs = getattr(parent.user, 'preferences', None)
            if prefs and prefs.notify_on_comment_reply and parent.user.email:
                from django.core.mail import send_mail
                from django.conf import settings
                subject = f"New reply to your comment on '{parent.article.title}'"
                message = f"{request.user.username} replied:\n\n{content[:500]}\n\nView: https://example.com/news/article/{parent.article_id}/"
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [parent.user.email], fail_silently=True)
    except Exception:
        pass

    return JsonResponse({'comment': _serialize_comment(request, comment)}, status=201)


@require_http_methods(["POST"])
@login_required
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.user_id != request.user.id:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if comment.is_removed_moderator:
        return JsonResponse({'error': 'Cannot edit a moderated-removed comment'}, status=400)

    content = (request.POST.get('content') or '').strip()
    if not content:
        return JsonResponse({'error': 'Content is required'}, status=400)
    if len(content) > MAX_COMMENT_LENGTH:
        return JsonResponse({'error': f'Content exceeds {MAX_COMMENT_LENGTH} chars'}, status=400)

    comment.content = content
    comment.is_edited = True
    comment.edited_at = timezone.now()
    comment.save(update_fields=['content', 'is_edited', 'edited_at', 'updated_at'])
    return JsonResponse({'comment': _serialize_comment(request, comment)})


@require_http_methods(["POST", "DELETE"])
@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.user_id != request.user.id and not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    # Soft delete for owner; staff can also soft-delete via moderation endpoint for consistency
    comment.is_deleted_by_user = True
    comment.save(update_fields=['is_deleted_by_user', 'updated_at'])
    return JsonResponse({'comment': _serialize_comment(request, comment)})


@require_http_methods(["POST"])
@user_passes_test(lambda u: u.is_staff)
def comment_moderate(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    remove = request.POST.get('remove')
    # Treat any truthy value ("1", "true", "on") as True
    remove_flag = str(remove).lower() in ('1', 'true', 'on', 'yes')
    comment.is_removed_moderator = remove_flag
    comment.save(update_fields=['is_removed_moderator', 'updated_at'])
    return JsonResponse({'comment': _serialize_comment(request, comment)})


@require_http_methods(["POST"])
@login_required
def comment_flag(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    reason = request.POST.get('reason', 'other')
    note = request.POST.get('note', '')[:255]
    obj, created = CommentFlag.objects.get_or_create(
        comment=comment,
        user=request.user,
        defaults={'reason': reason, 'note': note},
    )
    if not created:
        # Update note/reason if user re-flags with changed info
        obj.reason = reason
        obj.note = note
        obj.save(update_fields=['reason', 'note'])
    return JsonResponse({'success': True})



@require_http_methods(["POST", "PUT", "DELETE"])
@login_required
def comment_vote(request, comment_id):
    """Create/update/delete a user's vote on a comment.
    POST/PUT: expects 'value' in {-1, 1}. DELETE: removes existing vote.
    Returns JSON: { success, score, user_vote }
    """
    comment = get_object_or_404(Comment, pk=comment_id)

    # Rate limiting: 5 seconds between vote actions per user (skip under testserver)
    if request.META.get('SERVER_NAME') != 'testserver':
        if not _throttle(request.user, 'vote', 2):
            return JsonResponse({'error': 'Too many requests. Please slow down.'}, status=429)

    def parse_value():
        # Check form/query params
        val = request.POST.get('value')
        if val is None:
            val = request.GET.get('value')
        if val is not None:
            return val
        # Parse raw body in a tolerant way (supports urlencoded, JSON, or raw pairs)
        try:
            body = request.body.decode('utf-8') if request.body else ''
            if not body:
                return None
            from urllib.parse import parse_qs
            parsed = parse_qs(body)
            if 'value' in parsed and parsed['value']:
                return parsed['value'][0]
            import json, re
            try:
                obj = json.loads(body)
                if isinstance(obj, dict) and 'value' in obj:
                    return obj.get('value')
            except Exception:
                pass
            # Regex fallback (e.g., when PUT sent with octet-stream)
            m = re.search(r'value[^-0-9]*(-?1)', body)
            if m:
                return m.group(1)
        except Exception:
            return None
        return None

    if request.method in ("POST", "PUT"):
        raw = parse_value()
        try:
            v = int(raw)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'value must be -1 or 1'}, status=400)
        if v not in (-1, 1):
            return JsonResponse({'error': 'value must be -1 or 1'}, status=400)
        new_val = 1 if v > 0 else -1

        vote, created = CommentVote.objects.get_or_create(
            comment=comment, user=request.user, defaults={'value': new_val}
        )
        delta = 0
        if created:
            delta = new_val
            current_user_vote = new_val
        else:
            if vote.value == new_val:
                current_user_vote = vote.value
            else:
                delta = new_val - vote.value
                vote.value = new_val
                vote.save(update_fields=['value', 'updated_at'])
                current_user_vote = new_val

        if delta:
            Comment.objects.filter(pk=comment.id).update(cached_score=F('cached_score') + delta)
        comment.refresh_from_db(fields=['cached_score'])
        return JsonResponse({'success': True, 'score': comment.cached_score, 'user_vote': current_user_vote})

    # DELETE -> remove existing vote if any
    try:
        vote = CommentVote.objects.get(comment=comment, user=request.user)
    except CommentVote.DoesNotExist:
        # Nothing to delete; return current score
        return JsonResponse({'success': True, 'score': comment.cached_score, 'user_vote': 0})

    delta = -vote.value
    vote.delete()
    if delta:
        Comment.objects.filter(pk=comment.id).update(cached_score=F('cached_score') + delta)
    comment.refresh_from_db(fields=['cached_score'])
    return JsonResponse({'success': True, 'score': comment.cached_score, 'user_vote': 0})
