from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, Http404
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from courses.models import Course, Enrollment, Certificate, Review
from .models import UserActivity, CourseAnalytics, DailyStats
import json

User = get_user_model()


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin للتأكد من أن المستخدم مدير"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

    def handle_no_permission(self):
        raise Http404()


class AnalyticsDashboardView(AdminRequiredMixin, TemplateView):
    """لوحة التحليلات الرئيسية"""
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الإحصائيات العامة
        total_users = User.objects.filter(user_type='student').count()
        total_courses = Course.objects.count()
        total_enrollments = Enrollment.objects.count()
        total_certificates = Certificate.objects.count()

        # إحصائيات هذا الشهر
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        monthly_users = User.objects.filter(
            user_type='student',
            created_at__gte=current_month
        ).count()

        monthly_enrollments = Enrollment.objects.filter(
            enrollment_date__gte=current_month
        ).count()

        monthly_completions = Enrollment.objects.filter(
            completion_date__gte=current_month
        ).count()

        monthly_certificates = Certificate.objects.filter(
            issue_date__gte=current_month
        ).count()

        # معدل الإكمال العام
        completion_rate = 0
        if total_enrollments > 0:
            completed_enrollments = Enrollment.objects.filter(
                completion_date__isnull=False
            ).count()
            completion_rate = (completed_enrollments / total_enrollments) * 100

        # أفضل الدورات
        top_courses = Course.objects.annotate(
            enrollment_count=Count('enrollments'),
            completion_count=Count('enrollments', filter=Q(enrollments__completion_date__isnull=False)),
            avg_rating=Avg('enrollments__review__rating')
        ).filter(enrollment_count__gt=0).order_by('-enrollment_count')[:5]

        # النشاط الأخير
        recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:10]

        # الدورات الحديثة
        recent_courses = Course.objects.order_by('-created_at')[:5]

        context.update({
            'total_users': total_users,
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'total_certificates': total_certificates,
            'monthly_users': monthly_users,
            'monthly_enrollments': monthly_enrollments,
            'monthly_completions': monthly_completions,
            'monthly_certificates': monthly_certificates,
            'completion_rate': completion_rate,
            'top_courses': top_courses,
            'recent_activities': recent_activities,
            'recent_courses': recent_courses,
        })

        return context


class CourseAnalyticsView(AdminRequiredMixin, TemplateView):
    """تحليلات الدورات"""
    template_name = 'analytics/courses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات الدورات
        courses = Course.objects.annotate(
            enrollment_count=Count('enrollments'),
            completion_count=Count('enrollments', filter=Q(enrollments__completion_date__isnull=False)),
            avg_rating=Avg('enrollments__review__rating'),
            total_revenue=Sum('enrollments__course__price')
        ).order_by('-enrollment_count')

        # حساب معدل الإكمال لكل دورة
        for course in courses:
            if course.enrollment_count > 0:
                course.completion_rate = (course.completion_count / course.enrollment_count) * 100
            else:
                course.completion_rate = 0

        # إحصائيات حسب الفئة
        category_stats = {}
        for course in courses:
            category = course.category.name
            if category not in category_stats:
                category_stats[category] = {
                    'courses_count': 0,
                    'enrollments_count': 0,
                    'completions_count': 0,
                    'avg_rating': 0,
                    'ratings_count': 0
                }

            category_stats[category]['courses_count'] += 1
            category_stats[category]['enrollments_count'] += course.enrollment_count
            category_stats[category]['completions_count'] += course.completion_count

            if course.avg_rating:
                category_stats[category]['avg_rating'] += course.avg_rating
                category_stats[category]['ratings_count'] += 1

        # حساب متوسط التقييم لكل فئة
        for category in category_stats:
            if category_stats[category]['ratings_count'] > 0:
                category_stats[category]['avg_rating'] /= category_stats[category]['ratings_count']
            else:
                category_stats[category]['avg_rating'] = 0

        context.update({
            'courses': courses,
            'category_stats': category_stats,
        })

        return context


