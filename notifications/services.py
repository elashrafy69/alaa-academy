"""
خدمات نظام الإشعارات
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationBatch, NotificationType, NotificationPriority
)
import logging
from typing import List, Dict, Any, Optional
from datetime import timedelta

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """خدمة إدارة الإشعارات"""
    
    @staticmethod
    def create_notification(
        recipient: User,
        title: str,
        message: str,
        notification_type: str = NotificationType.SYSTEM,
        priority: str = NotificationPriority.NORMAL,
        sender: Optional[User] = None,
        action_url: Optional[str] = None,
        send_email: bool = False,
        expires_at: Optional[timezone.datetime] = None,
        extra_data: Optional[Dict] = None
    ) -> Notification:
        """إنشاء إشعار جديد"""
        
        # التحقق من تفضيلات المستخدم
        preferences = NotificationService.get_user_preferences(recipient)
        
        # التحقق من إمكانية إرسال هذا النوع من الإشعارات
        if not preferences.should_send_notification(notification_type):
            logger.info(f"Notification blocked by user preferences: {recipient.email}")
            return None
        
        # التحقق من الساعات الهادئة
        if preferences.is_quiet_time() and priority != NotificationPriority.URGENT:
            logger.info(f"Notification delayed due to quiet hours: {recipient.email}")
            # يمكن تأجيل الإشعار أو إرساله لاحقاً
        
        # إنشاء الإشعار
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            send_email=send_email and preferences.email_notifications,
            expires_at=expires_at,
            extra_data=extra_data or {}
        )
        
        # إرسال البريد الإلكتروني إذا كان مطلوباً
        if notification.send_email:
            NotificationService.send_email_notification(notification)
        
        logger.info(f"Notification created: {notification.id} for {recipient.email}")
        return notification
    
    @staticmethod
    def create_from_template(
        template_name: str,
        recipient: User,
        context: Dict[str, Any],
        sender: Optional[User] = None,
        action_url: Optional[str] = None,
        expires_at: Optional[timezone.datetime] = None
    ) -> Optional[Notification]:
        """إنشاء إشعار من قالب"""
        
        try:
            template = NotificationTemplate.objects.get(
                name=template_name,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template not found: {template_name}")
            return None
        
        # تطبيق القالب
        title = template.render_title(context)
        message = template.render_message(context)
        
        return NotificationService.create_notification(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=template.notification_type,
            priority=template.default_priority,
            sender=sender,
            action_url=action_url,
            send_email=template.send_email_default,
            expires_at=expires_at,
            extra_data={'template_name': template_name, 'context': context}
        )
    
    @staticmethod
    def bulk_create_notifications(
        recipients: List[User],
        title: str,
        message: str,
        notification_type: str = NotificationType.ANNOUNCEMENT,
        priority: str = NotificationPriority.NORMAL,
        sender: Optional[User] = None,
        send_email: bool = False
    ) -> NotificationBatch:
        """إنشاء إشعارات مجمعة"""
        
        # إنشاء مجموعة الإشعارات
        batch = NotificationBatch.objects.create(
            title=title,
            sender=sender,
            total_recipients=len(recipients),
            status='pending'
        )
        
        try:
            with transaction.atomic():
                batch.status = 'sending'
                batch.started_at = timezone.now()
                batch.save()
                
                notifications = []
                sent_count = 0
                failed_count = 0
                
                for recipient in recipients:
                    try:
                        notification = NotificationService.create_notification(
                            recipient=recipient,
                            title=title,
                            message=message,
                            notification_type=notification_type,
                            priority=priority,
                            sender=sender,
                            send_email=send_email
                        )
                        
                        if notification:
                            notifications.append(notification)
                            sent_count += 1
                        else:
                            failed_count += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to create notification for {recipient.email}: {e}")
                        failed_count += 1
                
                # تحديث إحصائيات المجموعة
                batch.sent_count = sent_count
                batch.failed_count = failed_count
                batch.status = 'completed'
                batch.completed_at = timezone.now()
                batch.save()
                
                logger.info(f"Bulk notifications created: {sent_count} sent, {failed_count} failed")
                
        except Exception as e:
            batch.status = 'failed'
            batch.save()
            logger.error(f"Bulk notification creation failed: {e}")
            raise
        
        return batch
    
    @staticmethod
    def send_email_notification(notification: Notification):
        """إرسال إشعار عبر البريد الإلكتروني"""
        
        if notification.email_sent:
            return
        
        try:
            # إعداد محتوى البريد
            subject = notification.title
            
            # استخدام قالب HTML للبريد
            html_content = render_to_string('notifications/email_notification.html', {
                'notification': notification,
                'recipient': notification.recipient,
                'site_name': getattr(settings, 'SITE_NAME', 'أكاديمية علاء عبد الحميد')
            })
            
            # إعداد البريد
            email = EmailMultiAlternatives(
                subject=subject,
                body=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[notification.recipient.email]
            )
            
            email.attach_alternative(html_content, "text/html")
            
            # إرسال البريد
            email.send()
            
            # تحديث حالة الإرسال
            notification.email_sent = True
            notification.email_sent_at = timezone.now()
            notification.save(update_fields=['email_sent', 'email_sent_at'])
            
            logger.info(f"Email notification sent to {notification.recipient.email}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            raise
    
    @staticmethod
    def get_user_preferences(user: User) -> NotificationPreference:
        """الحصول على تفضيلات المستخدم أو إنشاؤها"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_notifications': True,
                'browser_notifications': True,
            }
        )
        return preferences
    
    @staticmethod
    def mark_notifications_as_read(user: User, notification_ids: List[str] = None):
        """تحديد الإشعارات كمقروءة"""
        
        queryset = user.notifications.filter(is_read=False)
        
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)
        
        updated_count = queryset.update(
            is_read=True,
            read_at=timezone.now()
        )
        
        logger.info(f"Marked {updated_count} notifications as read for {user.email}")
        return updated_count
    
    @staticmethod
    def get_unread_count(user: User) -> int:
        """الحصول على عدد الإشعارات غير المقروءة"""
        return user.notifications.filter(is_read=False).count()
    
    @staticmethod
    def get_recent_notifications(user: User, limit: int = 10) -> List[Notification]:
        """الحصول على الإشعارات الحديثة"""
        return list(user.notifications.select_related('sender').order_by('-created_at')[:limit])
    
    @staticmethod
    def cleanup_old_notifications(days: int = 30):
        """تنظيف الإشعارات القديمة"""
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # حذف الإشعارات المقروءة القديمة
        deleted_count = Notification.objects.filter(
            is_read=True,
            created_at__lt=cutoff_date
        ).delete()[0]
        
        # حذف الإشعارات منتهية الصلاحية
        expired_count = Notification.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old notifications and {expired_count} expired notifications")
        return deleted_count + expired_count


