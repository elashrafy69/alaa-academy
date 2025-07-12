from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Category, Course, CourseContent, Enrollment,
    StudentProgress, Certificate, Review
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """إدارة فئات الدورات"""

    list_display = ['name', 'icon', 'color', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


class CourseContentInline(admin.TabularInline):
    """محتوى الدورة كجدول مضمن"""
    model = CourseContent
    extra = 1
    fields = ['title', 'content_type', 'order_sequence', 'duration', 'is_free', 'is_published']
    ordering = ['order_sequence']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """إدارة الدورات"""

    list_display = [
        'title', 'category', 'instructor', 'difficulty_level',
        'status', 'price', 'is_featured', 'created_at'
    ]

    list_filter = [
        'category', 'difficulty_level', 'status',
        'is_featured', 'created_at'
    ]

    search_fields = ['title', 'description', 'instructor__username']

    ordering = ['-created_at']

    prepopulated_fields = {'slug': ('title',)}

    inlines = [CourseContentInline]

    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('title', 'slug', 'category', 'instructor')
        }),
        (_('المحتوى'), {
            'fields': ('description', 'short_description', 'learning_objectives', 'prerequisites')
        }),
        (_('الإعدادات'), {
            'fields': (
                'difficulty_level', 'status', 'price', 'estimated_duration',
                'is_featured', 'enrollment_limit'
            )
        }),
        (_('الوسائط'), {
            'fields': ('thumbnail',)
        }),
    )


@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    """إدارة محتوى الدورات"""

    list_display = [
        'title', 'course', 'content_type', 'order_sequence',
        'duration', 'is_free', 'is_published', 'created_at'
    ]

    list_filter = ['content_type', 'is_free', 'is_published', 'created_at']

    search_fields = ['title', 'course__title', 'description']

    ordering = ['course', 'order_sequence']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """إدارة التسجيلات"""

    list_display = [
        'student', 'course', 'enrollment_date', 'progress_percentage',
        'is_active', 'completion_date'
    ]

    list_filter = [
        'is_active', 'enrollment_date', 'completion_date',
        'course__category'
    ]

    search_fields = [
        'student__username', 'student__email', 'course__title'
    ]

    ordering = ['-enrollment_date']

    readonly_fields = ['progress_percentage', 'completion_date']


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    """إدارة تقدم الطلاب"""

    list_display = [
        'enrollment', 'content', 'is_completed',
        'completion_date', 'time_spent'
    ]

    list_filter = ['is_completed', 'completion_date', 'created_at']

    search_fields = [
        'enrollment__student__username', 'content__title'
    ]

    ordering = ['-updated_at']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """إدارة الشهادات"""

    list_display = [
        'certificate_number', 'enrollment', 'issue_date',
        'is_verified', 'grade'
    ]

    list_filter = ['is_verified', 'issue_date']

    search_fields = [
        'certificate_number', 'enrollment__student__username',
        'enrollment__course__title'
    ]

    ordering = ['-issue_date']

    readonly_fields = ['certificate_number', 'issue_date']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """إدارة التقييمات"""

    list_display = [
        'enrollment', 'rating', 'is_approved', 'created_at'
    ]

    list_filter = ['rating', 'is_approved', 'created_at']

    search_fields = [
        'enrollment__student__username', 'enrollment__course__title',
        'comment'
    ]

    ordering = ['-created_at']
