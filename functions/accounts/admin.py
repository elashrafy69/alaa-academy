from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, RegistrationCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """إدارة المستخدمين"""

    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'user_type', 'is_verified', 'is_active', 'created_at'
    ]

    list_filter = [
        'user_type', 'is_verified', 'is_active',
        'is_staff', 'is_superuser', 'created_at'
    ]

    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']

    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        (_('معلومات إضافية'), {
            'fields': (
                'user_type', 'phone_number', 'profile_picture',
                'bio', 'date_of_birth', 'registration_code', 'is_verified'
            )
        }),
        (_('التواريخ المهمة'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('معلومات إضافية'), {
            'fields': ('user_type', 'phone_number', 'email')
        }),
    )


@admin.register(RegistrationCode)
class RegistrationCodeAdmin(admin.ModelAdmin):
    """إدارة أكواد التسجيل"""

    list_display = [
        'code', 'course', 'max_uses', 'current_uses',
        'expiry_date', 'is_active', 'created_by', 'created_at'
    ]

    list_filter = ['is_active', 'expiry_date', 'created_at', 'course']

    search_fields = ['code', 'course__title']

    ordering = ['-created_at']

    readonly_fields = ['current_uses', 'created_at']

    def save_model(self, request, obj, form, change):
        if not change:  # إذا كان إنشاء جديد
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
