"""
Views نظام الإشعارات
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Notification, NotificationPreference
from .services import NotificationService
import json


class NotificationListView(LoginRequiredMixin, ListView):
    """قائمة الإشعارات"""
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = self.request.user.notifications.select_related('sender').order_by('-created_at')
        
        # فلترة حسب الحالة
        status = self.request.GET.get('status')
        if status == 'unread':
            queryset = queryset.filter(is_read=False)
        elif status == 'read':
            queryset = queryset.filter(is_read=True)
        
        # فلترة حسب النوع
        notification_type = self.request.GET.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(message__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إحصائيات الإشعارات
        user_notifications = self.request.user.notifications
        context.update({
            'total_count': user_notifications.count(),
            'unread_count': user_notifications.filter(is_read=False).count(),
            'read_count': user_notifications.filter(is_read=True).count(),
            'status_filter': self.request.GET.get('status', ''),
            'type_filter': self.request.GET.get('type', ''),
            'search_query': self.request.GET.get('search', ''),
        })
        
        return context


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل الإشعار"""
    model = Notification
    template_name = 'notifications/notification_detail.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        return self.request.user.notifications.select_related('sender')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # تحديد الإشعار كمقروء عند عرضه
        if not obj.is_read:
            obj.mark_as_read()
        return obj


class NotificationPreferenceView(LoginRequiredMixin, UpdateView):
    """إعدادات الإشعارات"""
    model = NotificationPreference
    template_name = 'notifications/notification_preferences.html'
    fields = [
        'email_notifications', 'browser_notifications',
        'enrollment_notifications', 'course_update_notifications',
        'assignment_notifications', 'grade_notifications',
        'certificate_notifications', 'reminder_notifications',
        'announcement_notifications', 'message_notifications',
        'quiet_hours_start', 'quiet_hours_end'
    ]
    
    def get_object(self, queryset=None):
        return NotificationService.get_user_preferences(self.request.user)
    
    def get_success_url(self):
        messages.success(self.request, 'تم حفظ إعدادات الإشعارات بنجاح')
        return self.request.path


# API Views
@method_decorator(csrf_exempt, name='dispatch')
class NotificationAPIView(LoginRequiredMixin, ListView):
    """API للإشعارات"""
    
    def get(self, request, *args, **kwargs):
        """الحصول على الإشعارات"""
        
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
        
        queryset = request.user.notifications.select_related('sender').order_by('-created_at')
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        notifications = queryset[offset:offset + limit]
        
        data = []
        for notification in notifications:
            data.append({
                'id': str(notification.id),
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'action_url': notification.action_url,
                'icon': notification.get_icon(),
                'color_class': notification.get_color_class(),
                'sender': {
                    'name': notification.sender.get_full_name() if notification.sender else 'النظام',
                    'avatar': notification.sender.profile_picture.url if notification.sender and notification.sender.profile_picture else None
                } if notification.sender else None
            })
        
        return JsonResponse({
            'status': 'success',
            'notifications': data,
            'unread_count': request.user.notifications.filter(is_read=False).count(),
            'has_more': queryset.count() > offset + limit
        })
    
    def post(self, request, *args, **kwargs):
        """تحديث حالة الإشعارات"""
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            notification_ids = data.get('notification_ids', [])
            
            if action == 'mark_read':
                if notification_ids:
                    # تحديد إشعارات محددة كمقروءة
                    updated_count = NotificationService.mark_notifications_as_read(
                        request.user, notification_ids
                    )
                else:
                    # تحديد جميع الإشعارات كمقروءة
                    updated_count = NotificationService.mark_notifications_as_read(request.user)
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'تم تحديد {updated_count} إشعار كمقروء',
                    'updated_count': updated_count,
                    'unread_count': request.user.notifications.filter(is_read=False).count()
                })
            
            elif action == 'delete':
                if not notification_ids:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'لم يتم تحديد إشعارات للحذف'
                    })
                
                deleted_count = request.user.notifications.filter(
                    id__in=notification_ids
                ).delete()[0]
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'تم حذف {deleted_count} إشعار',
                    'deleted_count': deleted_count
                })
            
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'إجراء غير صحيح'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'بيانات غير صحيحة'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'حدث خطأ: {str(e)}'
            })


@login_required
def mark_notification_read(request, notification_id):
    """تحديد إشعار واحد كمقروء"""
    
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'تم تحديد الإشعار كمقروء'
        })
    
    # إعادة توجيه إلى رابط الإجراء إذا كان موجوداً
    if notification.action_url:
        return redirect(notification.action_url)
    
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    """تحديد جميع الإشعارات كمقروءة"""
    
    updated_count = NotificationService.mark_notifications_as_read(request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': f'تم تحديد {updated_count} إشعار كمقروء',
            'updated_count': updated_count
        })
    
    messages.success(request, f'تم تحديد {updated_count} إشعار كمقروء')
    return redirect('notifications:list')


@login_required
def delete_notification(request, notification_id):
    """حذف إشعار"""
    
    if request.method == 'POST':
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user
        )
        
        notification.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'تم حذف الإشعار'
            })
        
        messages.success(request, 'تم حذف الإشعار')
    
    return redirect('notifications:list')


@login_required
def notification_widget(request):
    """ويدجت الإشعارات للشريط العلوي"""
    
    recent_notifications = NotificationService.get_recent_notifications(
        request.user, limit=5
    )
    unread_count = NotificationService.get_unread_count(request.user)
    
    return render(request, 'notifications/widget.html', {
        'notifications': recent_notifications,
        'unread_count': unread_count
    })


# Admin Views (للمدراء فقط)
@login_required
def send_bulk_notification(request):
    """إرسال إشعار مجمع (للمدراء فقط)"""
    
    if not request.user.is_admin:
        return JsonResponse({
            'status': 'error',
            'message': 'غير مصرح لك بهذا الإجراء'
        }, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            title = data.get('title', '').strip()
            message = data.get('message', '').strip()
            recipient_type = data.get('recipient_type', 'all')
            send_email = data.get('send_email', False)
            
            if not title or not message:
                return JsonResponse({
                    'status': 'error',
                    'message': 'العنوان والرسالة مطلوبان'
                })
            
            # تحديد المستقبلين
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if recipient_type == 'all':
                recipients = User.objects.filter(user_type='student', is_active=True)
            elif recipient_type == 'enrolled':
                recipients = User.objects.filter(
                    user_type='student',
                    is_active=True,
                    enrollments__is_active=True
                ).distinct()
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'نوع مستقبلين غير صحيح'
                })
            
            # إرسال الإشعارات
            batch = NotificationService.bulk_create_notifications(
                recipients=list(recipients),
                title=title,
                message=message,
                sender=request.user,
                send_email=send_email
            )
            
            return JsonResponse({
                'status': 'success',
                'message': f'تم إرسال {batch.sent_count} إشعار بنجاح',
                'batch_id': str(batch.id),
                'sent_count': batch.sent_count,
                'failed_count': batch.failed_count
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'حدث خطأ: {str(e)}'
            })
    
    return render(request, 'notifications/admin/bulk_send.html')
