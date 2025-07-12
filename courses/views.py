from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.views import View
from .models import Course, Category, Enrollment, CourseContent, StudentProgress, Certificate, Review
from .forms import CourseForm, CourseContentForm, CategoryForm, EnrollmentForm, BulkEnrollmentForm, ReviewForm
from accounts.models import RegistrationCode


class CourseListView(ListView):
    """عرض قائمة الدورات"""
    model = Course
    template_name = 'courses/list.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        queryset = Course.objects.filter(status='published').select_related('category', 'instructor')

        # فلترة حسب الفئة
        category_id = self.kwargs.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['current_category'] = self.kwargs.get('category_id')
        return context


class CourseDetailView(DetailView):
    """عرض تفاصيل الدورة"""
    model = Course
    template_name = 'courses/detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(
                    student=self.request.user,
                    course=self.object
                )
                context['enrollment'] = enrollment
                context['is_enrolled'] = True
            except Enrollment.DoesNotExist:
                context['is_enrolled'] = False

        return context


# Helper functions
def is_admin(user):
    """فحص ما إذا كان المستخدم مدير"""
    return user.is_authenticated and user.is_admin


# Course Management Views for Admins
class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin للتأكد من أن المستخدم مدير"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

    def handle_no_permission(self):
        messages.error(self.request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('accounts:dashboard')


class CourseCreateView(AdminRequiredMixin, CreateView):
    """إنشاء دورة جديدة"""
    model = Course
    form_class = CourseForm
    template_name = 'courses/admin_create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم إنشاء الدورة "{self.object.title}" بنجاح!')
        return response

    def get_success_url(self):
        return reverse('courses:admin_edit', kwargs={'pk': self.object.pk})