class CourseDetailAnalyticsView(AdminRequiredMixin, TemplateView):
    """تحليلات تفصيلية للدورة"""
    template_name = 'analytics/course_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, pk=course_id)

        # إحصائيات الدورة
        enrollments = course.enrollments.all()
        total_enrollments = enrollments.count()
        completed_enrollments = enrollments.filter(completion_date__isnull=False).count()
        active_enrollments = enrollments.filter(is_active=True, completion_date__isnull=True).count()

        # معدل الإكمال
        completion_rate = 0
        if total_enrollments > 0:
            completion_rate = (completed_enrollments / total_enrollments) * 100

        # متوسط وقت الإكمال
        avg_completion_time = 0
        completed = enrollments.filter(completion_date__isnull=False)
        if completed.exists():
            total_days = sum(
                (enrollment.completion_date - enrollment.enrollment_date).days
                for enrollment in completed
            )
            avg_completion_time = total_days / completed.count()

        # التقييمات
        reviews = Review.objects.filter(enrollment__course=course)
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        rating_distribution = reviews.values('rating').annotate(count=Count('rating')).order_by('rating')

        # التسجيلات الشهرية (آخر 12 شهر)
        monthly_enrollments = []
        for i in range(12):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)

            count = enrollments.filter(
                enrollment_date__gte=month_start,
                enrollment_date__lt=month_end
            ).count()

            monthly_enrollments.append({
                'month': month_start.strftime('%Y-%m'),
                'count': count
            })

        monthly_enrollments.reverse()

        context.update({
            'course': course,
            'total_enrollments': total_enrollments,
            'completed_enrollments': completed_enrollments,
            'active_enrollments': active_enrollments,
            'completion_rate': completion_rate,
            'avg_completion_time': avg_completion_time,
            'avg_rating': avg_rating,
            'rating_distribution': rating_distribution,
            'monthly_enrollments': monthly_enrollments,
        })

        return context


class UserAnalyticsView(AdminRequiredMixin, TemplateView):
    """تحليلات المستخدمين"""
    template_name = 'analytics/users.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات المستخدمين
        total_students = User.objects.filter(user_type='student').count()
        active_students = User.objects.filter(
            user_type='student',
            enrollments__is_active=True
        ).distinct().count()

        # الطلاب الجدد (آخر 30 يوم)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_students = User.objects.filter(
            user_type='student',
            created_at__gte=thirty_days_ago
        ).count()

        # أفضل الطلاب (حسب عدد الدورات المكتملة)
        top_students = User.objects.filter(user_type='student').annotate(
            completed_courses=Count('enrollments', filter=Q(enrollments__completion_date__isnull=False)),
            total_enrollments=Count('enrollments'),
            certificates_count=Count('enrollments__certificate')
        ).filter(completed_courses__gt=0).order_by('-completed_courses')[:10]

        # التسجيلات الشهرية للطلاب
        monthly_registrations = []
        for i in range(12):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)

            count = User.objects.filter(
                user_type='student',
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()

            monthly_registrations.append({
                'month': month_start.strftime('%Y-%m'),
                'count': count
            })

        monthly_registrations.reverse()

        context.update({
            'total_students': total_students,
            'active_students': active_students,
            'new_students': new_students,
            'top_students': top_students,
            'monthly_registrations': monthly_registrations,
        })

        return context


class UserDetailAnalyticsView(AdminRequiredMixin, TemplateView):
    """تحليلات تفصيلية للمستخدم"""
    template_name = 'analytics/user_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_id = kwargs.get('user_id')
        user = get_object_or_404(User, pk=user_id)

        # إحصائيات المستخدم
        enrollments = user.enrollments.all()
        total_enrollments = enrollments.count()
        completed_enrollments = enrollments.filter(completion_date__isnull=False).count()
        active_enrollments = enrollments.filter(is_active=True, completion_date__isnull=True).count()
        certificates_count = Certificate.objects.filter(enrollment__student=user).count()

        # معدل الإكمال
        completion_rate = 0
        if total_enrollments > 0:
            completion_rate = (completed_enrollments / total_enrollments) * 100

        # متوسط وقت الإكمال
        avg_completion_time = 0
        completed = enrollments.filter(completion_date__isnull=False)
        if completed.exists():
            total_days = sum(
                (enrollment.completion_date - enrollment.enrollment_date).days
                for enrollment in completed
            )
            avg_completion_time = total_days / completed.count()

        # النشاط الأخير
        recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:20]

        # التقييمات المقدمة
        reviews = Review.objects.filter(enrollment__student=user)
        avg_rating_given = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

        context.update({
            'student': user,
            'total_enrollments': total_enrollments,
            'completed_enrollments': completed_enrollments,
            'active_enrollments': active_enrollments,
            'certificates_count': certificates_count,
            'completion_rate': completion_rate,
            'avg_completion_time': avg_completion_time,
            'recent_activities': recent_activities,
            'avg_rating_given': avg_rating_given,
        })

        return context


