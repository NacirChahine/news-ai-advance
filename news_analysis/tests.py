from django.test import TestCase, override_settings
from django.core import mail
from django.contrib.auth.models import User
from accounts.models import UserPreferences
from .models import MisinformationAlert
from .email_utils import get_opted_in_recipient_emails, send_misinformation_alert_email


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='test@example.com')
class MisinformationEmailTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='u1', email='u1@example.com', password='x')
        self.user2 = User.objects.create_user(username='u2', email='u2@example.com', password='x')
        self.user3 = User.objects.create_user(username='u3', email='', password='x')
        # Ensure preferences exist
        UserPreferences.objects.filter(user=self.user1).update(receive_misinformation_alerts=True)
        UserPreferences.objects.filter(user=self.user2).update(receive_misinformation_alerts=False)
        UserPreferences.objects.filter(user=self.user3).update(receive_misinformation_alerts=True)

        self.alert = MisinformationAlert.objects.create(
            title='Test Alert',
            description='Test description',
            severity='high',
            is_active=True,
        )

    def test_recipient_selection(self):
        emails = get_opted_in_recipient_emails()
        self.assertIn('u1@example.com', emails)
        self.assertNotIn('u2@example.com', emails)
        # user3 has no email
        self.assertNotIn('', emails)

    def test_send_alert_email_plaintext(self):
        result = send_misinformation_alert_email(self.alert)
        self.assertEqual(result['errors'], [])
        self.assertGreaterEqual(result['sent'], 1)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn('Misinformation Alert', message.subject)
        self.assertIn('Test Alert', message.body)

from django.test import TestCase

# Create your tests here.


from django.test import Client
from django.core.management import call_command
from news_aggregator.models import NewsSource, NewsArticle

class MisinformationIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.source = NewsSource.objects.create(name='Test Source', url='https://example.com')
        self.article = NewsArticle.objects.create(
            title='Big Health Claim Goes Viral',
            source=self.source,
            url='https://example.com/a1',
            content='A viral claim about health and wellness is circulating widely.',
        )
        self.alert = MisinformationAlert.objects.create(
            title='Viral Health Claim',
            description='A known misleading claim related to health.',
            severity='high',
            is_active=True,
        )

    def test_management_command_dry_run(self):
        call_command('send_misinformation_alerts', dry_run=True)
        # No emails should be sent during dry run
        self.assertEqual(len(mail.outbox), 0)

    def test_api_endpoint(self):
        # Attempt linking via analyze_articles
        call_command('analyze_articles', article_id=self.article.id, force=True)
        # API call
        resp = self.client.get(f"/analysis/api/articles/{self.article.id}/misinformation-alerts/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('alerts', data)
        # Ensure shows once linked
        self.alert.related_articles.add(self.article)
        resp = self.client.get(f"/analysis/api/articles/{self.article.id}/misinformation-alerts/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(len(data['alerts']), 1)

    def test_article_analysis_page_shows_alerts(self):
        self.alert.related_articles.add(self.article)
        resp = self.client.get(f"/analysis/article-analysis/{self.article.id}/")
        self.assertContains(resp, 'Misinformation Alerts')
        self.assertContains(resp, 'Viral Health Claim')


from unittest.mock import patch
from django.core.management import call_command
from news_aggregator.models import NewsArticle, NewsSource
from news_analysis.models import FactCheckResult
from news_analysis import utils as analysis_utils


class ClaimExtractionTests(TestCase):
    def setUp(self):
        self.content = (
            'The World Health Organization said on Monday that global life expectancy rose by 6 years since 2000. '
            'According to the report, more than 2.3 billion people were affected by respiratory illnesses in 2023. '
            'Experts estimated the cost at $1.2 trillion annually. "This is significant," said Dr. Smith.'
        )

    def test_extract_claims_returns_scored_sentences(self):
        claims = analysis_utils.extract_claims(self.content, max_claims=5)
        self.assertGreaterEqual(len(claims), 3)
        self.assertTrue(all(isinstance(c, str) and len(c) > 20 for c in claims))


class FactCheckPipelineTests(TestCase):
    def setUp(self):
        self.source = NewsSource.objects.create(name="Test Source", url="https://example.com")
        self.article = NewsArticle.objects.create(
            title="WHO: life expectancy rose by 6 years since 2000",
            source=self.source,
            url="https://example.com/article1",
            content=(
                'The World Health Organization said on Monday that global life expectancy rose by 6 years since 2000. '
                'According to the report, more than 2.3 billion people were affected by respiratory illnesses in 2023.'
            ),
        )

    @patch("news_analysis.management.commands.analyze_articles.spacy.load", autospec=True)
    @patch("news_analysis.utils.query_ollama")
    def test_analyze_articles_creates_fact_checks_with_llm(self, mock_ollama, mock_spacy_load):
        mock_spacy_load.return_value = object()  # Avoid downloading models
        mock_ollama.return_value = {
            "response": '{"rating":"mostly_true","confidence":0.78,"explanation":"Consistent with WHO data","sources":["https://www.who.int/"]}'
        }
        call_command("analyze_articles", article_id=self.article.id, force=True)
        fcs = FactCheckResult.objects.filter(article=self.article)
        self.assertGreaterEqual(fcs.count(), 1)
        fc = fcs.first()
        self.assertIn(fc.rating, [c[0] for c in FactCheckResult.RATING_CHOICES])
        self.assertIsNotNone(fc.last_verified)
        self.assertIsNotNone(fc.confidence)

    @patch("news_analysis.utils.query_ollama")
    def test_reverify_fact_checks_command_updates_entries(self, mock_ollama):
        fc = FactCheckResult.objects.create(
            article=self.article,
            claim="The World Health Organization said ...",
            rating="unverified",
            explanation="",
            sources="",
            confidence=None,
            last_verified=None,
        )
        mock_ollama.return_value = {
            "response": '{"rating":"true","confidence":0.9,"explanation":"Verified against WHO site","sources":["https://www.who.int/"]}'
        }
        call_command("reverify_fact_checks", article_id=self.article.id, limit=1, delay=0)
        fc.refresh_from_db()
        self.assertEqual(fc.rating, "true")
        self.assertIsNotNone(fc.last_verified)
        self.assertGreaterEqual(fc.confidence or 0, 0.0)