class CourseUpdateView(AdminRequiredMixin, UpdateView):
    """تعديل دورة موجودة"""
    model = Course
    form_class = CourseForm
    template_name = 'courses/admin_edit.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث الدورة "{self.object.title}" بنجاح!')
        return response

    def get_success_url(self):
        return reverse('courses:admin_edit', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_content'] = self.object.content.all().order_by('order_sequence')
        context['enrollments_count'] = self.object.enrollments.count()
        context['completed_count'] = self.object.enrollments.filter(completion_date__isnull=False).count()
        return context


class CourseDeleteView(AdminRequiredMixin, DeleteView):
    """حذف دورة"""
    model = Course
    template_name = 'courses/admin_delete.html'
    success_url = reverse_lazy('courses:admin_list')

    def delete(self, request, *args, **kwargs):
        course = self.get_object()
        messages.success(request, f'تم حذف الدورة "{course.title}" بنجاح!')
        return super().delete(request, *args, **kwargs)


class ContentCreateView(AdminRequiredMixin, CreateView):
    """إضافة محتوى للدورة"""
    model = CourseContent
    form_class = CourseContentForm
    template_name = 'courses/admin_content_add.html'

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=kwargs['course_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = self.course
        return kwargs

    def form_valid(self, form):
        form.instance.course = self.course
        response = super().form_valid(form)
        messages.success(self.request, f'تم إضافة المحتوى "{self.object.title}" بنجاح!')
        return response

    def get_success_url(self):
        return reverse('courses:admin_edit', kwargs={'pk': self.course.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        return context


class ContentUpdateView(AdminRequiredMixin, UpdateView):
    """تعديل محتوى الدورة"""
    model = CourseContent
    form_class = CourseContentForm
    template_name = 'courses/admin_content_edit.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = self.object.course
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث المحتوى "{self.object.title}" بنجاح!')
        return response

    def get_success_url(self):
        return reverse('courses:admin_edit', kwargs={'pk': self.object.course.pk})


class ContentDeleteView(AdminRequiredMixin, DeleteView):
    """حذف محتوى الدورة"""
    model = CourseContent
    template_name = 'courses/admin_content_delete.html'

    def delete(self, request, *args, **kwargs):
        content = self.get_object()
        course_pk = content.course.pk
        messages.success(request, f'تم حذف المحتوى "{content.title}" بنجاح!')
        response = super().delete(request, *args, **kwargs)
        return response

    def get_success_url(self):
        return reverse('courses:admin_edit', kwargs={'pk': self.object.course.pk})


# Student Views
class EnrollView(LoginRequiredMixin, DetailView):
    """تسجيل الطالب في الدورة"""
    model = Course
    template_name = 'courses/enroll.html'
    context_object_name = 'course'

    def post(self, request, *args, **kwargs):
        course = self.get_object()

        # فحص ما إذا كان الطالب مسجل بالفعل
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            messages.warning(request, 'أنت مسجل في هذه الدورة بالفعل!')
            return redirect('courses:detail', pk=course.pk)

        # فحص ما إذا كانت الدورة ممتلئة
        if course.is_full:
            messages.error(request, 'عذراً، الدورة ممتلئة!')
            return redirect('courses:detail', pk=course.pk)

        # إنشاء التسجيل
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course
        )

        messages.success(request, f'تم تسجيلك في دورة "{course.title}" بنجاح!')
        return redirect('courses:detail', pk=course.pk)


class ContentView(LoginRequiredMixin, DetailView):
    """عرض محتوى الدورة للطالب"""
    model = CourseContent
    template_name = 'courses/content.html'
    context_object_name = 'content'

    def dispatch(self, request, *args, **kwargs):
        self.content = get_object_or_404(CourseContent, pk=kwargs['content_id'])
        self.course = get_object_or_404(Course, pk=kwargs['course_id'])

        # فحص ما إذا كان الطالب مسجل في الدورة
        try:
            self.enrollment = Enrollment.objects.get(
                student=request.user,
                course=self.course,
                is_active=True
            )
        except Enrollment.DoesNotExist:
            messages.error(request, 'يجب التسجيل في الدورة أولاً!')
            return redirect('courses:detail', pk=self.course.pk)

        # فحص ما إذا كان المحتوى متاح (التسلسل)
        if not self.is_content_accessible():
            messages.error(request, 'يجب إكمال الدروس السابقة أولاً!')
            return redirect('courses:progress', pk=self.course.pk)

        return super().dispatch(request, *args, **kwargs)

    def is_content_accessible(self):
        """فحص ما إذا كان المحتوى متاح للطالب"""
        # المحتوى المجاني متاح دائماً
        if self.content.is_free:
            return True

        # فحص إكمال المحتوى السابق
        previous_content = self.course.content.filter(
            order_sequence__lt=self.content.order_sequence,
            is_published=True
        ).order_by('order_sequence')

        for prev_content in previous_content:
            try:
                progress = StudentProgress.objects.get(
                    enrollment=self.enrollment,
                    content=prev_content
                )
                if not progress.is_completed:
                    return False
            except StudentProgress.DoesNotExist:
                return False

        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        context['enrollment'] = self.enrollment

        # الحصول على تقدم الطالب
        progress, created = StudentProgress.objects.get_or_create(
            enrollment=self.enrollment,
            content=self.content
        )
        context['progress'] = progress

        # المحتوى التالي والسابق
        context['next_content'] = self.course.content.filter(
            order_sequence__gt=self.content.order_sequence,
            is_published=True
        ).first()

        context['previous_content'] = self.course.content.filter(
            order_sequence__lt=self.content.order_sequence,
            is_published=True
        ).last()

        return context

    def post(self, request, *args, **kwargs):
        """تحديث تقدم الطالب"""
        content = self.get_object()

        # تحديث التقدم
        progress, created = StudentProgress.objects.get_or_create(
            enrollment=self.enrollment,
            content=content
        )

        action = request.POST.get('action')

        if action == 'mark_complete':
            progress.mark_completed()
            messages.success(request, 'تم تحديد الدرس كمكتمل!')

        elif action == 'update_position':
            position = int(request.POST.get('position', 0))
            progress.last_position = position
            progress.save()
            return JsonResponse({'status': 'success'})

        elif action == 'save_notes':
            notes = request.POST.get('notes', '')
            progress.notes = notes
            progress.save()
            messages.success(request, 'تم حفظ الملاحظات!')

        return redirect('courses:content', course_id=self.course.pk, content_id=content.pk)


class ProgressView(LoginRequiredMixin, DetailView):
    """عرض تقدم الطالب في الدورة"""
    model = Course
    template_name = 'courses/progress.html'
    context_object_name = 'course'

    def dispatch(self, request, *args, **kwargs):
        course = self.get_object()

        # فحص التسجيل
        try:
            self.enrollment = Enrollment.objects.get(
                student=request.user,
                course=course,
                is_active=True
            )
        except Enrollment.DoesNotExist:
            messages.error(request, 'يجب التسجيل في الدورة أولاً!')
            return redirect('courses:detail', pk=course.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enrollment'] = self.enrollment

        # تقدم المحتوى
        content_progress = []
        for content in self.object.content.filter(is_published=True).order_by('order_sequence'):
            try:
                progress = StudentProgress.objects.get(
                    enrollment=self.enrollment,
                    content=content
                )
            except StudentProgress.DoesNotExist:
                progress = None

            content_progress.append({
                'content': content,
                'progress': progress,
                'is_accessible': self.is_content_accessible(content)
            })

        context['content_progress'] = content_progress
        return context

    def is_content_accessible(self, content):
        """فحص ما إذا كان المحتوى متاح"""
        if content.is_free:
            return True

        previous_content = self.object.content.filter(
            order_sequence__lt=content.order_sequence,
            is_published=True
        )

        for prev_content in previous_content:
            try:
                progress = StudentProgress.objects.get(
                    enrollment=self.enrollment,
                    content=prev_content
                )
                if not progress.is_completed:
                    return False
            except StudentProgress.DoesNotExist:
                return False

        return True


# Certificate and Review Views
class CertificateView(LoginRequiredMixin, DetailView):
    """عرض شهادة الطالب"""
    model = Course
    template_name = 'courses/certificate.html'
    context_object_name = 'course'

    def dispatch(self, request, *args, **kwargs):
        course = self.get_object()

        # فحص التسجيل والإكمال
        try:
            self.enrollment = Enrollment.objects.get(
                student=request.user,
                course=course,
                is_active=True,
                completion_date__isnull=False
            )
        except Enrollment.DoesNotExist:
            messages.error(request, 'يجب إكمال الدورة أولاً للحصول على الشهادة!')
            return redirect('courses:detail', pk=course.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enrollment'] = self.enrollment

        # إنشاء الشهادة إذا لم تكن موجودة
        certificate, created = Certificate.objects.get_or_create(
            enrollment=self.enrollment
        )
        context['certificate'] = certificate

        return context


class CertificateDownloadView(LoginRequiredMixin, DetailView):
    """تحميل الشهادة كـ PDF"""
    model = Certificate

    def get_object(self):
        certificate_id = self.kwargs['certificate_id']
        certificate = get_object_or_404(Certificate, pk=certificate_id)

        # فحص الصلاحية
        if certificate.enrollment.student != self.request.user:
            raise Http404("الشهادة غير موجودة")

        return certificate

    def get(self, request, *args, **kwargs):
        certificate = self.get_object()

        # استخدام مولد الشهادات المتقدم
        from .certificate_generator import generate_certificate_pdf

        try:
            # توليد PDF
            pdf_buffer = generate_certificate_pdf(certificate.enrollment)

            # إرجاع الـ PDF
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            filename = f"certificate_{certificate.certificate_number}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            # في حالة الخطأ، استخدم مولد بسيط
            return self._generate_simple_pdf(certificate)

    def _generate_simple_pdf(self, certificate):
        """مولد PDF بسيط كبديل"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, landscape
        from io import BytesIO

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)

        # رسم شهادة بسيطة
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredText(width/2, height-150, "Certificate of Completion")

        p.setFont("Helvetica", 16)
        p.drawCentredText(width/2, height-200, "Alaa Abdulhamid Academy")

        p.setFont("Helvetica", 14)
        p.drawCentredText(width/2, height-280, "This is to certify that")

        p.setFont("Helvetica-Bold", 20)
        student_name = certificate.enrollment.student.get_full_name()
        p.drawCentredText(width/2, height-320, student_name)

        p.setFont("Helvetica", 14)
        p.drawCentredText(width/2, height-360, "has successfully completed")

        p.setFont("Helvetica-Bold", 18)
        course_title = certificate.enrollment.course.title
        p.drawCentredText(width/2, height-400, course_title)

        p.setFont("Helvetica", 12)
        issue_date = certificate.issue_date.strftime("%B %d, %Y")
        p.drawCentredText(width/2, height-450, f"Issued on: {issue_date}")
        p.drawCentredText(width/2, height-470, f"Certificate No: {certificate.certificate_number}")

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f"certificate_{certificate.certificate_number}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


class ReviewView(LoginRequiredMixin, CreateView):
    """إضافة تقييم للدورة"""
    model = Review
    form_class = ReviewForm
    template_name = 'courses/review.html'

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=kwargs['pk'])

        # فحص التسجيل
        try:
            self.enrollment = Enrollment.objects.get(
                student=request.user,
                course=self.course,
                is_active=True
            )
        except Enrollment.DoesNotExist:
            messages.error(request, 'يجب التسجيل في الدورة أولاً!')
            return redirect('courses:detail', pk=self.course.pk)

        # فحص ما إذا كان التقييم موجود بالفعل
        if hasattr(self.enrollment, 'review'):
            messages.info(request, 'لقد قمت بتقييم هذه الدورة بالفعل!')
            return redirect('courses:detail', pk=self.course.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.enrollment = self.enrollment
        response = super().form_valid(form)
        messages.success(self.request, 'شكراً لك على تقييم الدورة!')
        return response

    def get_success_url(self):
        return reverse('courses:detail', kwargs={'pk': self.course.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        context['enrollment'] = self.enrollment
        return context


# Admin List Views
@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminCourseListView(ListView):
    """قائمة الدورات للمدير"""
    model = Course
    template_name = 'courses/admin_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        queryset = Course.objects.select_related('category', 'instructor').annotate(
            enrollments_count=Count('enrollments'),
            avg_rating=Avg('enrollments__review__rating')
        )

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        # فلترة حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # فلترة حسب الفئة
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['status_choices'] = Course.STATUS_CHOICES
        return context


# File Upload Views
@method_decorator(csrf_exempt, name='dispatch')
class FileUploadAPIView(LoginRequiredMixin, View):
    """API لرفع الملفات"""

    def post(self, request, *args, **kwargs):
        try:
            # التحقق من الصلاحيات
            if not request.user.is_admin:
                return JsonResponse({
                    'status': 'error',
                    'message': 'غير مصرح لك برفع الملفات'
                }, status=403)

            # التحقق من وجود الملف
            if 'file' not in request.FILES:
                return JsonResponse({
                    'status': 'error',
                    'message': 'لم يتم اختيار ملف'
                }, status=400)

            file = request.FILES['file']
            content_type = request.POST.get('content_type', 'document')

            # استخدام معالج الملفات
            from .file_handlers import validate_course_file

            result = validate_course_file(file, content_type)

            return JsonResponse({
                'status': 'success',
                'message': 'تم رفع الملف بنجاح',
                'data': result
            })

        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'حدث خطأ غير متوقع'
            }, status=500)


class FileManagerView(AdminRequiredMixin, TemplateView):
    """مدير الملفات"""
    template_name = 'courses/file_manager.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على جميع محتويات الدورات مع الملفات
        content_with_files = CourseContent.objects.filter(
            Q(file_upload__isnull=False) | Q(file_url__isnull=False)
        ).select_related('course').order_by('-created_at')

        # إحصائيات الملفات
        total_files = content_with_files.count()
        video_files = content_with_files.filter(content_type='video').count()
        document_files = content_with_files.filter(content_type='pdf').count()

        # حساب المساحة المستخدمة (تقريبي)
        total_size = 0
        for content in content_with_files:
            if content.file_upload:
                try:
                    total_size += content.file_upload.size
                except:
                    pass

        context.update({
            'content_with_files': content_with_files[:50],  # أول 50 ملف
            'total_files': total_files,
            'video_files': video_files,
            'document_files': document_files,
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024) if total_size > 0 else 0,
        })

        return context


@login_required
def delete_file_view(request, content_id):
    """حذف ملف"""
    if not request.user.is_admin:
        raise Http404()

    content = get_object_or_404(CourseContent, pk=content_id)

    if request.method == 'POST':
        try:
            # حذف الملف من التخزين
            if content.file_upload:
                content.file_upload.delete()

            # حذف المحتوى
            content.delete()

            messages.success(request, 'تم حذف الملف بنجاح')
            return JsonResponse({
                'status': 'success',
                'message': 'تم حذف الملف بنجاح'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطأ في حذف الملف: {str(e)}'
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'طريقة غير مدعومة'
    }, status=405)
