"""
نماذج نظام الإشعارات والتنبيهات
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
import uuid

User = get_user_model()


class NotificationType(models.TextChoices):
    """أنواع الإشعارات"""
    ENROLLMENT = 'enrollment', 'تسجيل في دورة'
    COURSE_UPDATE = 'course_update', 'تحديث الدورة'
    ASSIGNMENT = 'assignment', 'مهمة جديدة'
    GRADE = 'grade', 'درجة جديدة'
    CERTIFICATE = 'certificate', 'شهادة جديدة'
    REMINDER = 'reminder', 'تذكير'
    ANNOUNCEMENT = 'announcement', 'إعلان'
    MESSAGE = 'message', 'رسالة'
    SYSTEM = 'system', 'نظام'


class NotificationPriority(models.TextChoices):
    """أولوية الإشعارات"""
    LOW = 'low', 'منخفضة'
    NORMAL = 'normal', 'عادية'
    HIGH = 'high', 'عالية'
    URGENT = 'urgent', 'عاجلة'


class Notification(models.Model):
    """نموذج الإشعارات"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # المستقبل
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='المستقبل'
    )
    
    # المرسل (اختياري)
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        verbose_name='المرسل'
    )
    
    # محتوى الإشعار
    title = models.CharField(max_length=200, verbose_name='العنوان')
    message = models.TextField(verbose_name='الرسالة')
    
    # نوع وأولوية الإشعار
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        verbose_name='نوع الإشعار'
    )
    
    priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name='الأولوية'
    )
    
    # الرابط المرتبط بالإشعار
    action_url = models.URLField(blank=True, null=True, verbose_name='رابط الإجراء')
    
    # حالة الإشعار
    is_read = models.BooleanField(default=False, verbose_name='مقروء')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ القراءة')
    
    # إعدادات الإرسال
    send_email = models.BooleanField(default=False, verbose_name='إرسال بريد إلكتروني')
    email_sent = models.BooleanField(default=False, verbose_name='تم إرسال البريد')
    email_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ إرسال البريد')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ انتهاء الصلاحية')
    
    # بيانات إضافية (JSON)
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='بيانات إضافية')
    
    class Meta:
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f'{self.title} - {self.recipient.get_full_name()}'
    
    def mark_as_read(self):
        """تحديد الإشعار كمقروء"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def is_expired(self):
        """التحقق من انتهاء صلاحية الإشعار"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_icon(self):
        """الحصول على أيقونة الإشعار"""
        icons = {
            NotificationType.ENROLLMENT: 'fas fa-user-plus',
            NotificationType.COURSE_UPDATE: 'fas fa-book',
            NotificationType.ASSIGNMENT: 'fas fa-tasks',
            NotificationType.GRADE: 'fas fa-star',
            NotificationType.CERTIFICATE: 'fas fa-certificate',
            NotificationType.REMINDER: 'fas fa-bell',
            NotificationType.ANNOUNCEMENT: 'fas fa-bullhorn',
            NotificationType.MESSAGE: 'fas fa-envelope',
            NotificationType.SYSTEM: 'fas fa-cog',
        }
        return icons.get(self.notification_type, 'fas fa-info-circle')
    
    def get_color_class(self):
        """الحصول على فئة اللون حسب الأولوية"""
        colors = {
            NotificationPriority.LOW: 'text-muted',
            NotificationPriority.NORMAL: 'text-primary',
            NotificationPriority.HIGH: 'text-warning',
            NotificationPriority.URGENT: 'text-danger',
        }
        return colors.get(self.priority, 'text-primary')


