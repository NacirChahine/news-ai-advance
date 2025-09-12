from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from news_aggregator.models import NewsSource, NewsArticle
from news_analysis.models import LogicalFallacy, LogicalFallacyDetection
from news_analysis.utils import detect_logical_fallacies_with_ai


class LogicalFallaciesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.source = NewsSource.objects.create(
            name="Test Source",
            url="https://example.com",
        )
        self.article = NewsArticle.objects.create(
            title="Test Article",
            source=self.source,
            url="https://example.com/article",
            content="This is a test content that might include some fallacious reasoning.",
        )

    def test_catalog_seeded(self):
        # Data migration should have populated common fallacies
        count = LogicalFallacy.objects.count()
        self.assertGreater(count, 0, "LogicalFallacy catalog should be populated by data migration")

    @patch("news_analysis.utils.query_ollama")
    def test_detect_logical_fallacies_with_ai_parses_response(self, mock_query):
        mock_query.return_value = {
            "response": '[{"name":"Ad Hominem","confidence":0.82,"evidence_excerpt":"You can\'t trust him...","start_char":5,"end_char":25}]'
        }
        result = detect_logical_fallacies_with_ai("Some text")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        det = result[0]
        self.assertEqual(det["name"], "Ad Hominem")
        self.assertAlmostEqual(det["confidence"], 0.82, places=2)
        self.assertEqual(det["start_char"], 5)
        self.assertEqual(det["end_char"], 25)

    def test_fallacies_reference_view(self):
        url = reverse("news_analysis:fallacies")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Page lists fallacies and shows a heading
        self.assertContains(resp, "Logical Fallacies")
        # Should include at least one seeded fallacy name
        lf = LogicalFallacy.objects.first()
        if lf:
            self.assertContains(resp, lf.name)

    def test_article_analysis_includes_logical_fallacies_card(self):
        # create a detection to ensure content appears
        fallacy = LogicalFallacy.objects.first()
        if not fallacy:
            fallacy = LogicalFallacy.objects.create(name="Test Fallacy", slug="test-fallacy")
        LogicalFallacyDetection.objects.create(article=self.article, fallacy=fallacy, confidence=0.75)
        url = reverse("news_analysis:article_analysis", args=[self.article.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Logical Fallacies")
        self.assertContains(resp, fallacy.name)

