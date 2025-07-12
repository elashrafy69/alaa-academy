from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()


class UserActivity(models.Model):
    """نموذج نشاط المستخدم"""

    ACTION_CHOICES = [
        ('login', _('تسجيل دخول')),
        ('logout', _('تسجيل خروج')),
        ('course_view', _('عرض دورة')),
        ('content_view', _('عرض محتوى')),
        ('content_complete', _('إكمال محتوى')),
        ('course_enroll', _('تسجيل في دورة')),
        ('course_complete', _('إكمال دورة')),
        ('certificate_download', _('تحميل شهادة')),
        ('profile_update', _('تحديث الملف الشخصي')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('المستخدم')
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name=_('الإجراء')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('الوصف')
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_('عنوان IP')
    )

    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('معلومات المتصفح')
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('بيانات إضافية')
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('الوقت')
    )

    class Meta:
        verbose_name = _('نشاط المستخدم')
        verbose_name_plural = _('أنشطة المستخدمين')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp}"


class CourseAnalytics(models.Model):
    """نموذج تحليلات الدورة"""

    course = models.OneToOneField(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name=_('الدورة')
    )

    total_enrollments = models.PositiveIntegerField(
        default=0,
        verbose_name=_('إجمالي التسجيلات')
    )

    active_enrollments = models.PositiveIntegerField(
        default=0,
        verbose_name=_('التسجيلات النشطة')
    )

    completed_enrollments = models.PositiveIntegerField(
        default=0,
        verbose_name=_('التسجيلات المكتملة')
    )

    average_completion_time = models.FloatField(
        default=0.0,
        help_text=_('متوسط وقت الإكمال بالأيام'),
        verbose_name=_('متوسط وقت الإكمال')
    )

    average_rating = models.FloatField(
        default=0.0,
        verbose_name=_('متوسط التقييم')
    )

    total_reviews = models.PositiveIntegerField(
        default=0,
        verbose_name=_('إجمالي التقييمات')
    )

    total_views = models.PositiveIntegerField(
        default=0,
        verbose_name=_('إجمالي المشاهدات')
    )

    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_('آخر تحديث')
    )

    class Meta:
        verbose_name = _('تحليلات الدورة')
        verbose_name_plural = _('تحليلات الدورات')

    def __str__(self):
        return f"تحليلات {self.course.title}"

    def update_analytics(self):
        """تحديث إحصائيات الدورة"""
        enrollments = self.course.enrollments.all()

        self.total_enrollments = enrollments.count()
        self.active_enrollments = enrollments.filter(is_active=True).count()
        self.completed_enrollments = enrollments.filter(completion_date__isnull=False).count()

        # حساب متوسط وقت الإكمال
        completed = enrollments.filter(completion_date__isnull=False)
        if completed.exists():
            total_days = sum(
                (enrollment.completion_date - enrollment.enrollment_date).days
                for enrollment in completed
            )
            self.average_completion_time = total_days / completed.count()

        # حساب متوسط التقييم
        reviews = self.course.enrollments.filter(review__isnull=False).select_related('review')
        if reviews.exists():
            total_rating = sum(enrollment.review.rating for enrollment in reviews)
            self.average_rating = total_rating / reviews.count()
            self.total_reviews = reviews.count()

        self.save()


class DailyStats(models.Model):
    """نموذج الإحصائيات اليومية"""

    date = models.DateField(
        unique=True,
        verbose_name=_('التاريخ')
    )

    new_users = models.PositiveIntegerField(
        default=0,
        verbose_name=_('مستخدمون جدد')
    )

    active_users = models.PositiveIntegerField(
        default=0,
        verbose_name=_('مستخدمون نشطون')
    )

    new_enrollments = models.PositiveIntegerField(
        default=0,
        verbose_name=_('تسجيلات جديدة')
    )

    completed_courses = models.PositiveIntegerField(
        default=0,
        verbose_name=_('دورات مكتملة')
    )

    certificates_issued = models.PositiveIntegerField(
        default=0,
        verbose_name=_('شهادات صادرة')
    )

    total_learning_time = models.PositiveIntegerField(
        default=0,
        help_text=_('إجمالي وقت التعلم بالدقائق'),
        verbose_name=_('إجمالي وقت التعلم')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    class Meta:
        verbose_name = _('إحصائيات يومية')
        verbose_name_plural = _('الإحصائيات اليومية')
        ordering = ['-date']

    def __str__(self):
        return f"إحصائيات {self.date}"
