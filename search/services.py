"""
خدمات البحث المتقدم
"""

from django.db.models import Q, Count, Avg
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.paginator import Paginator
from courses.models import Course, CourseContent
from accounts.models import User
from .models import (
    SearchQuery, PopularSearch, SearchSuggestion, 
    SearchIndex, SearchClick, SearchAnalytics
)
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """خدمة البحث المتقدم"""
    
    # أوزان البحث لأنواع المحتوى المختلفة
    CONTENT_WEIGHTS = {
        'course': 10,
        'instructor': 8,
        'content': 6,
        'category': 4,
    }
    
    @classmethod
    def search(
        cls,
        query: str,
        filters: Optional[Dict] = None,
        user: Optional[User] = None,
        page: int = 1,
        per_page: int = 20,
        session_key: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """تنفيذ البحث المتقدم"""
        
        if not query or not query.strip():
            return cls._empty_result()
        
        query = query.strip()
        filters = filters or {}
        
        # تسجيل استعلام البحث
        search_query = cls._log_search_query(
            query, filters, user, session_key, ip_address, user_agent
        )
        
        # تحديث البحثات الشائعة
        PopularSearch.increment_search(query)
        
        # تنفيذ البحث
        results = cls._perform_search(query, filters)
        
        # ترقيم الصفحات
        paginator = Paginator(results, per_page)
        page_obj = paginator.get_page(page)
        
        # تحديث عدد النتائج
        search_query.results_count = paginator.count
        search_query.save(update_fields=['results_count'])
        
        # إعداد النتائج للإرجاع
        search_results = []
        for i, result in enumerate(page_obj.object_list, start=(page - 1) * per_page + 1):
            search_results.append({
                'object': result['object'],
                'type': result['type'],
                'title': result['title'],
                'description': result['description'],
                'url': result['url'],
                'score': result['score'],
                'position': i,
                'highlight': cls._highlight_text(result['title'], query),
                'metadata': result.get('metadata', {})
            })
        
        return {
            'query': query,
            'results': search_results,
            'total_count': paginator.count,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'suggestions': cls.get_search_suggestions(query),
            'filters_applied': filters,
            'search_time': timezone.now()
        }
    
    @classmethod
    def _perform_search(cls, query: str, filters: Dict) -> List[Dict]:
        """تنفيذ البحث الفعلي"""
        
        results = []
        search_terms = cls._parse_query(query)
        
        # البحث في الدورات
        course_results = cls._search_courses(search_terms, filters)
        results.extend(course_results)
        
        # البحث في المدربين
        instructor_results = cls._search_instructors(search_terms, filters)
        results.extend(instructor_results)
        
        # البحث في محتوى الدورات
        content_results = cls._search_course_content(search_terms, filters)
        results.extend(content_results)
        
        # ترتيب النتائج حسب النقاط
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    @classmethod
    def _search_courses(cls, search_terms: List[str], filters: Dict) -> List[Dict]:
        """البحث في الدورات"""
        
        queryset = Course.objects.filter(status='published')
        
        # تطبيق المرشحات
        if filters.get('category'):
            queryset = queryset.filter(category_id=filters['category'])
        
        if filters.get('difficulty'):
            queryset = queryset.filter(difficulty_level=filters['difficulty'])
        
        if filters.get('price_range'):
            price_range = filters['price_range']
            if price_range == 'free':
                queryset = queryset.filter(price=0)
            elif price_range == 'paid':
                queryset = queryset.filter(price__gt=0)
        
        if filters.get('duration_range'):
            duration = filters['duration_range']
            if duration == 'short':
                queryset = queryset.filter(estimated_duration__lt=10)
            elif duration == 'medium':
                queryset = queryset.filter(estimated_duration__gte=10, estimated_duration__lt=30)
            elif duration == 'long':
                queryset = queryset.filter(estimated_duration__gte=30)
        
        # البحث النصي
        search_q = Q()
        for term in search_terms:
            search_q |= (
                Q(title__icontains=term) |
                Q(short_description__icontains=term) |
                Q(description__icontains=term) |
                Q(tags__icontains=term)
            )
        
        courses = queryset.filter(search_q).select_related('category', 'instructor')
        
        results = []
        for course in courses:
            score = cls._calculate_course_score(course, search_terms)
            results.append({
                'object': course,
                'type': 'course',
                'title': course.title,
                'description': course.short_description,
                'url': f'/courses/{course.pk}/',
                'score': score,
                'metadata': {
                    'category': course.category.name,
                    'instructor': course.instructor.get_full_name(),
                    'price': course.price,
                    'duration': course.estimated_duration,
                    'difficulty': course.get_difficulty_level_display(),
                    'enrollment_count': course.enrollment_count,
                    'rating': course.average_rating
                }
            })
        
        return results
    
    @classmethod
    def _search_instructors(cls, search_terms: List[str], filters: Dict) -> List[Dict]:
        """البحث في المدربين"""
        
        queryset = User.objects.filter(user_type='instructor', is_active=True)
        
        # البحث النصي
        search_q = Q()
        for term in search_terms:
            search_q |= (
                Q(first_name__icontains=term) |
                Q(last_name__icontains=term) |
                Q(bio__icontains=term) |
                Q(specialization__icontains=term)
            )
        
        instructors = queryset.filter(search_q)
        
        results = []
        for instructor in instructors:
            score = cls._calculate_instructor_score(instructor, search_terms)
            results.append({
                'object': instructor,
                'type': 'instructor',
                'title': instructor.get_full_name(),
                'description': instructor.bio or 'مدرب معتمد',
                'url': f'/instructors/{instructor.pk}/',
                'score': score,
                'metadata': {
                    'specialization': instructor.specialization,
                    'courses_count': instructor.courses.filter(status='published').count(),
                    'students_count': instructor.total_students,
                    'rating': instructor.average_rating
                }
            })
        
        return results
    
    @classmethod
    def _search_course_content(cls, search_terms: List[str], filters: Dict) -> List[Dict]:
        """البحث في محتوى الدورات"""
        
        queryset = CourseContent.objects.filter(
            course__status='published',
            is_published=True
        )
        
        # البحث النصي
        search_q = Q()
        for term in search_terms:
            search_q |= (
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(content__icontains=term)
            )
        
        contents = queryset.filter(search_q).select_related('course')
        
        results = []
        for content in contents:
            score = cls._calculate_content_score(content, search_terms)
            results.append({
                'object': content,
                'type': 'content',
                'title': f'{content.course.title} - {content.title}',
                'description': content.description or 'محتوى الدورة',
                'url': f'/courses/{content.course.pk}/content/{content.pk}/',
                'score': score,
                'metadata': {
                    'course': content.course.title,
                    'type': content.get_content_type_display(),
                    'duration': content.duration,
                    'order': content.order
                }
            })
        
        return results
    
    @classmethod
    def _calculate_course_score(cls, course: Course, search_terms: List[str]) -> float:
        """حساب نقاط الدورة"""
        
        score = 0
        base_weight = cls.CONTENT_WEIGHTS['course']
        
        # نقاط العنوان
        title_matches = sum(1 for term in search_terms if term.lower() in course.title.lower())
        score += title_matches * base_weight * 3
        
        # نقاط الوصف
        desc_matches = sum(1 for term in search_terms if term.lower() in course.short_description.lower())
        score += desc_matches * base_weight * 2
        
        # نقاط التفاصيل
        detail_matches = sum(1 for term in search_terms if term.lower() in course.description.lower())
        score += detail_matches * base_weight
        
        # مكافآت إضافية
        score += course.enrollment_count * 0.1  # شعبية الدورة
        score += (course.average_rating or 0) * 2  # تقييم الدورة
        
        if course.is_featured:
            score += 5  # دورة مميزة
        
        return score
    
    @classmethod
    def _calculate_instructor_score(cls, instructor: User, search_terms: List[str]) -> float:
        """حساب نقاط المدرب"""
        
        score = 0
        base_weight = cls.CONTENT_WEIGHTS['instructor']
        
        # نقاط الاسم
        name = f'{instructor.first_name} {instructor.last_name}'.lower()
        name_matches = sum(1 for term in search_terms if term.lower() in name)
        score += name_matches * base_weight * 3
        
        # نقاط التخصص
        if instructor.specialization:
            spec_matches = sum(1 for term in search_terms if term.lower() in instructor.specialization.lower())
            score += spec_matches * base_weight * 2
        
        # نقاط السيرة الذاتية
        if instructor.bio:
            bio_matches = sum(1 for term in search_terms if term.lower() in instructor.bio.lower())
            score += bio_matches * base_weight
        
        # مكافآت إضافية
        score += instructor.total_students * 0.05
        score += (instructor.average_rating or 0) * 2
        
        return score
    
    @classmethod
    def _calculate_content_score(cls, content: CourseContent, search_terms: List[str]) -> float:
        """حساب نقاط المحتوى"""
        
        score = 0
        base_weight = cls.CONTENT_WEIGHTS['content']
        
        # نقاط العنوان
        title_matches = sum(1 for term in search_terms if term.lower() in content.title.lower())
        score += title_matches * base_weight * 2
        
        # نقاط الوصف
        if content.description:
            desc_matches = sum(1 for term in search_terms if term.lower() in content.description.lower())
            score += desc_matches * base_weight
        
        # نقاط المحتوى
        if content.content:
            content_matches = sum(1 for term in search_terms if term.lower() in content.content.lower())
            score += content_matches * base_weight * 0.5
        
        return score
    
    @classmethod
    def _parse_query(cls, query: str) -> List[str]:
        """تحليل استعلام البحث"""
        
        # إزالة الأحرف الخاصة والتقسيم إلى كلمات
        clean_query = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', query)
        terms = [term.strip() for term in clean_query.split() if len(term.strip()) > 1]
        
        return terms
    
    @classmethod
    def _highlight_text(cls, text: str, query: str) -> str:
        """تمييز النص المطابق"""
        
        if not text or not query:
            return text
        
        terms = cls._parse_query(query)
        highlighted = text
        
        for term in terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(f'<mark>{term}</mark>', highlighted)
        
        return highlighted
    
    @classmethod
    def _log_search_query(
        cls,
        query: str,
        filters: Dict,
        user: Optional[User],
        session_key: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> SearchQuery:
        """تسجيل استعلام البحث"""
        
        return SearchQuery.objects.create(
            user=user,
            query=query,
            filters=filters,
            session_key=session_key or '',
            ip_address=ip_address,
            user_agent=user_agent or ''
        )
    
    @classmethod
    def _empty_result(cls) -> Dict[str, Any]:
        """نتيجة فارغة"""
        
        return {
            'query': '',
            'results': [],
            'total_count': 0,
            'page': 1,
            'per_page': 20,
            'total_pages': 0,
            'has_next': False,
            'has_previous': False,
            'suggestions': [],
            'filters_applied': {},
            'search_time': timezone.now()
        }
    
    @classmethod
    def get_search_suggestions(cls, query: str, limit: int = 5) -> List[str]:
        """الحصول على اقتراحات البحث"""
        
        if not query or len(query) < 2:
            return []
        
        # البحث في الاقتراحات المحفوظة
        suggestions = SearchSuggestion.objects.filter(
            suggestion__icontains=query,
            is_active=True
        ).order_by('-priority', '-click_count')[:limit]
        
        result = [s.suggestion for s in suggestions]
        
        # إضافة اقتراحات من البحثات الشائعة
        if len(result) < limit:
            popular = PopularSearch.objects.filter(
                query__icontains=query
            ).order_by('-search_count')[:limit - len(result)]
            
            result.extend([p.query for p in popular])
        
        return result[:limit]
    
    @classmethod
    def record_click(
        cls,
        query: str,
        content_object: Any,
        position: int,
        user: Optional[User] = None,
        session_key: Optional[str] = None
    ):
        """تسجيل نقرة على نتيجة البحث"""
        
        content_type = ContentType.objects.get_for_model(content_object)
        
        SearchClick.objects.create(
            user=user,
            session_key=session_key or '',
            query=query,
            content_type=content_type,
            object_id=content_object.pk,
            result_position=position
        )
    
    @classmethod
    def get_popular_searches(cls, limit: int = 10) -> List[PopularSearch]:
        """الحصول على البحثات الشائعة"""
        
        return PopularSearch.objects.filter(
            search_count__gte=2
        ).order_by('-search_count')[:limit]
    
    @classmethod
    def get_trending_searches(cls, days: int = 7, limit: int = 10) -> List[PopularSearch]:
        """الحصول على البحثات الرائجة"""
        
        since_date = timezone.now() - timedelta(days=days)
        
        return PopularSearch.objects.filter(
            last_searched__gte=since_date,
            search_count__gte=3
        ).order_by('-search_count')[:limit]