class NotificationTemplate(models.Model):
    """قوالب الإشعارات"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=100, unique=True, verbose_name='اسم القالب')
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        verbose_name='نوع الإشعار'
    )
    
    # قوالب المحتوى
    title_template = models.CharField(max_length=200, verbose_name='قالب العنوان')
    message_template = models.TextField(verbose_name='قالب الرسالة')
    email_subject_template = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='قالب موضوع البريد'
    )
    email_body_template = models.TextField(blank=True, verbose_name='قالب نص البريد')
    
    # إعدادات افتراضية
    default_priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name='الأولوية الافتراضية'
    )
    
    send_email_default = models.BooleanField(default=False, verbose_name='إرسال بريد افتراضي')
    
    # حالة القالب
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'قالب إشعار'
        verbose_name_plural = 'قوالب الإشعارات'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def render_title(self, context):
        """تطبيق القالب على العنوان"""
        from django.template import Template, Context
        template = Template(self.title_template)
        return template.render(Context(context))
    
    def render_message(self, context):
        """تطبيق القالب على الرسالة"""
        from django.template import Template, Context
        template = Template(self.message_template)
        return template.render(Context(context))
    
    def render_email_subject(self, context):
        """تطبيق القالب على موضوع البريد"""
        if self.email_subject_template:
            from django.template import Template, Context
            template = Template(self.email_subject_template)
            return template.render(Context(context))
        return self.render_title(context)
    
    def render_email_body(self, context):
        """تطبيق القالب على نص البريد"""
        if self.email_body_template:
            from django.template import Template, Context
            template = Template(self.email_body_template)
            return template.render(Context(context))
        return self.render_message(context)


class NotificationPreference(models.Model):
    """تفضيلات الإشعارات للمستخدمين"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name='المستخدم'
    )
    
    # إعدادات عامة
    email_notifications = models.BooleanField(default=True, verbose_name='إشعارات البريد الإلكتروني')
    browser_notifications = models.BooleanField(default=True, verbose_name='إشعارات المتصفح')
    
    # إعدادات حسب النوع
    enrollment_notifications = models.BooleanField(default=True, verbose_name='إشعارات التسجيل')
    course_update_notifications = models.BooleanField(default=True, verbose_name='إشعارات تحديث الدورات')
    assignment_notifications = models.BooleanField(default=True, verbose_name='إشعارات المهام')
    grade_notifications = models.BooleanField(default=True, verbose_name='إشعارات الدرجات')
    certificate_notifications = models.BooleanField(default=True, verbose_name='إشعارات الشهادات')
    reminder_notifications = models.BooleanField(default=True, verbose_name='التذكيرات')
    announcement_notifications = models.BooleanField(default=True, verbose_name='الإعلانات')
    message_notifications = models.BooleanField(default=True, verbose_name='الرسائل')
    
    # إعدادات التوقيت
    quiet_hours_start = models.TimeField(null=True, blank=True, verbose_name='بداية الساعات الهادئة')
    quiet_hours_end = models.TimeField(null=True, blank=True, verbose_name='نهاية الساعات الهادئة')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'تفضيلات الإشعارات'
        verbose_name_plural = 'تفضيلات الإشعارات'
    
    def __str__(self):
        return f'تفضيلات {self.user.get_full_name()}'
    
    def should_send_notification(self, notification_type):
        """التحقق من إمكانية إرسال إشعار من نوع معين"""
        type_preferences = {
            NotificationType.ENROLLMENT: self.enrollment_notifications,
            NotificationType.COURSE_UPDATE: self.course_update_notifications,
            NotificationType.ASSIGNMENT: self.assignment_notifications,
            NotificationType.GRADE: self.grade_notifications,
            NotificationType.CERTIFICATE: self.certificate_notifications,
            NotificationType.REMINDER: self.reminder_notifications,
            NotificationType.ANNOUNCEMENT: self.announcement_notifications,
            NotificationType.MESSAGE: self.message_notifications,
        }
        return type_preferences.get(notification_type, True)
    
    def is_quiet_time(self):
        """التحقق من كون الوقت الحالي في الساعات الهادئة"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        current_time = timezone.now().time()
        
        if self.quiet_hours_start <= self.quiet_hours_end:
            # نفس اليوم
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end
        else:
            # عبر منتصف الليل
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end


class NotificationBatch(models.Model):
    """مجموعة إشعارات مرسلة معاً"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(max_length=200, verbose_name='عنوان المجموعة')
    description = models.TextField(blank=True, verbose_name='الوصف')
    
    # المرسل
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notification_batches',
        verbose_name='المرسل'
    )
    
    # إحصائيات
    total_recipients = models.PositiveIntegerField(default=0, verbose_name='إجمالي المستقبلين')
    sent_count = models.PositiveIntegerField(default=0, verbose_name='عدد المرسل')
    failed_count = models.PositiveIntegerField(default=0, verbose_name='عدد الفاشل')
    
    # حالة الإرسال
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'في الانتظار'),
            ('sending', 'جاري الإرسال'),
            ('completed', 'مكتمل'),
            ('failed', 'فاشل'),
        ],
        default='pending',
        verbose_name='الحالة'
    )
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ البدء')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإكمال')
    
    class Meta:
        verbose_name = 'مجموعة إشعارات'
        verbose_name_plural = 'مجموعات الإشعارات'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
