from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_userpreferences_enable_key_insights_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpreferences',
            name='show_comments',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='notify_on_comment_reply',
            field=models.BooleanField(default=False),
        ),
    ]

