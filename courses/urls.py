from django.urls import path
from . import views
from .certificate_views import (
    CertificateVerificationView, CertificateVerificationAPIView,
    certificate_download_public
)

app_name = 'courses'

urlpatterns = [
    # قائمة الدورات
    path('', views.CourseListView.as_view(), name='list'),
    path('category/<int:category_id>/', views.CourseListView.as_view(), name='by_category'),

    # تفاصيل الدورة
    path('<uuid:pk>/', views.CourseDetailView.as_view(), name='detail'),
    path('<uuid:pk>/enroll/', views.EnrollView.as_view(), name='enroll'),

    # محتوى الدورة
    path('<uuid:course_id>/content/<uuid:content_id>/', views.ContentView.as_view(), name='content'),
    path('<uuid:course_id>/progress/', views.ProgressView.as_view(), name='progress'),

    # الشهادات
    path('<uuid:pk>/certificate/', views.CertificateView.as_view(), name='certificate'),
    path('certificate/<uuid:certificate_id>/download/', views.CertificateDownloadView.as_view(), name='certificate_download'),

    # التحقق من الشهادات
    path('verify/', CertificateVerificationView.as_view(), name='certificate_verify'),
    path('verify/<str:certificate_number>/', CertificateVerificationView.as_view(), name='certificate_verify_number'),
    path('verify-api/', CertificateVerificationAPIView.as_view(), name='certificate_verify_api'),
    path('certificate-public/<str:certificate_number>/download/', certificate_download_public, name='certificate_download_public'),

    # التقييمات
    path('<uuid:pk>/review/', views.ReviewView.as_view(), name='review'),

    # إدارة الدورات (للمدراء)
    path('admin/', views.AdminCourseListView.as_view(), name='admin_list'),
    path('admin/create/', views.CourseCreateView.as_view(), name='admin_create'),
    path('admin/<uuid:pk>/edit/', views.CourseUpdateView.as_view(), name='admin_edit'),
    path('admin/<uuid:pk>/delete/', views.CourseDeleteView.as_view(), name='admin_delete'),
    path('admin/<uuid:course_id>/content/add/', views.ContentCreateView.as_view(), name='admin_content_add'),
    path('admin/content/<uuid:pk>/edit/', views.ContentUpdateView.as_view(), name='admin_content_edit'),
    path('admin/content/<uuid:pk>/delete/', views.ContentDeleteView.as_view(), name='admin_content_delete'),

    # File Upload and Management
    path('upload/', views.FileUploadAPIView.as_view(), name='file_upload_api'),
    path('admin/files/', views.FileManagerView.as_view(), name='file_manager'),
    path('admin/files/<uuid:content_id>/delete/', views.delete_file_view, name='delete_file'),
]
