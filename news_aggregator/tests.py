from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

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

    def test_deep_comment_loading(self):
        """Test that comments beyond depth 5 are loaded and serialized"""
        from news_aggregator.models import Comment

        # Create a deep comment thread (depth 0-7)
        parent = Comment.objects.create(article=self.article, user=self.user1, content='depth0')
        current = parent
        for i in range(1, 8):
            current = Comment.objects.create(
                article=self.article,
                user=self.user1,
                parent=current,
                content=f'depth{i}'
            )

        # Verify depths are stored correctly
        self.assertEqual(parent.depth, 0)
        self.assertEqual(current.depth, 7)

        # Fetch comments via API
        self.client.login(username='user1', password='x')
        url = reverse('news_aggregator:comments_list_create', args=[self.article.id])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Navigate through nested replies to find depth 7 comment
        def find_deepest(comment_data, current_depth=0):
            if not comment_data.get('replies'):
                return current_depth
            max_depth = current_depth
            for reply in comment_data['replies']:
                depth = find_deepest(reply, current_depth + 1)
                max_depth = max(max_depth, depth)
            return max_depth

        # Check that all depths are present in the response
        if data['results']:
            deepest = find_deepest(data['results'][0])
            self.assertEqual(deepest, 7, "All comment depths should be loaded")

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

        url = reverse('news_aggregator:latest_news')
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
