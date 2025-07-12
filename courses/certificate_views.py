"""
Views خاصة بنظام الشهادات والتحقق
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Certificate, Course, Enrollment
import json


class CertificateVerificationView(TemplateView):
    """صفحة التحقق من الشهادات"""
    template_name = 'courses/certificate_verify.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إذا كان هناك رقم شهادة في URL
        cert_number = self.kwargs.get('certificate_number')
        if cert_number:
            try:
                certificate = Certificate.objects.select_related(
                    'enrollment__student',
                    'enrollment__course',
                    'enrollment__course__instructor'
                ).get(certificate_number=cert_number, is_verified=True)
                context['certificate'] = certificate
                context['verification_result'] = 'valid'
            except Certificate.DoesNotExist:
                context['verification_result'] = 'invalid'
                context['error_message'] = 'رقم الشهادة غير صحيح أو غير موجود'
        
        return context


@method_decorator(csrf_exempt, name='dispatch')
class CertificateVerificationAPIView(TemplateView):
    """API للتحقق من الشهادات"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            certificate_number = data.get('certificate_number', '').strip()
            
            if not certificate_number:
                return JsonResponse({
                    'status': 'error',
                    'message': 'يرجى إدخال رقم الشهادة'
                })
            
            # البحث عن الشهادة
            try:
                certificate = Certificate.objects.select_related(
                    'enrollment__student',
                    'enrollment__course',
                    'enrollment__course__instructor',
                    'enrollment__course__category'
                ).get(certificate_number=certificate_number, is_verified=True)
                
                # إرجاع بيانات الشهادة
                return JsonResponse({
                    'status': 'success',
                    'certificate': {
                        'number': certificate.certificate_number,
                        'student_name': certificate.enrollment.student.get_full_name(),
                        'course_title': certificate.enrollment.course.title,
                        'course_category': certificate.enrollment.course.category.name,
                        'instructor_name': certificate.enrollment.course.instructor.get_full_name(),
                        'issue_date': certificate.issue_date.strftime('%Y-%m-%d'),
                        'completion_date': certificate.enrollment.completion_date.strftime('%Y-%m-%d') if certificate.enrollment.completion_date else None,
                        'course_duration': certificate.enrollment.course.estimated_duration,
                        'difficulty_level': certificate.enrollment.course.get_difficulty_level_display(),
                        'grade': certificate.grade or 'ممتاز',
                        'is_verified': certificate.is_verified
                    }
                })
                
            except Certificate.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'رقم الشهادة غير صحيح أو غير موجود'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'خطأ في البيانات المرسلة'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'حدث خطأ غير متوقع'
            })


class CertificateStatsView(TemplateView):
    """إحصائيات الشهادات للمدراء"""
    template_name = 'courses/certificate_stats.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إحصائيات عامة
        total_certificates = Certificate.objects.count()
        verified_certificates = Certificate.objects.filter(is_verified=True).count()
        
        # إحصائيات حسب الدورة
        course_stats = []
        for course in Course.objects.filter(status='published'):
            course_certificates = Certificate.objects.filter(
                enrollment__course=course
            ).count()
            
            if course_certificates > 0:
                course_stats.append({
                    'course': course,
                    'certificates_count': course_certificates,
                    'completion_rate': (course_certificates / course.enrollment_count * 100) if course.enrollment_count > 0 else 0
                })
        
        # ترتيب حسب عدد الشهادات
        course_stats.sort(key=lambda x: x['certificates_count'], reverse=True)
        
        # الشهادات الحديثة
        recent_certificates = Certificate.objects.select_related(
            'enrollment__student',
            'enrollment__course'
        ).order_by('-issue_date')[:10]
        
        context.update({
            'total_certificates': total_certificates,
            'verified_certificates': verified_certificates,
            'verification_rate': (verified_certificates / total_certificates * 100) if total_certificates > 0 else 0,
            'course_stats': course_stats[:10],  # أفضل 10 دورات
            'recent_certificates': recent_certificates
        })
        
        return context


@login_required
def bulk_certificate_generation(request):
    """توليد شهادات مجمع للدورة"""
    if not request.user.is_admin:
        raise Http404()
    
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        
        try:
            course = get_object_or_404(Course, pk=course_id)
            
            # الحصول على التسجيلات المكتملة بدون شهادات
            completed_enrollments = Enrollment.objects.filter(
                course=course,
                completion_date__isnull=False,
                certificate__isnull=True
            )
            
            certificates_created = 0
            for enrollment in completed_enrollments:
                certificate = Certificate.objects.create(enrollment=enrollment)
                certificates_created += 1
            
            return JsonResponse({
                'status': 'success',
                'message': f'تم إنشاء {certificates_created} شهادة بنجاح',
                'certificates_created': certificates_created
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'حدث خطأ: {str(e)}'
            })
    
    # GET request - عرض النموذج
    courses = Course.objects.filter(status='published').annotate(
        completed_enrollments=models.Count(
            'enrollments',
            filter=models.Q(enrollments__completion_date__isnull=False)
        ),
        certificates_count=models.Count('enrollments__certificate')
    )
    
    return render(request, 'courses/bulk_certificate_generation.html', {
        'courses': courses
    })


def certificate_download_public(request, certificate_number):
    """تحميل الشهادة للعامة (بدون تسجيل دخول)"""
    try:
        certificate = get_object_or_404(
            Certificate,
            certificate_number=certificate_number,
            is_verified=True
        )
        
        # استخدام مولد الشهادات
        from .certificate_generator import generate_certificate_pdf
        
        pdf_buffer = generate_certificate_pdf(certificate.enrollment)
        
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        filename = f"certificate_{certificate.certificate_number}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        
        return response
        
    except Exception as e:
        raise Http404("الشهادة غير موجودة أو غير صالحة")


class CertificateGalleryView(TemplateView):
    """معرض الشهادات العامة"""
    template_name = 'courses/certificate_gallery.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # الشهادات المعتمدة والعامة (يمكن إضافة فلتر للخصوصية)
        certificates = Certificate.objects.filter(
            is_verified=True
        ).select_related(
            'enrollment__student',
            'enrollment__course',
            'enrollment__course__category'
        ).order_by('-issue_date')[:50]  # آخر 50 شهادة
        
        # إحصائيات سريعة
        total_certificates = Certificate.objects.filter(is_verified=True).count()
        total_students = Certificate.objects.filter(
            is_verified=True
        ).values('enrollment__student').distinct().count()
        
        context.update({
            'certificates': certificates,
            'total_certificates': total_certificates,
            'total_students': total_students
        })
        
        return context
