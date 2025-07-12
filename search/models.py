"""
نماذج نظام البحث المتقدم
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import uuid

User = get_user_model()


class SearchQuery(models.Model):
    """استعلامات البحث المحفوظة"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # المستخدم (اختياري للبحث المجهول)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='search_queries',
        verbose_name='المستخدم'
    )
    
    # تفاصيل البحث
    query = models.CharField(max_length=500, verbose_name='استعلام البحث')
    filters = models.JSONField(default=dict, blank=True, verbose_name='المرشحات')
    
    # نتائج البحث
    results_count = models.PositiveIntegerField(default=0, verbose_name='عدد النتائج')
    
    # معلومات الجلسة
    session_key = models.CharField(max_length=40, blank=True, verbose_name='مفتاح الجلسة')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='عنوان IP')
    user_agent = models.TextField(blank=True, verbose_name='وكيل المستخدم')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ البحث')
    
    class Meta:
        verbose_name = 'استعلام بحث'
        verbose_name_plural = 'استعلامات البحث'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['query']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'{self.query} - {self.results_count} نتيجة'


class PopularSearch(models.Model):
    """البحثات الشائعة"""
    
    query = models.CharField(max_length=200, unique=True, verbose_name='استعلام البحث')
    search_count = models.PositiveIntegerField(default=0, verbose_name='عدد مرات البحث')
    last_searched = models.DateTimeField(auto_now=True, verbose_name='آخر بحث')
    
    # إعدادات العرض
    is_trending = models.BooleanField(default=False, verbose_name='رائج')
    is_featured = models.BooleanField(default=False, verbose_name='مميز')
    
    class Meta:
        verbose_name = 'بحث شائع'
        verbose_name_plural = 'البحثات الشائعة'
        ordering = ['-search_count', '-last_searched']
    
    def __str__(self):
        return f'{self.query} ({self.search_count} مرة)'
    
    @classmethod
    def increment_search(cls, query):
        """زيادة عداد البحث"""
        popular_search, created = cls.objects.get_or_create(
            query=query.lower().strip(),
            defaults={'search_count': 1}
        )
        if not created:
            popular_search.search_count += 1
            popular_search.save(update_fields=['search_count', 'last_searched'])
        return popular_search


class SearchSuggestion(models.Model):
    """اقتراحات البحث"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    suggestion = models.CharField(max_length=200, verbose_name='الاقتراح')
    category = models.CharField(
        max_length=50,
        choices=[
            ('course', 'دورة'),
            ('instructor', 'مدرب'),
            ('topic', 'موضوع'),
            ('skill', 'مهارة'),
            ('general', 'عام'),
        ],
        default='general',
        verbose_name='الفئة'
    )
    
    # الكائن المرتبط (اختياري)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='نوع المحتوى'
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='معرف الكائن')
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # إعدادات
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    priority = models.PositiveIntegerField(default=0, verbose_name='الأولوية')
    
    # إحصائيات
    click_count = models.PositiveIntegerField(default=0, verbose_name='عدد النقرات')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'اقتراح بحث'
        verbose_name_plural = 'اقتراحات البحث'
        ordering = ['-priority', '-click_count', 'suggestion']
        indexes = [
            models.Index(fields=['suggestion']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['priority', '-click_count']),
        ]
    
    def __str__(self):
        return self.suggestion
    
    def increment_click(self):
        """زيادة عداد النقرات"""
        self.click_count += 1
        self.save(update_fields=['click_count'])


class SearchFilter(models.Model):
    """مرشحات البحث المحفوظة"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_filters',
        verbose_name='المستخدم'
    )
    
    name = models.CharField(max_length=100, verbose_name='اسم المرشح')
    filters = models.JSONField(verbose_name='المرشحات')
    
    # إعدادات
    is_default = models.BooleanField(default=False, verbose_name='افتراضي')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'مرشح محفوظ'
        verbose_name_plural = 'المرشحات المحفوظة'
        ordering = ['-is_default', 'name']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f'{self.name} - {self.user.get_full_name()}'


class SearchIndex(models.Model):
    """فهرس البحث للمحتوى"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # الكائن المفهرس
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='نوع المحتوى'
    )
    object_id = models.PositiveIntegerField(verbose_name='معرف الكائن')
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # محتوى البحث
    title = models.CharField(max_length=500, verbose_name='العنوان')
    content = models.TextField(verbose_name='المحتوى')
    keywords = models.TextField(blank=True, verbose_name='الكلمات المفتاحية')
    
    # معلومات إضافية
    category = models.CharField(max_length=100, blank=True, verbose_name='الفئة')
    tags = models.JSONField(default=list, blank=True, verbose_name='العلامات')
    
    # إعدادات الفهرسة
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    search_weight = models.PositiveIntegerField(default=1, verbose_name='وزن البحث')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الفهرسة')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'فهرس بحث'
        verbose_name_plural = 'فهارس البحث'
        ordering = ['-search_weight', 'title']
        unique_together = ['content_type', 'object_id']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['content']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active', '-search_weight']),
        ]
    
    def __str__(self):
        return self.title


class SearchAnalytics(models.Model):
    """تحليلات البحث"""
    
    date = models.DateField(verbose_name='التاريخ')
    
    # إحصائيات يومية
    total_searches = models.PositiveIntegerField(default=0, verbose_name='إجمالي البحثات')
    unique_users = models.PositiveIntegerField(default=0, verbose_name='المستخدمون الفريدون')
    avg_results_per_search = models.FloatField(default=0, verbose_name='متوسط النتائج لكل بحث')
    
    # أشهر البحثات
    top_queries = models.JSONField(default=list, blank=True, verbose_name='أشهر البحثات')
    
    # معدلات النقر
    click_through_rate = models.FloatField(default=0, verbose_name='معدل النقر')
    
    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'تحليلات البحث'
        verbose_name_plural = 'تحليلات البحث'
        ordering = ['-date']
        unique_together = ['date']
    
    def __str__(self):
        return f'تحليلات {self.date} - {self.total_searches} بحث'


class SearchClick(models.Model):
    """نقرات نتائج البحث"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # المستخدم والجلسة
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='search_clicks',
        verbose_name='المستخدم'
    )
    session_key = models.CharField(max_length=40, blank=True, verbose_name='مفتاح الجلسة')
    
    # تفاصيل البحث
    query = models.CharField(max_length=500, verbose_name='استعلام البحث')
    
    # النتيجة المنقورة
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='نوع المحتوى'
    )
    object_id = models.PositiveIntegerField(verbose_name='معرف الكائن')
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # معلومات النقرة
    result_position = models.PositiveIntegerField(verbose_name='موضع النتيجة')
    
    # تواريخ
    clicked_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ النقرة')
    
    class Meta:
        verbose_name = 'نقرة بحث'
        verbose_name_plural = 'نقرات البحث'
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['query']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['clicked_at']),
        ]
    
    def __str__(self):
        return f'{self.query} -> {self.content_object}'
