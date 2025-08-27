from django.test import TestCase, override_settings
from django.core import mail
from django.contrib.auth.models import User
from accounts.models import UserPreferences
from news_analysis.models import MisinformationAlert
from news_analysis.email_utils import get_opted_in_recipient_emails, send_misinformation_alert_email


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

