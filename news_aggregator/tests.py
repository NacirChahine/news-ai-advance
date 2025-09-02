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