class ReportsView(AdminRequiredMixin, TemplateView):
    """صفحة التقارير"""
    template_name = 'analytics/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # تقارير جاهزة
        reports = [
            {
                'name': 'تقرير التسجيلات الشهرية',
                'description': 'إحصائيات التسجيلات في الدورات حسب الشهر',
                'url': 'enrollment_monthly'
            },
            {
                'name': 'تقرير معدلات الإكمال',
                'description': 'معدلات إكمال الدورات حسب الفئة والمستوى',
                'url': 'completion_rates'
            },
            {
                'name': 'تقرير الإيرادات',
                'description': 'إجمالي الإيرادات من الدورات المدفوعة',
                'url': 'revenue_report'
            },
            {
                'name': 'تقرير التقييمات',
                'description': 'تحليل تقييمات الطلاب للدورات',
                'url': 'ratings_report'
            },
            {
                'name': 'تقرير الشهادات',
                'description': 'إحصائيات الشهادات الصادرة',
                'url': 'certificates_report'
            }
        ]

        context['reports'] = reports
        return context


# API Views للرسوم البيانية
class EnrollmentTrendsAPIView(AdminRequiredMixin, TemplateView):
    """API لاتجاهات التسجيل"""

    def get(self, request, *args, **kwargs):
        # آخر 12 شهر
        data = []
        for i in range(12):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)

            enrollments = Enrollment.objects.filter(
                enrollment_date__gte=month_start,
                enrollment_date__lt=month_end
            ).count()

            completions = Enrollment.objects.filter(
                completion_date__gte=month_start,
                completion_date__lt=month_end
            ).count()

            data.append({
                'month': month_start.strftime('%Y-%m'),
                'enrollments': enrollments,
                'completions': completions
            })

        data.reverse()
        return JsonResponse({'data': data})


class CompletionRatesAPIView(AdminRequiredMixin, TemplateView):
    """API لمعدلات الإكمال"""

    def get(self, request, *args, **kwargs):
        courses = Course.objects.annotate(
            enrollment_count=Count('enrollments'),
            completion_count=Count('enrollments', filter=Q(enrollments__completion_date__isnull=False))
        ).filter(enrollment_count__gt=0)

        data = []
        for course in courses:
            completion_rate = (course.completion_count / course.enrollment_count) * 100
            data.append({
                'course_title': course.title,
                'enrollment_count': course.enrollment_count,
                'completion_count': course.completion_count,
                'completion_rate': round(completion_rate, 2)
            })

        return JsonResponse({'data': data})


class UserActivityAPIView(AdminRequiredMixin, TemplateView):
    """API لنشاط المستخدمين"""

    def get(self, request, *args, **kwargs):
        # آخر 7 أيام
        data = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)

            activities = UserActivity.objects.filter(
                timestamp__date=date
            ).count()

            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'activities': activities
            })

        data.reverse()
        return JsonResponse({'data': data})
