"""
نماذج نظام إدارة المحتوى المتقدم
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.validators import FileExtensionValidator
import uuid
import os

User = get_user_model()


class ContentStatus(models.TextChoices):
    """حالات المحتوى"""
    DRAFT = 'draft', 'مسودة'
    REVIEW = 'review', 'قيد المراجعة'
    PUBLISHED = 'published', 'منشور'
    ARCHIVED = 'archived', 'مؤرشف'


class ContentType(models.TextChoices):
    """أنواع المحتوى"""
    PAGE = 'page', 'صفحة'
    ARTICLE = 'article', 'مقال'
    NEWS = 'news', 'خبر'
    ANNOUNCEMENT = 'announcement', 'إعلان'
    FAQ = 'faq', 'سؤال شائع'
    POLICY = 'policy', 'سياسة'


class Category(models.Model):
    """فئات المحتوى"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=100, verbose_name='الاسم')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='الرابط')
    description = models.TextField(blank=True, verbose_name='الوصف')
    
    # الفئة الأب
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='الفئة الأب'
    )
    
    # إعدادات العرض
    icon = models.CharField(max_length=50, blank=True, verbose_name='الأيقونة')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='اللون')
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')
    
    # حالة الفئة
    is_active = models.BooleanField(default=True, verbose_name='نشطة')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'فئة المحتوى'
        verbose_name_plural = 'فئات المحتوى'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('cms:category', kwargs={'slug': self.slug})
    
    def get_full_path(self):
        """الحصول على المسار الكامل للفئة"""
        if self.parent:
            return f'{self.parent.get_full_path()} > {self.name}'
        return self.name


class Tag(models.Model):
    """علامات المحتوى"""
    
    name = models.CharField(max_length=50, unique=True, verbose_name='الاسم')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='الرابط')
    color = models.CharField(max_length=7, default='#6c757d', verbose_name='اللون')
    
    # إحصائيات
    usage_count = models.PositiveIntegerField(default=0, verbose_name='عدد الاستخدام')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        verbose_name = 'علامة'
        verbose_name_plural = 'العلامات'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('cms:tag', kwargs={'slug': self.slug})


class Content(models.Model):
    """المحتوى الأساسي"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # معلومات أساسية
    title = models.CharField(max_length=200, verbose_name='العنوان')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='الرابط')
    excerpt = models.TextField(max_length=500, blank=True, verbose_name='المقتطف')
    content = models.TextField(verbose_name='المحتوى')
    
    # نوع المحتوى
    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices,
        default=ContentType.ARTICLE,
        verbose_name='نوع المحتوى'
    )
    
    # التصنيف
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contents',
        verbose_name='الفئة'
    )
    
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='contents',
        verbose_name='العلامات'
    )
    
    # المؤلف والمحرر
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_contents',
        verbose_name='المؤلف'
    )
    
    editor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='edited_contents',
        verbose_name='المحرر'
    )
    
    # حالة المحتوى
    status = models.CharField(
        max_length=20,
        choices=ContentStatus.choices,
        default=ContentStatus.DRAFT,
        verbose_name='الحالة'
    )
    
    # إعدادات النشر
    is_featured = models.BooleanField(default=False, verbose_name='مميز')
    is_pinned = models.BooleanField(default=False, verbose_name='مثبت')
    allow_comments = models.BooleanField(default=True, verbose_name='السماح بالتعليقات')
    
    # تواريخ النشر
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ النشر')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ انتهاء الصلاحية')
    
    # إحصائيات
    view_count = models.PositiveIntegerField(default=0, verbose_name='عدد المشاهدات')
    like_count = models.PositiveIntegerField(default=0, verbose_name='عدد الإعجابات')
    share_count = models.PositiveIntegerField(default=0, verbose_name='عدد المشاركات')
    
    # SEO
    meta_title = models.CharField(max_length=60, blank=True, verbose_name='عنوان SEO')
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='وصف SEO')
    meta_keywords = models.CharField(max_length=255, blank=True, verbose_name='كلمات مفتاحية')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'محتوى'
        verbose_name_plural = 'المحتويات'
        ordering = ['-is_pinned', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['content_type', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_featured', '-published_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('cms:content_detail', kwargs={'slug': self.slug})
    
    def is_published(self):
        """التحقق من كون المحتوى منشور"""
        return (
            self.status == ContentStatus.PUBLISHED and
            self.published_at and
            self.published_at <= timezone.now() and
            (not self.expires_at or self.expires_at > timezone.now())
        )
    
    def can_be_viewed_by(self, user):
        """التحقق من إمكانية عرض المحتوى للمستخدم"""
        if self.is_published():
            return True
        
        if not user or not user.is_authenticated:
            return False
        
        # المؤلف والمحرر يمكنهما رؤية المحتوى
        if user == self.author or user == self.editor:
            return True
        
        # المدراء يمكنهم رؤية جميع المحتويات
        if user.is_admin:
            return True
        
        return False
    
    def increment_view_count(self):
        """زيادة عداد المشاهدات"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def get_reading_time(self):
        """حساب وقت القراءة المقدر"""
        words_per_minute = 200
        word_count = len(self.content.split())
        reading_time = max(1, round(word_count / words_per_minute))
        return reading_time