class NotificationTemplateService:
    """خدمة إدارة قوالب الإشعارات"""
    
    @staticmethod
    def create_default_templates():
        """إنشاء القوالب الافتراضية"""
        
        templates = [
            {
                'name': 'course_enrollment',
                'notification_type': NotificationType.ENROLLMENT,
                'title_template': 'تم تسجيلك في دورة {{ course.title }}',
                'message_template': 'مرحباً {{ user.first_name }}، تم تسجيلك بنجاح في دورة "{{ course.title }}". يمكنك البدء في التعلم الآن!',
                'email_subject_template': 'تأكيد التسجيل في دورة {{ course.title }}',
                'send_email_default': True,
            },
            {
                'name': 'course_completion',
                'notification_type': NotificationType.CERTIFICATE,
                'title_template': 'تهانينا! أكملت دورة {{ course.title }}',
                'message_template': 'تهانينا {{ user.first_name }}! لقد أكملت بنجاح دورة "{{ course.title }}". يمكنك الآن تحميل شهادتك.',
                'email_subject_template': 'تهانينا على إكمال دورة {{ course.title }}',
                'send_email_default': True,
                'default_priority': NotificationPriority.HIGH,
            },
            {
                'name': 'assignment_due',
                'notification_type': NotificationType.REMINDER,
                'title_template': 'تذكير: مهمة {{ assignment.title }} مستحقة قريباً',
                'message_template': 'مرحباً {{ user.first_name }}، تذكير بأن مهمة "{{ assignment.title }}" مستحقة في {{ assignment.due_date }}.',
                'email_subject_template': 'تذكير: مهمة مستحقة قريباً',
                'send_email_default': True,
                'default_priority': NotificationPriority.HIGH,
            },
            {
                'name': 'new_announcement',
                'notification_type': NotificationType.ANNOUNCEMENT,
                'title_template': 'إعلان جديد: {{ announcement.title }}',
                'message_template': '{{ announcement.content }}',
                'email_subject_template': 'إعلان جديد من أكاديمية علاء عبد الحميد',
                'send_email_default': False,
            }
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                created_count += 1
        
        logger.info(f"Created {created_count} default notification templates")
        return created_count


# دوال مساعدة للاستخدام السريع
def notify_user(user: User, title: str, message: str, **kwargs):
    """دالة مساعدة لإرسال إشعار سريع"""
    return NotificationService.create_notification(
        recipient=user,
        title=title,
        message=message,
        **kwargs
    )


def notify_course_enrollment(user: User, course):
    """إشعار التسجيل في دورة"""
    return NotificationService.create_from_template(
        template_name='course_enrollment',
        recipient=user,
        context={'user': user, 'course': course},
        action_url=f'/courses/{course.pk}/'
    )


def notify_course_completion(user: User, course):
    """إشعار إكمال دورة"""
    return NotificationService.create_from_template(
        template_name='course_completion',
        recipient=user,
        context={'user': user, 'course': course},
        action_url=f'/courses/{course.pk}/certificate/'
    )


def notify_assignment_due(user: User, assignment):
    """تذكير بمهمة مستحقة"""
    return NotificationService.create_from_template(
        template_name='assignment_due',
        recipient=user,
        context={'user': user, 'assignment': assignment},
        action_url=f'/assignments/{assignment.pk}/',
        expires_at=assignment.due_date
    )
