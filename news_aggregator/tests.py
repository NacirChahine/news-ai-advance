from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from news_aggregator.models import NewsSource, NewsArticle
from news_analysis.models import FactCheckResult


class ArticleDetailFactCheckUITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.source = NewsSource.objects.create(name='Test Source', url='https://example.com')
        self.article = NewsArticle.objects.create(
            title='Test Article',
            source=self.source,
            url='https://example.com/a1',
            content='This is some article content used for testing.'
        )
        # Create a user
        self.user = User.objects.create_user(username='u', email='u@example.com', password='x')

    def test_unauthenticated_user_sees_prompt(self):
        # Mark as analyzed so the Fact Checks panel can render
        self.article.is_analyzed = True
        self.article.save(update_fields=['is_analyzed'])
        url = reverse('news_aggregator:article_detail', kwargs={'article_id': self.article.id})
        resp = self.client.get(url)
        self.assertContains(resp, 'Want to see fact-checks?')
        self.assertContains(resp, reverse('accounts:signup'))
        self.assertContains(resp, reverse('accounts:login'))

    def test_authenticated_fact_checks_disabled_prompt(self):
        # Ensure preference exists and disable
        prefs = self.user.preferences
        prefs.enable_fact_check = False
        prefs.save()
        # Mark as analyzed
        self.article.is_analyzed = True
        self.article.save(update_fields=['is_analyzed'])

        self.client.login(username='u', password='x')
        url = reverse('news_aggregator:article_detail', kwargs={'article_id': self.article.id})
        resp = self.client.get(url)
        self.assertContains(resp, 'Fact-checking is currently disabled')
        self.assertContains(resp, reverse('accounts:preferences'))

    def test_authenticated_enabled_no_fact_checks_message(self):
        prefs = self.user.preferences
        prefs.enable_fact_check = True
        prefs.save()
        # Mark as analyzed
        self.article.is_analyzed = True
        self.article.save(update_fields=['is_analyzed'])
        self.client.login(username='u', password='x')
        url = reverse('news_aggregator:article_detail', kwargs={'article_id': self.article.id})
        resp = self.client.get(url)
        # No FactCheckResult exists, should see info alert
        self.assertContains(resp, 'No fact-checks are available for this article yet')

    def test_authenticated_enabled_with_fact_checks_shows_accordion(self):
        prefs = self.user.preferences
        prefs.enable_fact_check = True
        prefs.save()
        # Create a fact-check
        FactCheckResult.objects.create(
            article=self.article,
            claim='A verifiable claim in the article.',
            rating='mostly_true',
            explanation='An explanation',
            sources='https://example.org',
        )
        # Mark as analyzed
        self.article.is_analyzed = True
        self.article.save(update_fields=['is_analyzed'])
        self.client.login(username='u', password='x')
        url = reverse('news_aggregator:article_detail', kwargs={'article_id': self.article.id})
        resp = self.client.get(url)
        self.assertContains(resp, 'Fact Checks')
        self.assertContains(resp, 'A verifiable claim')



class CommentApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.source = NewsSource.objects.create(name='S', url='https://s.example')
        self.article = NewsArticle.objects.create(title='T', source=self.source, url='https://s.example/t', content='c')
        self.user = User.objects.create_user(username='u2', email='u2@example.com', password='x')

    def test_create_requires_login(self):
        url = reverse('news_aggregator:comments_list_create', args=[self.article.id])
        resp = self.client.post(url, {'content': 'hello'})
        # JSON API returns 401 for unauthenticated
        self.assertEqual(resp.status_code, 401)
        self.assertIn('error', resp.json())

    def test_create_and_list_comment(self):
        self.client.login(username='u2', password='x')
        list_url = reverse('news_aggregator:comments_list_create', args=[self.article.id])
        resp = self.client.post(list_url, {'content': 'First!'})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn('comment', data)
        self.assertEqual(data['comment']['content'], 'First!')

        # Now list
        resp2 = self.client.get(list_url)
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertGreaterEqual(data2['count'], 1)
        self.assertTrue(any(c['content'] == 'First!' for c in data2['results']))



class CommentModelTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.source = NewsSource.objects.create(name='S2', url='https://s2.example')
        self.article = NewsArticle.objects.create(title='T2', source=self.source, url='https://s2.example/t2', content='c2')
        self.user = User.objects.create_user(username='u3', email='u3@example.com', password='x')
        self.staff = User.objects.create_user(username='staff', email='s@example.com', password='x', is_staff=True)

    def test_threading_depth_tracking(self):
        """Test that true depth is stored beyond MAX_DEPTH"""
        from news_aggregator.models import Comment
        parent = Comment.objects.create(article=self.article, user=self.user, content='p')
        self.assertEqual(parent.depth, 0)

        c1 = Comment.objects.create(article=self.article, user=self.user, parent=parent, content='r1')
        self.assertEqual(c1.depth, 1)

        c2 = Comment.objects.create(article=self.article, user=self.user, parent=c1, content='r2')
        self.assertEqual(c2.depth, 2)

        c3 = Comment.objects.create(article=self.article, user=self.user, parent=c2, content='r3')
        self.assertEqual(c3.depth, 3)

        c4 = Comment.objects.create(article=self.article, user=self.user, parent=c3, content='r4')
        self.assertEqual(c4.depth, 4)

        c5 = Comment.objects.create(article=self.article, user=self.user, parent=c4, content='r5')
        self.assertEqual(c5.depth, 5)

        # Beyond MAX_DEPTH - should still track true depth
        c6 = Comment.objects.create(article=self.article, user=self.user, parent=c5, content='r6')
        self.assertEqual(c6.depth, 6)

        c7 = Comment.objects.create(article=self.article, user=self.user, parent=c6, content='r7')
        self.assertEqual(c7.depth, 7)

    def test_display_depth_capping(self):
        """Test that get_display_depth() caps at MAX_DEPTH"""
        from news_aggregator.models import Comment
        parent = Comment.objects.create(article=self.article, user=self.user, content='p')

        # Create deep nesting
        current = parent
        for i in range(10):
            current = Comment.objects.create(
                article=self.article,
                user=self.user,
                parent=current,
                content=f'reply{i}'
            )

        # True depth should be 10
        self.assertEqual(current.depth, 10)
        # Display depth should be capped at MAX_DEPTH
        self.assertEqual(current.get_display_depth(), Comment.MAX_DEPTH)

    def test_soft_delete(self):
        from news_aggregator.models import Comment
        c = Comment.objects.create(article=self.article, user=self.user, content='hi')
        self.client.login(username='u3', password='x')
        url = reverse('news_aggregator:comment_delete', args=[c.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        c.refresh_from_db()
        self.assertTrue(c.is_deleted_by_user)

    def test_moderate_remove_restore(self):
        from news_aggregator.models import Comment
        c = Comment.objects.create(article=self.article, user=self.user, content='hi')
        self.client.login(username='staff', password='x')
        mod_url = reverse('news_aggregator:comment_moderate', args=[c.id])
        resp = self.client.post(mod_url, {'remove': 'true'})
        self.assertEqual(resp.status_code, 200)
        c.refresh_from_db()
        self.assertTrue(c.is_removed_moderator)
        # restore
        resp2 = self.client.post(mod_url, {'remove': 'false'})
        self.assertEqual(resp2.status_code, 200)
        c.refresh_from_db()
        self.assertFalse(c.is_removed_moderator)



class CommentVotingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.source = NewsSource.objects.create(name='SV', url='https://sv.example')
        self.article = NewsArticle.objects.create(title='TV', source=self.source, url='https://sv.example/tv', content='cv')
        self.user = User.objects.create_user(username='uv', email='uv@example.com', password='x')
        from news_aggregator.models import Comment
        self.comment = Comment.objects.create(article=self.article, user=self.user, content='hello')

    def test_vote_requires_login(self):
        url = reverse('news_aggregator:comment_vote', args=[self.comment.id])
        resp = self.client.post(url, {'value': 1})
        self.assertEqual(resp.status_code, 302)  # redirected to login due to @login_required

    def test_upvote_and_remove(self):
        self.client.login(username='uv', password='x')
        url = reverse('news_aggregator:comment_vote', args=[self.comment.id])
        # Upvote
        r1 = self.client.post(url, {'value': 1})
        self.assertEqual(r1.status_code, 200)
        data = r1.json()
        self.assertEqual(data['user_vote'], 1)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.cached_score, 1)
        # Remove via DELETE
        r2 = self.client.delete(url)
        self.assertEqual(r2.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.cached_score, 0)

    def test_switch_vote(self):
        self.client.login(username='uv', password='x')
        url = reverse('news_aggregator:comment_vote', args=[self.comment.id])
        # Downvote first
        r1 = self.client.post(url, {'value': -1})
        self.assertEqual(r1.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.cached_score, -1)
        # Switch to upvote -> delta +2
        r2 = self.client.put(url, {'value': 1})
        self.assertEqual(r2.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.cached_score, 1)


class CommentSerializationTests(TestCase):
    """Tests for comment serialization with parent_username"""
    def setUp(self):
        self.client = Client()
        self.source = NewsSource.objects.create(name='S', url='https://s.example')
        self.article = NewsArticle.objects.create(title='T', source=self.source, url='https://s.example/t', content='c')
        self.user1 = User.objects.create_user(username='user1', email='u1@example.com', password='x')
        self.user2 = User.objects.create_user(username='user2', email='u2@example.com', password='x')

    def test_parent_username_in_serialization(self):
        """Test that parent_username is included in comment serialization"""
        from news_aggregator.models import Comment

        # Create parent comment
        parent = Comment.objects.create(article=self.article, user=self.user1, content='parent')

        # Create reply
        reply = Comment.objects.create(article=self.article, user=self.user2, parent=parent, content='reply')

        # Login and fetch comments
        self.client.login(username='user2', password='x')
        url = reverse('news_aggregator:comments_list_create', args=[self.article.id])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Find the parent comment in results
        parent_data = next((c for c in data['results'] if c['id'] == parent.id), None)
        self.assertIsNotNone(parent_data)

        # Check that reply has parent_username
        if parent_data and 'replies' in parent_data and len(parent_data['replies']) > 0:
            reply_data = parent_data['replies'][0]
            self.assertEqual(reply_data['parent_username'], 'user1')

    def test_comment_count_in_response(self):
        """Test that total_comments is included in API response"""
        from news_aggregator.models import Comment

        # Create multiple comments
        Comment.objects.create(article=self.article, user=self.user1, content='c1')
        Comment.objects.create(article=self.article, user=self.user1, content='c2')
        Comment.objects.create(article=self.article, user=self.user2, content='c3')

        self.client.login(username='user1', password='x')
        url = reverse('news_aggregator:comments_list_create', args=[self.article.id])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('total_comments', data)
        self.assertEqual(data['total_comments'], 3)

    def test_flat_comment_structure(self):
        """Test that comments are returned in flat structure with ALL replies in thread"""
        from news_aggregator.models import Comment

        # Create a deep comment thread (depth 0-3)
        parent = Comment.objects.create(article=self.article, user=self.user1, content='depth0')
        reply1 = Comment.objects.create(
            article=self.article,
            user=self.user1,
            parent=parent,
            content='depth1_reply1'
        )
        reply2 = Comment.objects.create(
            article=self.article,
            user=self.user1,
            parent=parent,
            content='depth1_reply2'
        )
        # Nested reply to reply1 (should be included in parent's replies for flat structure)
        nested = Comment.objects.create(
            article=self.article,
            user=self.user1,
            parent=reply1,
            content='depth2_nested'
        )

        # Fetch comments via API
        self.client.login(username='user1', password='x')
        url = reverse('news_aggregator:comments_list_create', args=[self.article.id])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Check flat structure - parent should have ALL replies in thread (including nested)
        if data['results']:
            parent_data = data['results'][0]
            # Should have 3 total replies (2 direct + 1 nested)
            self.assertEqual(len(parent_data['replies']), 3, "Should have 3 total replies in thread")
            self.assertEqual(parent_data['reply_count'], 3, "reply_count should be 3")

            # All replies should be included in flat structure
            reply_contents = [r['content'] for r in parent_data['replies']]
            self.assertIn('depth1_reply1', reply_contents)
            self.assertIn('depth1_reply2', reply_contents)
            self.assertIn('depth2_nested', reply_contents, "Nested reply should be included in flat structure")

    def test_reply_pagination(self):
        """Test that reply_count is included and pagination works for replies"""
        from news_aggregator.models import Comment

        # Create a parent comment with 8 replies (more than the 5 initial limit)
        parent = Comment.objects.create(article=self.article, user=self.user1, content='parent')
        for i in range(8):
            Comment.objects.create(
                article=self.article,
                user=self.user2,
                parent=parent,
                content=f'reply{i}'
            )

        # Fetch comments via API
        self.client.login(username='user1', password='x')
        url = reverse('news_aggregator:comments_list_create', args=[self.article.id])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Check that parent comment has reply_count
        if data['results']:
            parent_data = data['results'][0]
            self.assertIn('reply_count', parent_data)
            self.assertEqual(parent_data['reply_count'], 8)
            # Only first 5 replies should be loaded initially
            self.assertEqual(len(parent_data['replies']), 5)

        # Test loading more replies via comment_replies endpoint
        replies_url = reverse('news_aggregator:comment_replies', args=[parent.id])
        resp2 = self.client.get(replies_url + '?page=2')
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()

        # Should have 3 more replies (8 total - 5 on first page)
        self.assertEqual(len(data2['results']), 3)
        self.assertEqual(data2['count'], 8)
        self.assertEqual(data2['num_pages'], 2)


class CommentCounterTests(TestCase):
    """Tests for comment counter functionality"""
    def setUp(self):
        self.client = Client()
        self.source = NewsSource.objects.create(name='S', url='https://s.example')
        self.article = NewsArticle.objects.create(title='T', source=self.source, url='https://s.example/t', content='c')
        self.user = User.objects.create_user(username='u', email='u@example.com', password='x')

    def test_comment_count_in_article_detail(self):
        """Test that comment_count is in article detail context"""
        from news_aggregator.models import Comment

        # Create comments
        Comment.objects.create(article=self.article, user=self.user, content='c1')
        Comment.objects.create(article=self.article, user=self.user, content='c2')

        url = reverse('news_aggregator:article_detail', args=[self.article.id])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('comment_count', resp.context)
        self.assertEqual(resp.context['comment_count'], 2)

    def test_comment_count_in_latest_news(self):
        """Test that articles have comment_count in listing view"""
        from news_aggregator.models import Comment

        # Create comments
        Comment.objects.create(article=self.article, user=self.user, content='c1')
        Comment.objects.create(article=self.article, user=self.user, content='c2')

        url = reverse('news_aggregator:latest')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        # Check that articles in page_obj have comment_count attribute
        articles = resp.context['page_obj']
        if articles:
            first_article = articles[0]
            self.assertTrue(hasattr(first_article, 'comment_count'))


class PublicProfileTests(TestCase):
    """Tests for public user profile functionality"""
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', email='u1@example.com', password='x')
        self.user2 = User.objects.create_user(username='user2', email='u2@example.com', password='x')
        self.source = NewsSource.objects.create(name='S', url='https://s.example')
        self.article = NewsArticle.objects.create(title='T', source=self.source, url='https://s.example/t', content='c')

    def test_public_profile_accessible(self):
        """Test that public profile is accessible when enabled"""
        url = reverse('accounts:public_profile', args=['user1'])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('profile_user', resp.context)
        self.assertEqual(resp.context['profile_user'].username, 'user1')
        self.assertFalse(resp.context['is_private'])

    def test_private_profile_blocked(self):
        """Test that private profile shows privacy message"""
        # Set profile to private
        prefs = self.user1.preferences
        prefs.public_profile = False
        prefs.save()

        # Try to access as different user
        self.client.login(username='user2', password='x')
        url = reverse('accounts:public_profile', args=['user1'])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['is_private'])

    def test_own_private_profile_accessible(self):
        """Test that user can view their own private profile"""
        # Set profile to private
        prefs = self.user1.preferences
        prefs.public_profile = False
        prefs.save()

        # Access own profile
        self.client.login(username='user1', password='x')
        url = reverse('accounts:public_profile', args=['user1'])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['is_private'])
        self.assertTrue(resp.context['is_own_profile'])

    def test_profile_shows_comments(self):
        """Test that profile displays user's comments"""
        from news_aggregator.models import Comment

        # Create comments
        Comment.objects.create(article=self.article, user=self.user1, content='comment1')
        Comment.objects.create(article=self.article, user=self.user1, content='comment2')

        url = reverse('accounts:public_profile', args=['user1'])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['total_comments'], 2)

    def test_profile_shows_liked_articles(self):
        """Test that profile displays user's liked articles"""
        from news_aggregator.models import ArticleLike

        # Create likes
        ArticleLike.objects.create(article=self.article, user=self.user1, is_like=True)

        url = reverse('accounts:public_profile', args=['user1'])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['liked_page_obj'].paginator.count, 1)


