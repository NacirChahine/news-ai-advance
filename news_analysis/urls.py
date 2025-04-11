from django.urls import path
from . import views

urlpatterns = [
    path('misinformation-tracker/', views.misinformation_tracker, name='misinformation_tracker'),
    path('article-analysis/<int:article_id>/', views.article_analysis, name='article_analysis'),
    path('bias-analysis/<int:article_id>/', views.bias_analysis, name='bias_analysis'),
    path('sentiment-analysis/<int:article_id>/', views.sentiment_analysis, name='sentiment_analysis'),
    path('fact-check/<int:article_id>/', views.fact_check, name='fact_check'),
    path('misinformation/<int:alert_id>/details/', views.alert_detail, name='alert_detail'),
]
