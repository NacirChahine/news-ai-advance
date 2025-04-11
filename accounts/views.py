from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, UserPreferences
from news_aggregator.models import UserSavedArticle

def signup(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('accounts:login')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def profile(request):
    """User profile view"""
    user = request.user
    profile = user.profile
    
    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def preferences(request):
    """User preferences view"""
    user = request.user
    preferences = user.preferences
    
    context = {
        'user': user,
        'preferences': preferences,
    }
    return render(request, 'accounts/preferences.html', context)

@login_required
def saved_articles(request):
    """View for user's saved articles"""
    user = request.user
    saved = UserSavedArticle.objects.filter(user=user).order_by('-saved_at')
    
    context = {
        'saved_articles': saved,
    }
    return render(request, 'accounts/saved_articles.html', context)
