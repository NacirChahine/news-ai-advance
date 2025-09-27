from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('news_aggregator', '0003_comments'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='cached_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['cached_score'], name='news_aggre_cached_sco_idx'),
        ),
        migrations.CreateModel(
            name='CommentVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.SmallIntegerField(choices=[(1, 'upvote'), (-1, 'downvote')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='news_aggregator.comment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_votes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('comment', 'user')},
            },
        ),
        migrations.AddIndex(
            model_name='commentvote',
            index=models.Index(fields=['comment'], name='news_aggre_vote_comment_idx'),
        ),
        migrations.AddIndex(
            model_name='commentvote',
            index=models.Index(fields=['user'], name='news_aggre_vote_user_idx'),
        ),
        migrations.AddConstraint(
            model_name='commentvote',
            constraint=models.CheckConstraint(check=models.Q(('value__in', [-1, 1])), name='comment_vote_value_valid'),
        ),
    ]