def content_media_path(instance, filename):
    """مسار رفع ملفات المحتوى"""
    return f'content/{instance.content.id}/{filename}'


class ContentMedia(models.Model):
    """ملفات المحتوى"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='media_files',
        verbose_name='المحتوى'
    )
    
    # معلومات الملف
    title = models.CharField(max_length=200, verbose_name='العنوان')
    description = models.TextField(blank=True, verbose_name='الوصف')
    
    file = models.FileField(
        upload_to=content_media_path,
        validators=[FileExtensionValidator(allowed_extensions=[
            'jpg', 'jpeg', 'png', 'gif', 'webp',  # صور
            'mp4', 'webm', 'ogg',  # فيديو
            'mp3', 'wav', 'ogg',  # صوت
            'pdf', 'doc', 'docx', 'txt',  # مستندات
        ])],
        verbose_name='الملف'
    )
    
    # نوع الملف
    media_type = models.CharField(
        max_length=20,
        choices=[
            ('image', 'صورة'),
            ('video', 'فيديو'),
            ('audio', 'صوت'),
            ('document', 'مستند'),
        ],
        verbose_name='نوع الملف'
    )
    
    # معلومات إضافية
    file_size = models.PositiveIntegerField(default=0, verbose_name='حجم الملف')
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='النص البديل')
    
    # ترتيب العرض
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')
    
    # تواريخ
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')
    
    class Meta:
        verbose_name = 'ملف محتوى'
        verbose_name_plural = 'ملفات المحتوى'
        ordering = ['order', 'uploaded_at']
    
    def __str__(self):
        return self.title
    
    def get_file_extension(self):
        """الحصول على امتداد الملف"""
        return os.path.splitext(self.file.name)[1].lower()
    
    def is_image(self):
        """التحقق من كون الملف صورة"""
        return self.media_type == 'image'
    
    def is_video(self):
        """التحقق من كون الملف فيديو"""
        return self.media_type == 'video'


class ContentRevision(models.Model):
    """مراجعات المحتوى"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='revisions',
        verbose_name='المحتوى'
    )
    
    # المحرر
    editor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='المحرر'
    )
    
    # محتوى المراجعة
    title = models.CharField(max_length=200, verbose_name='العنوان')
    content_text = models.TextField(verbose_name='المحتوى')
    
    # ملاحظات التغيير
    change_summary = models.CharField(max_length=500, blank=True, verbose_name='ملخص التغيير')
    
    # تاريخ المراجعة
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ المراجعة')
    
    class Meta:
        verbose_name = 'مراجعة محتوى'
        verbose_name_plural = 'مراجعات المحتوى'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.content.title} - {self.created_at.strftime("%Y-%m-%d %H:%M")}'


class ContentView(models.Model):
    """مشاهدات المحتوى"""
    
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='المحتوى'
    )
    
    # المشاهد
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='المستخدم'
    )
    
    # معلومات الجلسة
    session_key = models.CharField(max_length=40, blank=True, verbose_name='مفتاح الجلسة')
    ip_address = models.GenericIPAddressField(verbose_name='عنوان IP')
    user_agent = models.TextField(blank=True, verbose_name='وكيل المستخدم')
    
    # تاريخ المشاهدة
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ المشاهدة')
    
    class Meta:
        verbose_name = 'مشاهدة محتوى'
        verbose_name_plural = 'مشاهدات المحتوى'
        ordering = ['-viewed_at']
        unique_together = ['content', 'user', 'session_key']
    
    def __str__(self):
        return f'{self.content.title} - {self.viewed_at.strftime("%Y-%m-%d")}'
