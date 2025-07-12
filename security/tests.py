"""
اختبارات الأمان
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test.utils import override_settings
from .validators import (
    SecurePasswordValidator, FileSecurityValidator, 
    InputSanitizer, validate_no_special_chars
)
import tempfile
import os

User = get_user_model()


class SecurityMiddlewareTest(TestCase):
    """اختبار middleware الأمان"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
    
    def test_security_headers(self):
        """اختبار headers الأمان"""
        response = self.client.get('/')
        
        # التحقق من وجود headers الأمان
        self.assertIn('Content-Security-Policy', response)
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-XSS-Protection', response)
        
        # التحقق من القيم
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
    
    def test_rate_limiting(self):
        """اختبار تحديد معدل الطلبات"""
        login_url = reverse('accounts:login')
        
        # محاولة تسجيل دخول متكررة
        for i in range(6):  # أكثر من الحد المسموح (5)
            response = self.client.post(login_url, {
                'username': 'wrong@example.com',
                'password': 'wrongpassword'
            })
        
        # يجب أن يتم رفض الطلب السادس
        self.assertEqual(response.status_code, 429)
    
    def test_suspicious_activity_detection(self):
        """اختبار اكتشاف النشاط المشبوه"""
        # محاولة XSS
        response = self.client.get('/?search=<script>alert("xss")</script>')
        self.assertEqual(response.status_code, 403)
        
        # محاولة SQL Injection
        response = self.client.get('/?id=1 UNION SELECT * FROM users')
        self.assertEqual(response.status_code, 403)
        
        # محاولة Path Traversal
        response = self.client.get('/../../etc/passwd')
        self.assertEqual(response.status_code, 403)


class PasswordValidatorTest(TestCase):
    """اختبار مدقق كلمات المرور"""
    
    def setUp(self):
        self.validator = SecurePasswordValidator()
        self.user = User(
            email='test@example.com',
            first_name='John',
            last_name='Doe'
        )
    
    def test_strong_password(self):
        """اختبار كلمة مرور قوية"""
        strong_password = 'StrongPass123!'
        
        # يجب ألا ترفع استثناء
        try:
            self.validator.validate(strong_password, self.user)
        except ValidationError:
            self.fail('Strong password should be valid')
    
    def test_weak_passwords(self):
        """اختبار كلمات مرور ضعيفة"""
        weak_passwords = [
            'short',  # قصيرة جداً
            'nouppercase123!',  # لا تحتوي على أحرف كبيرة
            'NOLOWERCASE123!',  # لا تحتوي على أحرف صغيرة
            'NoNumbers!',  # لا تحتوي على أرقام
            'NoSpecialChars123',  # لا تحتوي على رموز خاصة
            'password123',  # شائعة
            'JohnDoe123!',  # تحتوي على اسم المستخدم
        ]
        
        for password in weak_passwords:
            with self.assertRaises(ValidationError):
                self.validator.validate(password, self.user)
    
    def test_password_with_user_info(self):
        """اختبار كلمة مرور تحتوي على معلومات المستخدم"""
        passwords_with_user_info = [
            'JohnPassword123!',
            'DoeSecure123!',
            'testPassword123!',
        ]
        
        for password in passwords_with_user_info:
            with self.assertRaises(ValidationError):
                self.validator.validate(password, self.user)


class FileSecurityValidatorTest(TestCase):
    """اختبار مدقق أمان الملفات"""
    
    def setUp(self):
        self.validator = FileSecurityValidator()
    
    def test_valid_image_file(self):
        """اختبار ملف صورة صحيح"""
        # إنشاء ملف صورة وهمي
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        image_file = SimpleUploadedFile(
            'test_image.png',
            image_content,
            content_type='image/png'
        )
        
        # يجب أن يمر الاختبار
        try:
            self.validator.validate_file(image_file, 'image')
        except ValidationError:
            self.fail('Valid image file should pass validation')
    
    def test_invalid_file_extension(self):
        """اختبار امتداد ملف غير صحيح"""
        malicious_file = SimpleUploadedFile(
            'malicious.exe',
            b'malicious content',
            content_type='application/octet-stream'
        )
        
        with self.assertRaises(ValidationError):
            self.validator.validate_file(malicious_file, 'image')
    
    def test_oversized_file(self):
        """اختبار ملف كبير الحجم"""
        # إنشاء ملف كبير (أكبر من الحد المسموح)
        large_content = b'x' * (6 * 1024 * 1024)  # 6 MB
        large_file = SimpleUploadedFile(
            'large_image.jpg',
            large_content,
            content_type='image/jpeg'
        )
        
        with self.assertRaises(ValidationError):
            self.validator.validate_file(large_file, 'image')
    
    def test_malicious_filename(self):
        """اختبار اسم ملف ضار"""
        malicious_filenames = [
            '../../../etc/passwd',
            'file<script>.jpg',
            'file"dangerous".png',
            'file|pipe.pdf',
        ]
        
        for filename in malicious_filenames:
            malicious_file = SimpleUploadedFile(
                filename,
                b'content',
                content_type='image/jpeg'
            )
            
            with self.assertRaises(ValidationError):
                self.validator.validate_file(malicious_file, 'image')


