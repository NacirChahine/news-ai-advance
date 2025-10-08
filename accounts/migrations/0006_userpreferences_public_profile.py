# Generated migration for public_profile field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_userpreferences_comments_prefs'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpreferences',
            name='public_profile',
            field=models.BooleanField(default=True, help_text='Allow others to view your public profile'),
        ),
    ]

