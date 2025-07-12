"""
Middleware للأمان
"""

import logging
import time
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
import re

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """إضافة headers الأمان"""
    
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "media-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
        
        # HTTPS Strict Transport Security (في الإنتاج فقط)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """تحديد معدل الطلبات"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # إعدادات التحديد
        self.rate_limits = {
            'login': {'requests': 5, 'window': 300},  # 5 محاولات في 5 دقائق
            'register': {'requests': 3, 'window': 3600},  # 3 تسجيلات في ساعة
            'api': {'requests': 100, 'window': 3600},  # 100 طلب API في ساعة
            'upload': {'requests': 10, 'window': 3600},  # 10 رفع ملف في ساعة
            'default': {'requests': 60, 'window': 60},  # 60 طلب في دقيقة
        }
    
    def __call__(self, request):
        # تحديد نوع الطلب
        rate_type = self._get_rate_type(request)
        
        # التحقق من التحديد
        if not self._check_rate_limit(request, rate_type):
            return self._rate_limit_response(request)
        
        response = self.get_response(request)
        return response
    
    def _get_rate_type(self, request):
        """تحديد نوع معدل التحديد"""
        path = request.path
        
        if '/accounts/login/' in path:
            return 'login'
        elif '/accounts/register/' in path:
            return 'register'
        elif '/api/' in path:
            return 'api'
        elif 'upload' in path:
            return 'upload'
        else:
            return 'default'
    
    def _check_rate_limit(self, request, rate_type):
        """التحقق من معدل التحديد"""
        # الحصول على معرف العميل
        client_id = self._get_client_id(request)
        
        # مفتاح التخزين المؤقت
        cache_key = f'rate_limit:{rate_type}:{client_id}'
        
        # الحصول على الإعدادات
        config = self.rate_limits.get(rate_type, self.rate_limits['default'])
        
        # الحصول على العدد الحالي
        current_count = cache.get(cache_key, 0)
        
        if current_count >= config['requests']:
            return False
        
        # زيادة العداد
        cache.set(cache_key, current_count + 1, config['window'])
        
        return True
    
    def _get_client_id(self, request):
        """الحصول على معرف العميل"""
        # استخدام IP + User Agent كمعرف
        ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:100]
        
        if request.user.is_authenticated:
            return f'user:{request.user.id}'
        
        return f'ip:{ip}:{hash(user_agent)}'
    
    def _get_client_ip(self, request):
        """الحصول على IP العميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _rate_limit_response(self, request):
        """استجابة تجاوز المعدل"""
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'error': 'تم تجاوز الحد المسموح من الطلبات',
                'message': 'يرجى المحاولة لاحقاً'
            }, status=429)
        
        return HttpResponseForbidden('تم تجاوز الحد المسموح من الطلبات')


class SuspiciousActivityMiddleware(MiddlewareMixin):
    """مراقبة النشاط المشبوه"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # أنماط مشبوهة
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'union\s+select',  # SQL Injection
            r'drop\s+table',  # SQL Injection
            r'exec\s*\(',  # Code Injection
            r'eval\s*\(',  # Code Injection
            r'\.\./',  # Path Traversal
            r'%2e%2e%2f',  # Encoded Path Traversal
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
    
    def __call__(self, request):
        # فحص النشاط المشبوه
        if self._detect_suspicious_activity(request):
            self._log_suspicious_activity(request)
            
            # حظر الطلب إذا كان خطيراً
            if self._is_dangerous_request(request):
                return HttpResponseForbidden('طلب مرفوض لأسباب أمنية')
        
        response = self.get_response(request)
        return response
    
    def _detect_suspicious_activity(self, request):
        """اكتشاف النشاط المشبوه"""
        # فحص المعاملات
        for key, value in request.GET.items():
            if self._contains_suspicious_content(str(value)):
                return True
        
        if request.method == 'POST':
            for key, value in request.POST.items():
                if self._contains_suspicious_content(str(value)):
                    return True
        
        # فحص المسار
        if self._contains_suspicious_content(request.path):
            return True
        
        # فحص User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if self._is_suspicious_user_agent(user_agent):
            return True
        
        return False
    
    def _contains_suspicious_content(self, content):
        """التحقق من وجود محتوى مشبوه"""
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                return True
        return False
    
    def _is_suspicious_user_agent(self, user_agent):
        """التحقق من User Agent مشبوه"""
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan',
            'burpsuite', 'owasp', 'w3af', 'acunetix'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(agent in user_agent_lower for agent in suspicious_agents)
    
    def _is_dangerous_request(self, request):
        """التحقق من كون الطلب خطيراً"""
        # طلبات خطيرة يجب حظرها فوراً
        dangerous_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'exec\s*\(',
            r'<script[^>]*>.*?</script>',
        ]
        
        for pattern in dangerous_patterns:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            
            # فحص جميع البيانات
            all_data = ' '.join([
                request.path,
                ' '.join(request.GET.values()),
                ' '.join(request.POST.values()) if request.method == 'POST' else ''
            ])
            
            if compiled_pattern.search(all_data):
                return True
        
        return False
    
    def _log_suspicious_activity(self, request):
        """تسجيل النشاط المشبوه"""
        logger.warning(
            f'Suspicious activity detected: '
            f'IP={self._get_client_ip(request)}, '
            f'Path={request.path}, '
            f'Method={request.method}, '
            f'User={request.user if request.user.is_authenticated else "Anonymous"}, '
            f'UserAgent={request.META.get("HTTP_USER_AGENT", "")[:100]}'
        )
    
    def _get_client_ip(self, request):
        """الحصول على IP العميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionSecurityMiddleware(MiddlewareMixin):
    """أمان الجلسات"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # التحقق من تغيير IP
            current_ip = self._get_client_ip(request)
            session_ip = request.session.get('ip_address')
            
            if session_ip and session_ip != current_ip:
                # تسجيل تحذير
                logger.warning(
                    f'IP address changed for user {request.user.id}: '
                    f'{session_ip} -> {current_ip}'
                )
                
                # إنهاء الجلسة (اختياري - قد يكون مزعجاً للمستخدمين)
                # logout(request)
                # return redirect('accounts:login')
            
            # حفظ IP الحالي
            request.session['ip_address'] = current_ip
            
            # التحقق من انتهاء صلاحية الجلسة
            last_activity = request.session.get('last_activity')
            if last_activity:
                inactive_time = time.time() - last_activity
                max_inactive_time = getattr(settings, 'SESSION_TIMEOUT', 3600)  # ساعة واحدة
                
                if inactive_time > max_inactive_time:
                    logout(request)
                    return redirect('accounts:login')
            
            # تحديث وقت النشاط
            request.session['last_activity'] = time.time()
    
    def _get_client_ip(self, request):
        """الحصول على IP العميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
