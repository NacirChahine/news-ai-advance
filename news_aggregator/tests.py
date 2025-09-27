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

    def test_threading_depth_limit(self):
        from news_aggregator.models import Comment
        parent = Comment.objects.create(article=self.article, user=self.user, content='p')
        c1 = Comment.objects.create(article=self.article, user=self.user, parent=parent, content='r1')
        c2 = Comment.objects.create(article=self.article, user=self.user, parent=c1, content='r2')
        c3 = Comment.objects.create(article=self.article, user=self.user, parent=c2, content='r3')
        c4 = Comment.objects.create(article=self.article, user=self.user, parent=c3, content='r4')
        self.assertLessEqual(c4.depth, Comment.MAX_DEPTH)

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