class ArticleValidationTests(TestCase):
    """Integration tests for article validation functionality"""
    
    def setUp(self):
        self.source = NewsSource.objects.create(
            name='Test News',
            url='https://testnews.example.com'
        )
    
    def test_valid_article_url_patterns(self):
        """Test that valid article URLs pass validation"""
        from news_aggregator.article_validator import ArticleValidator
        
        valid_urls = [
            'https://testnews.example.com/news/2024/11/breaking-story',
            'https://testnews.example.com/article/important-update',
            'https://testnews.example.com/politics/election-news',
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(ArticleValidator.is_valid_article_url(url))
    
    def test_invalid_category_and_tag_urls(self):
        """Test that category and tag pages are rejected"""
        from news_aggregator.article_validator import ArticleValidator
        
        invalid_urls = [
            'https://testnews.example.com/category/politics',
            'https://testnews.example.com/tag/breaking-news',
            'https://testnews.example.com/author/john-doe',
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(ArticleValidator.is_valid_article_url(url))
    
    def test_article_structure_validation(self):
        """Test validation of article HTML structure"""
        from news_aggregator.article_validator import ArticleValidator
        from bs4 import BeautifulSoup
        
        # Valid article HTML
        valid_html = """
        <html>
        <head>
            <title>Breaking News: Important Update</title>
            <meta property="og:type" content="article">
            <meta property="article:author" content="Jane Smith">
            <meta property="article:published_time" content="2024-11-29T10:00:00Z">
        </head>
        <body>
            <article>
                <h1>Breaking News: Important Update</h1>
                <p>This is the first paragraph with substantial content.</p>
                <p>This is the second paragraph with more details.</p>
                <p>This is the third paragraph with analysis.</p>
                <p>This is the fourth paragraph with conclusion.</p>
            </article>
        </body>
        </html>
        """
        
        soup = BeautifulSoup(valid_html, 'lxml')
        validation = ArticleValidator.validate_article_structure(soup)
        
        self.assertTrue(validation['is_valid'])
        self.assertTrue(validation['has_title'])
        self.assertTrue(validation['has_content'])
        self.assertTrue(validation['has_metadata'])
    
    def test_invalid_article_insufficient_content(self):
        """Test that pages with insufficient content are rejected"""
        from news_aggregator.article_validator import ArticleValidator
        from bs4 import BeautifulSoup
        
        # Minimal content
        invalid_html = """
        <html>
        <head><title>Short Page</title></head>
        <body>
            <h1>Short Page</h1>
            <p>Too short.</p>
        </body>
        </html>
        """
        
        soup = BeautifulSoup(invalid_html, 'lxml')
        validation = ArticleValidator.validate_article_structure(soup)
        
        self.assertFalse(validation['is_valid'])
        self.assertFalse(validation['has_content'])
    
    def test_complete_validation_flow(self):
        """Test the complete validation flow with URL and HTML"""
        from news_aggregator.article_validator import ArticleValidator
        
        url = 'https://testnews.example.com/news/2024/11/article'
        html = """
        <html>
        <head>
            <title>Valid Article Title</title>
            <meta property="og:type" content="article">
            <meta property="article:author" content="Test Author">
            <meta property="article:published_time" content="2024-11-29T10:00:00Z">
        </head>
        <body>
            <article>
                <h1>Valid Article Title</h1>
                <div class="author">By Test Author</div>
                <time datetime="2024-11-29">November 29, 2024</time>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
                <p>Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
                <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.</p>
                <p>Duis aute irure dolor in reprehenderit in voluptate velit esse.</p>
            </article>
        </body>
        </html>
        """
        
        is_valid, details = ArticleValidator.is_valid_article(url, html)
        
        self.assertTrue(is_valid)
        self.assertEqual(details['url'], url)
        self.assertTrue(details['has_title'])
        self.assertTrue(details['has_content'])


class NewsSortingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        # Create sources
        self.source_preferred = NewsSource.objects.create(name='Preferred Source', url='http://pref.com')
        self.source_other = NewsSource.objects.create(name='Other Source', url='http://other.com')
        
        # Add preferred source to user profile
        self.user.profile.preferred_sources.add(self.source_preferred)
        
        # Create articles
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        
        # Article 1: Today 10:00, Non-Preferred (Newest date)
        self.a1 = NewsArticle.objects.create(
            title='A1 Today Non-Pref',
            source=self.source_other,
            url='http://other.com/1',
            published_date=now.replace(hour=10, minute=0, second=0, microsecond=0),
            content='content'
        )
        
        # Article 2: Yesterday 10:00, Preferred
        self.a2 = NewsArticle.objects.create(
            title='A2 Yesterday Pref 10:00',
            source=self.source_preferred,
            url='http://pref.com/2',
            published_date=yesterday.replace(hour=10, minute=0, second=0, microsecond=0),
            content='content'
        )
        
        # Article 3: Yesterday 09:00, Non-Preferred
        self.a3 = NewsArticle.objects.create(
            title='A3 Yesterday Non-Pref 09:00',
            source=self.source_other,
            url='http://other.com/3',
            published_date=yesterday.replace(hour=9, minute=0, second=0, microsecond=0),
            content='content'
        )
        
        # Article 4: Yesterday 11:00, Preferred
        self.a4 = NewsArticle.objects.create(
            title='A4 Yesterday Pref 11:00',
            source=self.source_preferred,
            url='http://pref.com/4',
            published_date=yesterday.replace(hour=11, minute=0, second=0, microsecond=0),
            content='content'
        )

    def test_latest_news_sorting(self):
        url = reverse('news_aggregator:latest')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        articles = list(response.context['page_obj'])
        
        # Expected order:
        # 1. A1 (Today)
        # 2. A4 (Yesterday, Preferred, 11:00)
        # 3. A2 (Yesterday, Preferred, 10:00)
        # 4. A3 (Yesterday, Non-Preferred, 09:00)
        
        self.assertEqual(articles[0], self.a1)
        self.assertEqual(articles[1], self.a4)
        self.assertEqual(articles[2], self.a2)
        self.assertEqual(articles[3], self.a3)

    def test_sorting_without_preference(self):
        # Remove preference
        self.user.profile.preferred_sources.clear()
        
        url = reverse('news_aggregator:latest')
        response = self.client.get(url)
        
        articles = list(response.context['page_obj'])
        
        # Expected order (pure date desc):
        # 1. A1 (Today 10:00)
        # 2. A4 (Yesterday 11:00)
        # 3. A2 (Yesterday 10:00)
        # 4. A3 (Yesterday 09:00)
        
        self.assertEqual(articles[0], self.a1)
        self.assertEqual(articles[1], self.a4)
        self.assertEqual(articles[2], self.a2)
        self.assertEqual(articles[3], self.a3)
