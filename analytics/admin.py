from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import UserActivity, CourseAnalytics, DailyStats


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """إدارة أنشطة المستخدمين"""

    list_display = [
        'user', 'action', 'description', 'ip_address', 'timestamp'
    ]

    list_filter = ['action', 'timestamp']

    search_fields = ['user__username', 'description', 'ip_address']

    ordering = ['-timestamp']

    readonly_fields = ['timestamp']

    date_hierarchy = 'timestamp'


@admin.register(CourseAnalytics)
class CourseAnalyticsAdmin(admin.ModelAdmin):
    """إدارة تحليلات الدورات"""

    list_display = [
        'course', 'total_enrollments', 'active_enrollments',
        'completed_enrollments', 'average_rating', 'total_views'
    ]

    list_filter = ['last_updated']

    search_fields = ['course__title']

    ordering = ['-total_enrollments']

    readonly_fields = [
        'total_enrollments', 'active_enrollments', 'completed_enrollments',
        'average_completion_time', 'average_rating', 'total_reviews',
        'total_views', 'last_updated'
    ]


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    """إدارة الإحصائيات اليومية"""

    list_display = [
        'date', 'new_users', 'active_users', 'new_enrollments',
        'completed_courses', 'certificates_issued'
    ]

    list_filter = ['date']

    ordering = ['-date']

    date_hierarchy = 'date'
