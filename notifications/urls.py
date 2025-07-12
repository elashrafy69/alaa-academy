"""
URLs نظام الإشعارات
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification List and Detail
    path('', views.NotificationListView.as_view(), name='list'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(), name='detail'),
    
    # Notification Actions
    path('mark-read/<uuid:notification_id>/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('delete/<uuid:notification_id>/', views.delete_notification, name='delete'),
    
    # Preferences
    path('preferences/', views.NotificationPreferenceView.as_view(), name='preferences'),
    
    # API
    path('api/', views.NotificationAPIView.as_view(), name='api'),
    
    # Widget
    path('widget/', views.notification_widget, name='widget'),
    
    # Admin
    path('admin/bulk-send/', views.send_bulk_notification, name='admin_bulk_send'),
]
