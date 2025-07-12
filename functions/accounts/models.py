from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """نموذج المستخدم المخصص لأكاديمية علاء عبد الحميد"""

    USER_TYPE_CHOICES = [
        ('admin', _('مدير')),
        ('student', _('طالب')),
    ]

    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='student',
        verbose_name=_('نوع المستخدم')
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('رقم الهاتف')
    )

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        verbose_name=_('صورة الملف الشخصي')
    )

    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('نبذة شخصية')
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('تاريخ الميلاد')
    )

    registration_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('كود التسجيل')
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('تم التحقق')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاريخ التحديث')
    )

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"

    @property
    def is_admin(self):
        """فحص ما إذا كان المستخدم مدير"""
        return self.user_type == 'admin'

    @property
    def is_student(self):
        """فحص ما إذا كان المستخدم طالب"""
        return self.user_type == 'student'

    def get_full_name(self):
        """الحصول على الاسم الكامل"""
        return f"{self.first_name} {self.last_name}".strip()


class RegistrationCode(models.Model):
    """نموذج أكواد التسجيل"""

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('الكود')
    )

    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('الدورة')
    )

    max_uses = models.PositiveIntegerField(
        default=1,
        verbose_name=_('الحد الأقصى للاستخدام')
    )

    current_uses = models.PositiveIntegerField(
        default=0,
        verbose_name=_('الاستخدام الحالي')
    )

    expiry_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('تاريخ الانتهاء')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط')
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_codes',
        verbose_name=_('أنشأ بواسطة')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    class Meta:
        verbose_name = _('كود تسجيل')
        verbose_name_plural = _('أكواد التسجيل')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.course.title if self.course else 'عام'}"

    @property
    def is_expired(self):
        """فحص ما إذا كان الكود منتهي الصلاحية"""
        if self.expiry_date:
            from django.utils import timezone
            return timezone.now() > self.expiry_date
        return False

    @property
    def is_available(self):
        """فحص ما إذا كان الكود متاح للاستخدام"""
        return (
            self.is_active and
            not self.is_expired and
            self.current_uses < self.max_uses
        )

    def use_code(self):
        """استخدام الكود"""
        if self.is_available:
            self.current_uses += 1
            self.save()
            return True
        return False
