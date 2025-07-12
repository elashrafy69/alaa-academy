from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from . import admin_views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.custom_login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Admin URLs
    path('admin/students/', admin_views.StudentManagementView.as_view(), name='admin_students'),
    path('admin/students/<uuid:pk>/', admin_views.StudentDetailView.as_view(), name='admin_student_detail'),
    path('admin/students/<uuid:pk>/edit/', admin_views.StudentEditView.as_view(), name='admin_student_edit'),
    path('admin/students/bulk-actions/', admin_views.student_bulk_actions, name='admin_student_bulk_actions'),
    path('admin/students/export/', admin_views.export_students_csv, name='admin_export_students'),

    # Registration Codes
    path('admin/registration-codes/', admin_views.RegistrationCodeManagementView.as_view(), name='admin_registration_codes'),
    path('admin/registration-codes/create/', admin_views.RegistrationCodeCreateView.as_view(), name='admin_registration_code_create'),
    path('admin/registration-codes/bulk/', admin_views.bulk_registration_codes, name='admin_bulk_registration_codes'),
]
