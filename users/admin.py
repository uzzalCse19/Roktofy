from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('blood_group', 'health_conditions', 'avatar')

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'phone', 'user_type', 'is_available', 'is_verified', 'age', 'last_donation_date')
    list_filter = ('user_type', 'is_available', 'is_verified')

    def blood_group(self, obj):
        return obj.profile.blood_group if hasattr(obj, 'profile') else None
    blood_group.short_description = 'Blood Group'
      
    def avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None
    avatar.short_description = 'Avatar'
    list_display += ('blood_group', 'avatar')
    fieldsets = (
        (None, {'fields': ('email', 'password')}), 
        ('Personal info', {'fields': ('phone', 'address', 'age', 'last_donation_date')}), 
        ('Permissions', {'fields': ('user_type', 'is_available', 'is_verified', 'is_active', 'is_staff', 'is_superuser')}), 
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'password1', 'password2', 'user_type'),
        }),
    )
    
    search_fields = ('email', 'phone', 'user_type', 'is_verified')
    ordering = ('email',)
    readonly_fields = ('email', 'last_donation_date')

admin.site.register(User, CustomUserAdmin)