class InputSanitizerTest(TestCase):
    """اختبار منظف المدخلات"""
    
    def test_html_sanitization(self):
        """اختبار تنظيف HTML"""
        malicious_html = '<script>alert("xss")</script><p>Safe content</p>'
        sanitized = InputSanitizer.sanitize_html(malicious_html)
        
        # يجب إزالة script وإبقاء p
        self.assertNotIn('<script>', sanitized)
        self.assertIn('<p>Safe content</p>', sanitized)
    
    def test_filename_sanitization(self):
        """اختبار تنظيف أسماء الملفات"""
        dangerous_filename = 'file<>:"|?*.txt'
        sanitized = InputSanitizer.sanitize_filename(dangerous_filename)
        
        # يجب إزالة الأحرف الخطيرة
        self.assertEqual(sanitized, 'file.txt')
    
    def test_sql_input_sanitization(self):
        """اختبار تنظيف مدخلات SQL"""
        malicious_input = "'; DROP TABLE users; --"
        sanitized = InputSanitizer.sanitize_sql_input(malicious_input)
        
        # يجب إزالة الكلمات المفتاحية الخطيرة
        self.assertNotIn('DROP', sanitized.upper())
        self.assertNotIn('TABLE', sanitized.upper())


class AuthenticationSecurityTest(TestCase):
    """اختبار أمان المصادقة"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
    
    def test_login_with_valid_credentials(self):
        """اختبار تسجيل الدخول بمعلومات صحيحة"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test@example.com',
            'password': 'TestPass123!'
        })
        
        # يجب أن ينجح تسجيل الدخول
        self.assertEqual(response.status_code, 302)  # إعادة توجيه
    
    def test_login_with_invalid_credentials(self):
        """اختبار تسجيل الدخول بمعلومات خاطئة"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        # يجب أن يفشل تسجيل الدخول
        self.assertEqual(response.status_code, 200)  # البقاء في نفس الصفحة
        self.assertContains(response, 'خطأ')
    
    def test_csrf_protection(self):
        """اختبار حماية CSRF"""
        # محاولة POST بدون CSRF token
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test@example.com',
            'password': 'TestPass123!'
        }, HTTP_X_CSRFTOKEN='invalid')
        
        # يجب رفض الطلب
        self.assertEqual(response.status_code, 403)
    
    def test_session_security(self):
        """اختبار أمان الجلسات"""
        # تسجيل الدخول
        self.client.login(email='test@example.com', password='TestPass123!')
        
        # التحقق من وجود الجلسة
        self.assertIn('_auth_user_id', self.client.session)
        
        # تسجيل الخروج
        self.client.logout()
        
        # التحقق من إزالة الجلسة
        self.assertNotIn('_auth_user_id', self.client.session)


class AccessControlTest(TestCase):
    """اختبار التحكم في الوصول"""
    
    def setUp(self):
        self.client = Client()
        
        # إنشاء مستخدمين مختلفين
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='AdminPass123!',
            user_type='admin'
        )
        
        self.student_user = User.objects.create_user(
            email='student@example.com',
            password='StudentPass123!',
            user_type='student'
        )
        
        self.instructor_user = User.objects.create_user(
            email='instructor@example.com',
            password='InstructorPass123!',
            user_type='instructor'
        )
    
    def test_admin_access(self):
        """اختبار وصول المدير"""
        self.client.login(email='admin@example.com', password='AdminPass123!')
        
        # المدير يجب أن يصل لجميع الصفحات
        admin_urls = [
            reverse('analytics:dashboard'),
            reverse('accounts:admin_students'),
        ]
        
        for url in admin_urls:
            response = self.client.get(url)
            self.assertNotEqual(response.status_code, 403)
    
    def test_student_access_restriction(self):
        """اختبار قيود وصول الطالب"""
        self.client.login(email='student@example.com', password='StudentPass123!')
        
        # الطالب لا يجب أن يصل لصفحات الإدارة
        restricted_urls = [
            reverse('analytics:dashboard'),
            reverse('accounts:admin_students'),
        ]
        
        for url in restricted_urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [403, 302])  # منع أو إعادة توجيه
    
    def test_anonymous_access_restriction(self):
        """اختبار قيود الوصول للمستخدمين غير المسجلين"""
        # المستخدم غير المسجل لا يجب أن يصل للصفحات المحمية
        protected_urls = [
            reverse('accounts:dashboard'),
            reverse('accounts:profile'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # إعادة توجيه لتسجيل الدخول


class DataValidationTest(TestCase):
    """اختبار التحقق من صحة البيانات"""
    
    def test_no_special_chars_validator(self):
        """اختبار مدقق الأحرف الخاصة"""
        # نص آمن
        safe_text = 'نص آمن بدون أحرف خاصة'
        try:
            validate_no_special_chars(safe_text)
        except ValidationError:
            self.fail('Safe text should pass validation')
        
        # نص خطير
        dangerous_texts = [
            'نص يحتوي على <script>',
            'نص يحتوي على "quotes"',
            "نص يحتوي على 'single quotes'",
            'نص يحتوي على >',
        ]
        
        for text in dangerous_texts:
            with self.assertRaises(ValidationError):
                validate_no_special_chars(text)


@override_settings(DEBUG=False)
class ProductionSecurityTest(TestCase):
    """اختبار الأمان في بيئة الإنتاج"""
    
    def test_debug_disabled(self):
        """التحقق من إيقاف وضع التطوير"""
        from django.conf import settings
        self.assertFalse(settings.DEBUG)
    
    def test_secure_headers_in_production(self):
        """اختبار headers الأمان في الإنتاج"""
        response = self.client.get('/')
        
        # يجب وجود HSTS في الإنتاج
        self.assertIn('Strict-Transport-Security', response)
    
    def test_secret_key_security(self):
        """التحقق من أمان المفتاح السري"""
        from django.conf import settings
        
        # المفتاح السري يجب ألا يكون فارغاً أو افتراضياً
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertNotEqual(settings.SECRET_KEY, '')
        self.assertGreater(len(settings.SECRET_KEY), 20)
