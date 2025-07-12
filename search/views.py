"""
Views نظام البحث المتقدم
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q, Count
from courses.models import Course, Category
from accounts.models import User
from .models import SearchSuggestion, PopularSearch, SearchFilter
from .services import SearchService
import json


class SearchView(TemplateView):
    """صفحة البحث الرئيسية"""
    template_name = 'search/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        query = self.request.GET.get('q', '').strip()
        page = int(self.request.GET.get('page', 1))
        
        # المرشحات
        filters = {
            'category': self.request.GET.get('category'),
            'difficulty': self.request.GET.get('difficulty'),
            'price_range': self.request.GET.get('price_range'),
            'duration_range': self.request.GET.get('duration_range'),
        }
        
        # إزالة المرشحات الفارغة
        filters = {k: v for k, v in filters.items() if v}
        
        # تنفيذ البحث
        if query:
            search_results = SearchService.search(
                query=query,
                filters=filters,
                user=self.request.user if self.request.user.is_authenticated else None,
                page=page,
                per_page=20,
                session_key=self.request.session.session_key,
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        else:
            search_results = SearchService._empty_result()
        
        # البيانات الإضافية
        categories = Category.objects.all()
        popular_searches = SearchService.get_popular_searches(limit=8)
        trending_searches = SearchService.get_trending_searches(limit=6)
        
        context.update({
            'query': query,
            'search_results': search_results,
            'categories': categories,
            'popular_searches': popular_searches,
            'trending_searches': trending_searches,
            'current_filters': filters,
            'difficulty_choices': Course.DIFFICULTY_CHOICES,
        })
        
        return context
    
    def get_client_ip(self):
        """الحصول على عنوان IP للعميل"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class SearchAPIView(TemplateView):
    """API البحث للاستخدام مع AJAX"""
    
    def get(self, request, *args, **kwargs):
        """البحث عبر API"""
        
        query = request.GET.get('q', '').strip()
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        
        if not query:
            return JsonResponse({
                'status': 'error',
                'message': 'استعلام البحث مطلوب'
            })
        
        # المرشحات
        filters = {}
        for key in ['category', 'difficulty', 'price_range', 'duration_range']:
            value = request.GET.get(key)
            if value:
                filters[key] = value
        
        try:
            # تنفيذ البحث
            search_results = SearchService.search(
                query=query,
                filters=filters,
                user=request.user if request.user.is_authenticated else None,
                page=page,
                per_page=per_page,
                session_key=request.session.session_key,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # تحويل النتائج للتسلسل
            results_data = []
            for result in search_results['results']:
                results_data.append({
                    'type': result['type'],
                    'title': result['title'],
                    'description': result['description'],
                    'url': result['url'],
                    'score': result['score'],
                    'position': result['position'],
                    'highlight': result['highlight'],
                    'metadata': result['metadata']
                })
            
            return JsonResponse({
                'status': 'success',
                'query': search_results['query'],
                'results': results_data,
                'total_count': search_results['total_count'],
                'page': search_results['page'],
                'per_page': search_results['per_page'],
                'total_pages': search_results['total_pages'],
                'has_next': search_results['has_next'],
                'has_previous': search_results['has_previous'],
                'suggestions': search_results['suggestions']
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطأ في البحث: {str(e)}'
            })
    
    def _get_client_ip(self, request):
        """الحصول على عنوان IP للعميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SearchSuggestionsAPIView(TemplateView):
    """API اقتراحات البحث"""
    
    def get(self, request, *args, **kwargs):
        """الحصول على اقتراحات البحث"""
        
        query = request.GET.get('q', '').strip()
        limit = int(request.GET.get('limit', 10))
        
        if len(query) < 2:
            return JsonResponse({
                'status': 'success',
                'suggestions': []
            })
        
        try:
            suggestions = SearchService.get_search_suggestions(query, limit)
            
            return JsonResponse({
                'status': 'success',
                'suggestions': suggestions
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطأ في الحصول على الاقتراحات: {str(e)}'
            })


@method_decorator(csrf_exempt, name='dispatch')
class SearchClickAPIView(TemplateView):
    """API تسجيل النقرات"""
    
    def post(self, request, *args, **kwargs):
        """تسجيل نقرة على نتيجة البحث"""
        
        try:
            data = json.loads(request.body)
            
            query = data.get('query', '').strip()
            content_type_name = data.get('content_type')
            object_id = data.get('object_id')
            position = data.get('position', 1)
            
            if not all([query, content_type_name, object_id]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'بيانات غير مكتملة'
                })
            
            # الحصول على نوع المحتوى
            content_type = ContentType.objects.get(model=content_type_name)
            content_object = content_type.get_object_for_this_type(pk=object_id)
            
            # تسجيل النقرة
            SearchService.record_click(
                query=query,
                content_object=content_object,
                position=position,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'تم تسجيل النقرة'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطأ في تسجيل النقرة: {str(e)}'
            })


class PopularSearchesView(TemplateView):
    """صفحة البحثات الشائعة"""
    template_name = 'search/popular_searches.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        popular_searches = SearchService.get_popular_searches(limit=20)
        trending_searches = SearchService.get_trending_searches(limit=15)
        
        context.update({
            'popular_searches': popular_searches,
            'trending_searches': trending_searches,
        })
        
        return context


class SearchFiltersView(TemplateView):
    """إدارة مرشحات البحث المحفوظة"""
    template_name = 'search/filters.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            saved_filters = SearchFilter.objects.filter(
                user=self.request.user
            ).order_by('-is_default', 'name')
        else:
            saved_filters = []
        
        context.update({
            'saved_filters': saved_filters,
            'categories': Category.objects.all(),
            'difficulty_choices': Course.DIFFICULTY_CHOICES,
        })
        
        return context


@method_decorator(csrf_exempt, name='dispatch')
class SaveFilterAPIView(TemplateView):
    """API حفظ مرشح البحث"""
    
    def post(self, request, *args, **kwargs):
        """حفظ مرشح بحث جديد"""
        
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'يجب تسجيل الدخول أولاً'
            })
        
        try:
            data = json.loads(request.body)
            
            name = data.get('name', '').strip()
            filters = data.get('filters', {})
            is_default = data.get('is_default', False)
            
            if not name:
                return JsonResponse({
                    'status': 'error',
                    'message': 'اسم المرشح مطلوب'
                })
            
            # التحقق من عدم وجود مرشح بنفس الاسم
            if SearchFilter.objects.filter(user=request.user, name=name).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'يوجد مرشح بهذا الاسم بالفعل'
                })
            
            # إزالة الافتراضي من المرشحات الأخرى إذا كان هذا افتراضي
            if is_default:
                SearchFilter.objects.filter(
                    user=request.user,
                    is_default=True
                ).update(is_default=False)
            
            # إنشاء المرشح الجديد
            search_filter = SearchFilter.objects.create(
                user=request.user,
                name=name,
                filters=filters,
                is_default=is_default
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'تم حفظ المرشح بنجاح',
                'filter_id': str(search_filter.id)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطأ في حفظ المرشح: {str(e)}'
            })


def delete_filter(request, filter_id):
    """حذف مرشح محفوظ"""
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'غير مصرح'
        }, status=403)
    
    if request.method == 'POST':
        try:
            search_filter = get_object_or_404(
                SearchFilter,
                id=filter_id,
                user=request.user
            )
            
            search_filter.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': 'تم حذف المرشح بنجاح'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطأ في حذف المرشح: {str(e)}'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'طريقة غير مدعومة'
    })


def search_redirect(request):
    """إعادة توجيه البحث السريع"""
    
    query = request.GET.get('q', '').strip()
    if query:
        return redirect(f'/search/?q={query}')
    
    return redirect('/search/')
