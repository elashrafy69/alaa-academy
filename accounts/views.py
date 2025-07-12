from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, UserProfileForm
from .models import User


class RegisterView(CreateView):
    """عرض التسجيل"""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إنشاء حسابك بنجاح! يمكنك الآن تسجيل الدخول.')
        )
        return response

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, UpdateView):
    """عرض الملف الشخصي"""
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث ملفك الشخصي بنجاح!')
        )
        return response


@login_required
def dashboard_view(request):
    """لوحة التحكم الرئيسية"""
    user = request.user

    if user.is_admin:
        # إحصائيات للمدير
        from courses.models import Course, Enrollment
        from analytics.models import DailyStats
        from django.utils import timezone
        from datetime import timedelta

        context = {
            'total_courses': Course.objects.count(),
            'total_students': User.objects.filter(user_type='student').count(),
            'total_enrollments': Enrollment.objects.count(),
            'recent_enrollments': Enrollment.objects.select_related(
                'student', 'course'
            ).order_by('-enrollment_date')[:10],
            'recent_courses': Course.objects.order_by('-created_at')[:5],
        }

        # إحصائيات الأسبوع الماضي
        week_ago = timezone.now().date() - timedelta(days=7)
        weekly_stats = DailyStats.objects.filter(date__gte=week_ago)

        context.update({
            'weekly_new_users': sum(stat.new_users for stat in weekly_stats),
            'weekly_enrollments': sum(stat.new_enrollments for stat in weekly_stats),
            'weekly_completions': sum(stat.completed_courses for stat in weekly_stats),
        })

        return render(request, 'accounts/admin_dashboard.html', context)

    else:
        # لوحة تحكم الطالب
        from courses.models import Enrollment

        enrollments = Enrollment.objects.filter(
            student=user, is_active=True
        ).select_related('course').order_by('-enrollment_date')

        context = {
            'enrollments': enrollments,
            'total_courses': enrollments.count(),
            'completed_courses': enrollments.filter(completion_date__isnull=False).count(),
            'in_progress_courses': enrollments.filter(completion_date__isnull=True).count(),
        }

        return render(request, 'accounts/student_dashboard.html', context)


def custom_login_view(request):
    """عرض تسجيل الدخول المخصص"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    from django.contrib.auth.views import LoginView
    from .forms import CustomAuthenticationForm

    class CustomLoginView(LoginView):
        form_class = CustomAuthenticationForm
        template_name = 'accounts/login.html'

        def get_success_url(self):
            return reverse_lazy('dashboard')

        def form_valid(self, form):
            response = super().form_valid(form)
            messages.success(
                self.request,
                _('مرحباً بك! تم تسجيل دخولك بنجاح.')
            )
            return response

    return CustomLoginView.as_view()(request)
