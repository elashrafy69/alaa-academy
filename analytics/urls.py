from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # لوحة التحليلات الرئيسية
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    
    # تحليلات الدورات
    path('courses/', views.CourseAnalyticsView.as_view(), name='courses'),
    path('courses/<uuid:course_id>/', views.CourseDetailAnalyticsView.as_view(), name='course_detail'),
    
    # تحليلات المستخدمين
    path('users/', views.UserAnalyticsView.as_view(), name='users'),
    path('users/<int:user_id>/', views.UserDetailAnalyticsView.as_view(), name='user_detail'),
    
    # التقارير
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/export/', views.ExportReportView.as_view(), name='export_report'),
    
    # API للرسوم البيانية
    path('api/enrollment-trends/', views.EnrollmentTrendsAPIView.as_view(), name='api_enrollment_trends'),
    path('api/completion-rates/', views.CompletionRatesAPIView.as_view(), name='api_completion_rates'),
    path('api/user-activity/', views.UserActivityAPIView.as_view(), name='api_user_activity'),
]
