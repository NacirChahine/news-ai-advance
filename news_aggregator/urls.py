from django.urls import path
from . import views

urlpatterns = [
    path('latest/', views.latest_news, name='latest'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('sources/', views.source_list, name='source_list'),
    path('source/<int:source_id>/', views.source_detail, name='source_detail'),
    path('save-article/', views.save_article_ajax, name='save_article'),
    path('save-article/<int:article_id>/', views.save_article, name='save_article_by_id'),

    # Comment API endpoints (AJAX JSON)
    path('article/<int:article_id>/comments/', views.comments_list_create, name='comments_list_create'),
    path('comments/<int:comment_id>/replies/', views.comment_replies, name='comment_replies'),
    path('comments/<int:comment_id>/reply/', views.comment_reply, name='comment_reply'),
    path('comments/<int:comment_id>/edit/', views.comment_edit, name='comment_edit'),
    path('comments/<int:comment_id>/flag/', views.comment_flag, name='comment_flag'),
    path('comments/<int:comment_id>/moderate/', views.comment_moderate, name='comment_moderate'),
    path('comments/<int:comment_id>/', views.comment_delete, name='comment_delete'),
]
