from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('preferences/', views.preferences, name='preferences'),
    path('saved-articles/', views.saved_articles, name='saved_articles'),
    path('update-saved-notes/', views.update_saved_notes, name='update_saved_notes'),
    path('delete-saved/', views.delete_saved, name='delete_saved'),
    path('bulk-delete-saved/', views.bulk_delete_saved, name='bulk_delete_saved'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
]
