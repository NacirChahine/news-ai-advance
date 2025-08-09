from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('news_aggregator', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsarticle',
            name='political_bias',
            field=models.FloatField(blank=True, null=True, help_text='Political bias score from -1 (left) to +1 (right)'),
        ),
        migrations.AddField(
            model_name='newssource',
            name='political_bias',
            field=models.FloatField(default=0.0, help_text='Average political bias score from -1 (left) to +1 (right)'),
        ),
    ]
