from django.urls import path
from . import views

urlpatterns = [
    path('latest/', views.latest_news, name='latest'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('sources/', views.source_list, name='source_list'),
    path('source/<int:source_id>/', views.source_detail, name='source_detail'),
    path('save-article/', views.save_article_ajax, name='save_article'),
    path('save-article/<int:article_id>/', views.save_article, name='save_article_by_id'),
]
