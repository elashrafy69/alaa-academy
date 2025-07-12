from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class Category(models.Model):
    """نموذج فئات الدورات"""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('اسم الفئة')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('الوصف')
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=_('اسم أيقونة Bootstrap أو Font Awesome'),
        verbose_name=_('الأيقونة')
    )

    color = models.CharField(
        max_length=7,
        default='#007bff',
        help_text=_('لون الفئة بصيغة hex'),
        verbose_name=_('اللون')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    class Meta:
        verbose_name = _('فئة')
        verbose_name_plural = _('الفئات')
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(models.Model):
    """نموذج الدورات التدريبية"""

    DIFFICULTY_CHOICES = [
        ('beginner', _('مبتدئ')),
        ('intermediate', _('متوسط')),
        ('advanced', _('متقدم')),
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('published', _('منشور')),
        ('archived', _('مؤرشف')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('عنوان الدورة')
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_('الرابط المختصر')
    )

    description = models.TextField(
        verbose_name=_('وصف الدورة')
    )

    short_description = models.CharField(
        max_length=300,
        verbose_name=_('وصف مختصر')
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_('الفئة')
    )

    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='taught_courses',
        verbose_name=_('المدرب')
    )

    thumbnail = models.ImageField(
        upload_to='course_thumbnails/',
        verbose_name=_('صورة الدورة')
    )

    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner',
        verbose_name=_('مستوى الصعوبة')
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('الحالة')
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_('السعر')
    )

    estimated_duration = models.PositiveIntegerField(
        help_text=_('المدة المقدرة بالساعات'),
        verbose_name=_('المدة المقدرة')
    )

    prerequisites = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('المتطلبات المسبقة')
    )

    learning_objectives = models.TextField(
        verbose_name=_('أهداف التعلم')
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name=_('دورة مميزة')
    )

    enrollment_limit = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('حد التسجيل')
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
        verbose_name = _('دورة')
        verbose_name_plural = _('الدورات')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def total_lessons(self):
        """إجمالي عدد الدروس"""
        return self.content.count()

    @property
    def total_duration(self):
        """إجمالي مدة الدورة بالدقائق"""
        return sum(content.duration or 0 for content in self.content.all())

    @property
    def enrollment_count(self):
        """عدد المسجلين"""
        return self.enrollments.filter(is_active=True).count()

    @property
    def is_full(self):
        """فحص ما إذا كانت الدورة ممتلئة"""
        if self.enrollment_limit:
            return self.enrollment_count >= self.enrollment_limit
        return False


class CourseContent(models.Model):
    """نموذج محتوى الدورة"""

    CONTENT_TYPE_CHOICES = [
        ('video', _('فيديو')),
        ('pdf', _('ملف PDF')),
        ('quiz', _('اختبار')),
        ('assignment', _('مهمة')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='content',
        verbose_name=_('الدورة')
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('عنوان المحتوى')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('الوصف')
    )

    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        verbose_name=_('نوع المحتوى')
    )

    file_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('رابط الملف')
    )

    file_upload = models.FileField(
        upload_to='course_content/',
        blank=True,
        null=True,
        verbose_name=_('رفع الملف')
    )

    duration = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text=_('المدة بالدقائق'),
        verbose_name=_('المدة')
    )

    order_sequence = models.PositiveIntegerField(
        default=1,
        verbose_name=_('ترتيب التسلسل')
    )

    is_free = models.BooleanField(
        default=False,
        verbose_name=_('مجاني')
    )

    is_published = models.BooleanField(
        default=True,
        verbose_name=_('منشور')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    class Meta:
        verbose_name = _('محتوى الدورة')
        verbose_name_plural = _('محتويات الدورة')
        ordering = ['course', 'order_sequence']
        unique_together = ['course', 'order_sequence']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    @property
    def file_size(self):
        """حجم الملف"""
        if self.file_upload:
            return self.file_upload.size
        return None


class Enrollment(models.Model):
    """نموذج التسجيل في الدورات"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('الطالب')
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('الدورة')
    )

    enrollment_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ التسجيل')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط')
    )

    completion_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('تاريخ الإكمال')
    )

    progress_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name=_('نسبة التقدم')
    )

    last_accessed = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('آخر وصول')
    )

    registration_code_used = models.ForeignKey(
        'accounts.RegistrationCode',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('كود التسجيل المستخدم')
    )

    class Meta:
        verbose_name = _('تسجيل')
        verbose_name_plural = _('التسجيلات')
        unique_together = ['student', 'course']
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title}"

    @property
    def is_completed(self):
        """فحص ما إذا كانت الدورة مكتملة"""
        return self.completion_date is not None

    def update_progress(self):
        """تحديث نسبة التقدم"""
        total_content = self.course.content.filter(is_published=True).count()
        if total_content == 0:
            self.progress_percentage = 0.0
        else:
            completed_content = self.progress_records.filter(is_completed=True).count()
            self.progress_percentage = (completed_content / total_content) * 100

            # فحص الإكمال
            if self.progress_percentage >= 100.0 and not self.completion_date:
                from django.utils import timezone
                self.completion_date = timezone.now()

        self.save()


class StudentProgress(models.Model):
    """نموذج تقدم الطالب في المحتوى"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name=_('التسجيل')
    )

    content = models.ForeignKey(
        CourseContent,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name=_('المحتوى')
    )

    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('مكتمل')
    )

    completion_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('تاريخ الإكمال')
    )

    time_spent = models.PositiveIntegerField(
        default=0,
        help_text=_('الوقت المقضي بالثواني'),
        verbose_name=_('الوقت المقضي')
    )

    last_position = models.PositiveIntegerField(
        default=0,
        help_text=_('آخر موضع في الفيديو بالثواني'),
        verbose_name=_('آخر موضع')
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('الملاحظات')
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
        verbose_name = _('تقدم الطالب')
        verbose_name_plural = _('تقدم الطلاب')
        unique_together = ['enrollment', 'content']
        ordering = ['content__order_sequence']

    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.content.title}"

    def mark_completed(self):
        """تحديد المحتوى كمكتمل"""
        if not self.is_completed:
            from django.utils import timezone
            self.is_completed = True
            self.completion_date = timezone.now()
            self.save()

            # تحديث تقدم التسجيل
            self.enrollment.update_progress()


class Certificate(models.Model):
    """نموذج الشهادات"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='certificate',
        verbose_name=_('التسجيل')
    )

    certificate_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('رقم الشهادة')
    )

    issue_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإصدار')
    )

    certificate_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('رابط الشهادة')
    )

    is_verified = models.BooleanField(
        default=True,
        verbose_name=_('تم التحقق')
    )

    grade = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_('الدرجة')
    )

    class Meta:
        verbose_name = _('شهادة')
        verbose_name_plural = _('الشهادات')
        ordering = ['-issue_date']

    def __str__(self):
        return f"شهادة {self.enrollment.course.title} - {self.enrollment.student.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            # إنشاء رقم شهادة فريد
            import random
            import string
            self.certificate_number = f"ALAA-{self.enrollment.course.id.hex[:8].upper()}-{''.join(random.choices(string.digits, k=6))}"
        super().save(*args, **kwargs)


class Review(models.Model):
    """نموذج تقييمات الدورات"""

    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name=_('التسجيل')
    )

    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('التقييم')
    )

    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('التعليق')
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name=_('معتمد')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    class Meta:
        verbose_name = _('تقييم')
        verbose_name_plural = _('التقييمات')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.enrollment.course.title} - {self.rating} نجوم"
