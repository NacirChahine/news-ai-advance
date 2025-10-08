from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserPreferences

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'
    fields = ('bio', 'profile_picture', 'is_reporter', 'preferred_sources')

class UserPreferencesInline(admin.StackedInline):
    model = UserPreferences
    can_delete = False
    verbose_name_plural = 'preferences'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserPreferencesInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_reporter_display', 'date_joined')

    def is_reporter_display(self, obj):
        """Display if user is a reporter"""
        try:
            return obj.profile.is_reporter
        except:
            return False
    is_reporter_display.boolean = True
    is_reporter_display.short_description = 'Reporter'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
