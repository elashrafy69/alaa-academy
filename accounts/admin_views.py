"""
Views خاصة بإدارة الطلاب والمستخدمين
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.views import View
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from courses.models import Course, Enrollment, Certificate, Review
from .models import RegistrationCode
from .forms import RegistrationCodeForm, StudentEditForm
import csv
import json
from datetime import datetime, timedelta

User = get_user_model()


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin للتأكد من أن المستخدم مدير"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin
    
    def handle_no_permission(self):
        raise Http404()


class StudentManagementView(AdminRequiredMixin, ListView):
    """إدارة الطلاب الرئيسية"""
    model = User
    template_name = 'accounts/admin/student_management.html'
    context_object_name = 'students'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(user_type='student').annotate(
            enrollments_count=Count('enrollments'),
            completed_courses=Count('enrollments', filter=Q(enrollments__completion_date__isnull=False)),
            certificates_count=Count('enrollments__certificate')
        ).order_by('-created_at')
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        # فلترة حسب الحالة
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'enrolled':
            queryset = queryset.filter(enrollments__is_active=True).distinct()
        
        # فلترة حسب تاريخ التسجيل
        date_filter = self.request.GET.get('date_filter')
        if date_filter == 'today':
            queryset = queryset.filter(created_at__date=timezone.now().date())
        elif date_filter == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=week_ago)
        elif date_filter == 'month':
            month_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(created_at__gte=month_ago)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إحصائيات عامة
        total_students = User.objects.filter(user_type='student').count()
        active_students = User.objects.filter(user_type='student', is_active=True).count()
        new_students_today = User.objects.filter(
            user_type='student',
            created_at__date=timezone.now().date()
        ).count()
        
        # الطلاب المسجلين حالياً
        enrolled_students = User.objects.filter(
            user_type='student',
            enrollments__is_active=True
        ).distinct().count()
        
        context.update({
            'total_students': total_students,
            'active_students': active_students,
            'new_students_today': new_students_today,
            'enrolled_students': enrolled_students,
            'search_query': self.request.GET.get('search', ''),
            'status_filter': self.request.GET.get('status', ''),
            'date_filter': self.request.GET.get('date_filter', ''),
        })
        
        return context


class StudentDetailView(AdminRequiredMixin, DetailView):
    """تفاصيل الطالب"""
    model = User
    template_name = 'accounts/admin/student_detail.html'
    context_object_name = 'student'
    
    def get_queryset(self):
        return User.objects.filter(user_type='student')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object
        
        # تسجيلات الطالب
        enrollments = student.enrollments.select_related('course').order_by('-enrollment_date')
        
        # إحصائيات الطالب
        total_enrollments = enrollments.count()
        completed_courses = enrollments.filter(completion_date__isnull=False).count()
        active_enrollments = enrollments.filter(is_active=True, completion_date__isnull=True).count()
        certificates = Certificate.objects.filter(enrollment__student=student).count()
        
        # معدل الإكمال
        completion_rate = 0
        if total_enrollments > 0:
            completion_rate = (completed_courses / total_enrollments) * 100
        
        # متوسط وقت الإكمال
        avg_completion_time = 0
        completed = enrollments.filter(completion_date__isnull=False)
        if completed.exists():
            total_days = sum(
                (enrollment.completion_date - enrollment.enrollment_date).days
                for enrollment in completed
            )
            avg_completion_time = total_days / completed.count()
        
        # التقييمات المقدمة
        reviews = Review.objects.filter(enrollment__student=student)
        avg_rating_given = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        
        # النشاط الأخير
        from analytics.models import UserActivity
        recent_activities = UserActivity.objects.filter(user=student).order_by('-timestamp')[:10]
        
        context.update({
            'enrollments': enrollments[:10],  # أول 10 تسجيلات
            'total_enrollments': total_enrollments,
            'completed_courses': completed_courses,
            'active_enrollments': active_enrollments,
            'certificates': certificates,
            'completion_rate': completion_rate,
            'avg_completion_time': avg_completion_time,
            'avg_rating_given': avg_rating_given,
            'recent_activities': recent_activities,
        })
        
        return context


class StudentEditView(AdminRequiredMixin, UpdateView):
    """تعديل بيانات الطالب"""
    model = User
    form_class = StudentEditForm
    template_name = 'accounts/admin/student_edit.html'
    
    def get_queryset(self):
        return User.objects.filter(user_type='student')
    
    def get_success_url(self):
        return reverse('accounts:admin_student_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث بيانات الطالب بنجاح')
        return super().form_valid(form)


class RegistrationCodeManagementView(AdminRequiredMixin, ListView):
    """إدارة أكواد التسجيل"""
    model = RegistrationCode
    template_name = 'accounts/admin/registration_codes.html'
    context_object_name = 'codes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = RegistrationCode.objects.select_related('course', 'created_by').order_by('-created_at')
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(course__title__icontains=search)
            )
        
        # فلترة حسب الحالة
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True, expires_at__gt=timezone.now())
        elif status == 'expired':
            queryset = queryset.filter(Q(expires_at__lt=timezone.now()) | Q(is_active=False))
        elif status == 'used':
            queryset = queryset.filter(usage_count__gte=1)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إحصائيات الأكواد
        total_codes = RegistrationCode.objects.count()
        active_codes = RegistrationCode.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()
        used_codes = RegistrationCode.objects.filter(usage_count__gte=1).count()
        
        context.update({
            'total_codes': total_codes,
            'active_codes': active_codes,
            'used_codes': used_codes,
            'search_query': self.request.GET.get('search', ''),
            'status_filter': self.request.GET.get('status', ''),
        })
        
        return context


class RegistrationCodeCreateView(AdminRequiredMixin, CreateView):
    """إنشاء كود تسجيل جديد"""
    model = RegistrationCode
    form_class = RegistrationCodeForm
    template_name = 'accounts/admin/registration_code_create.html'
    success_url = reverse_lazy('accounts:admin_registration_codes')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'تم إنشاء كود التسجيل بنجاح')
        return super().form_valid(form)


@login_required
def bulk_registration_codes(request):
    """إنشاء أكواد تسجيل مجمعة"""
    if not request.user.is_admin:
        raise Http404()
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            count = int(data.get('count', 1))
            expires_days = int(data.get('expires_days', 30))
            max_uses = int(data.get('max_uses', 1))
            
            if count > 100:
                return JsonResponse({
                    'status': 'error',
                    'message': 'لا يمكن إنشاء أكثر من 100 كود في المرة الواحدة'
                })
            
            course = get_object_or_404(Course, pk=course_id)
            expires_at = timezone.now() + timedelta(days=expires_days)
            
            codes = []
            for i in range(count):
                code = RegistrationCode.objects.create(
                    course=course,
                    expires_at=expires_at,
                    max_uses=max_uses,
                    created_by=request.user
                )
                codes.append({
                    'code': code.code,
                    'course': course.title,
                    'expires_at': code.expires_at.strftime('%Y-%m-%d'),
                    'max_uses': code.max_uses
                })
            
            return JsonResponse({
                'status': 'success',
                'message': f'تم إنشاء {count} كود بنجاح',
                'codes': codes
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطأ في إنشاء الأكواد: {str(e)}'
            })
    
    courses = Course.objects.filter(status='published')
    return render(request, 'accounts/admin/bulk_registration_codes.html', {
        'courses': courses
    })


@login_required
def export_students_csv(request):
    """تصدير بيانات الطلاب كـ CSV"""
    if not request.user.is_admin:
        raise Http404()
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'
    response.write('\ufeff')  # BOM for UTF-8
    
    writer = csv.writer(response)
    writer.writerow([
        'الاسم الأول', 'الاسم الأخير', 'البريد الإلكتروني', 'الهاتف',
        'تاريخ التسجيل', 'الحالة', 'عدد الدورات', 'الدورات المكتملة', 'الشهادات'
    ])
    
    students = User.objects.filter(user_type='student').annotate(
        enrollments_count=Count('enrollments'),
        completed_courses=Count('enrollments', filter=Q(enrollments__completion_date__isnull=False)),
        certificates_count=Count('enrollments__certificate')
    )
    
    for student in students:
        writer.writerow([
            student.first_name,
            student.last_name,
            student.email,
            student.phone or '',
            student.created_at.strftime('%Y-%m-%d'),
            'نشط' if student.is_active else 'غير نشط',
            student.enrollments_count,
            student.completed_courses,
            student.certificates_count
        ])
    
    return response


@login_required
def student_bulk_actions(request):
    """إجراءات مجمعة على الطلاب"""
    if not request.user.is_admin:
        raise Http404()
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            student_ids = data.get('student_ids', [])
            
            if not student_ids:
                return JsonResponse({
                    'status': 'error',
                    'message': 'لم يتم اختيار أي طلاب'
                })
            
            students = User.objects.filter(
                pk__in=student_ids,
                user_type='student'
            )
            
            if action == 'activate':
                students.update(is_active=True)
                message = f'تم تفعيل {students.count()} طالب'
                
            elif action == 'deactivate':
                students.update(is_active=False)
                message = f'تم إلغاء تفعيل {students.count()} طالب'
                
            elif action == 'delete':
                count = students.count()
                students.delete()
                message = f'تم حذف {count} طالب'
                
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'إجراء غير صحيح'
                })
            
            return JsonResponse({
                'status': 'success',
                'message': message
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطأ في تنفيذ الإجراء: {str(e)}'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'طريقة غير مدعومة'
    })
