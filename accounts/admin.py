from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserPreferences

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserPreferencesInline(admin.StackedInline):
    model = UserPreferences
    can_delete = False
    verbose_name_plural = 'preferences'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserPreferencesInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
