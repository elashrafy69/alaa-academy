"""
مدققات الأمان
"""

import re
import magic
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import os


class SecurePasswordValidator:
    """مدقق كلمات المرور الآمنة"""
    
    def __init__(self, min_length=8):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        """التحقق من قوة كلمة المرور"""
        errors = []
        
        # الطول الأدنى
        if len(password) < self.min_length:
            errors.append(f'كلمة المرور يجب أن تكون {self.min_length} أحرف على الأقل')
        
        # وجود أحرف كبيرة
        if not re.search(r'[A-Z]', password):
            errors.append('كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل')
        
        # وجود أحرف صغيرة
        if not re.search(r'[a-z]', password):
            errors.append('كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل')
        
        # وجود أرقام
        if not re.search(r'\d', password):
            errors.append('كلمة المرور يجب أن تحتوي على رقم واحد على الأقل')
        
        # وجود رموز خاصة
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل')
        
        # التحقق من عدم وجود معلومات المستخدم
        if user:
            user_info = [
                user.first_name.lower() if user.first_name else '',
                user.last_name.lower() if user.last_name else '',
                user.email.split('@')[0].lower() if user.email else '',
            ]
            
            password_lower = password.lower()
            for info in user_info:
                if info and len(info) > 2 and info in password_lower:
                    errors.append('كلمة المرور لا يجب أن تحتوي على معلومات شخصية')
                    break
        
        # كلمات المرور الشائعة
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in common_passwords:
            errors.append('كلمة المرور شائعة جداً، يرجى اختيار كلمة مرور أقوى')
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            'كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل، '
            'وتتضمن أحرف كبيرة وصغيرة وأرقام ورموز خاصة'
        )


class FileSecurityValidator:
    """مدقق أمان الملفات"""
    
    def __init__(self):
        # الامتدادات المسموحة
        self.allowed_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            'video': ['.mp4', '.webm', '.ogg', '.avi', '.mov'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
            'archive': ['.zip', '.rar', '.7z'],
        }
        
        # الأنواع MIME المسموحة
        self.allowed_mime_types = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/webm', 'video/ogg',
            'audio/mpeg', 'audio/wav', 'audio/ogg',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain', 'application/rtf',
            'application/zip', 'application/x-rar-compressed',
        }
        
        # الحد الأقصى لحجم الملف (بالبايت)
        self.max_file_sizes = {
            'image': 5 * 1024 * 1024,  # 5 MB
            'video': 100 * 1024 * 1024,  # 100 MB
            'audio': 20 * 1024 * 1024,  # 20 MB
            'document': 10 * 1024 * 1024,  # 10 MB
            'archive': 50 * 1024 * 1024,  # 50 MB
        }
    
    def validate_file(self, file, file_type='document'):
        """التحقق من أمان الملف"""
        errors = []
        
        # التحقق من وجود الملف
        if not file:
            raise ValidationError('لم يتم رفع أي ملف')
        
        # التحقق من الامتداد
        file_extension = os.path.splitext(file.name)[1].lower()
        allowed_extensions = self.allowed_extensions.get(file_type, [])
        
        if file_extension not in allowed_extensions:
            errors.append(f'امتداد الملف غير مدعوم. الامتدادات المسموحة: {", ".join(allowed_extensions)}')
        
        # التحقق من حجم الملف
        max_size = self.max_file_sizes.get(file_type, 10 * 1024 * 1024)
        if file.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            errors.append(f'حجم الملف كبير جداً. الحد الأقصى: {max_size_mb:.1f} MB')
        
        # التحقق من نوع MIME
        try:
            # قراءة أول 1024 بايت للتحقق من نوع الملف
            file.seek(0)
            file_header = file.read(1024)
            file.seek(0)
            
            # استخدام python-magic للتحقق من نوع الملف الحقيقي
            mime_type = magic.from_buffer(file_header, mime=True)
            
            if mime_type not in self.allowed_mime_types:
                errors.append(f'نوع الملف غير مدعوم: {mime_type}')
        
        except Exception as e:
            errors.append('فشل في التحقق من نوع الملف')
        
        # التحقق من اسم الملف
        if not self._is_safe_filename(file.name):
            errors.append('اسم الملف يحتوي على أحرف غير آمنة')
        
        # فحص الملف للبحث عن محتوى ضار
        if self._contains_malicious_content(file):
            errors.append('الملف يحتوي على محتوى ضار محتمل')
        
        if errors:
            raise ValidationError(errors)
        
        return True
    
    def _is_safe_filename(self, filename):
        """التحقق من أمان اسم الملف"""
        # أحرف غير مسموحة
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        
        for char in dangerous_chars:
            if char in filename:
                return False
        
        # التحقق من الطول
        if len(filename) > 255:
            return False
        
        # التحقق من أن الاسم لا يبدأ بنقطة
        if filename.startswith('.'):
            return False
        
        return True
    
    def _contains_malicious_content(self, file):
        """فحص الملف للبحث عن محتوى ضار"""
        try:
            file.seek(0)
            content = file.read(1024).decode('utf-8', errors='ignore')
            file.seek(0)
            
            # أنماط ضارة
            malicious_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'vbscript:',
                r'onload\s*=',
                r'onerror\s*=',
                r'eval\s*\(',
                r'exec\s*\(',
            ]
            
            for pattern in malicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
        
        except:
            # إذا فشل في قراءة الملف كنص، فهو على الأرجح ملف ثنائي آمن
            pass
        
        return False


class InputSanitizer:
    """منظف المدخلات"""
    
    @staticmethod
    def sanitize_html(text):
        """تنظيف HTML من العناصر الضارة"""
        import bleach
        
        # العلامات المسموحة
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'
        ]
        
        # الخصائص المسموحة
        allowed_attributes = {
            '*': ['class'],
        }
        
        return bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes)
    
    @staticmethod
    def sanitize_filename(filename):
        """تنظيف اسم الملف"""
        # إزالة الأحرف الخطيرة
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # إزالة المسافات المتعددة
        filename = re.sub(r'\s+', '_', filename)
        
        # إزالة النقاط المتعددة
        filename = re.sub(r'\.+', '.', filename)
        
        # قطع الاسم إذا كان طويلاً
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        
        return filename
    
    @staticmethod
    def sanitize_sql_input(text):
        """تنظيف المدخلات من SQL injection"""
        if not isinstance(text, str):
            return text
        
        # إزالة الكلمات المفتاحية الخطيرة
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER',
            'EXEC', 'EXECUTE', 'UNION', 'SELECT', 'SCRIPT'
        ]
        
        text_upper = text.upper()
        for keyword in dangerous_keywords:
            if keyword in text_upper:
                text = text.replace(keyword.lower(), '')
                text = text.replace(keyword.upper(), '')
                text = text.replace(keyword.capitalize(), '')
        
        return text


# مدققات مخصصة للنماذج
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message='رقم الهاتف يجب أن يكون بين 9-15 رقم ويمكن أن يبدأ بـ +'
)

arabic_name_validator = RegexValidator(
    regex=r'^[\u0600-\u06FF\s]+$',
    message='الاسم يجب أن يحتوي على أحرف عربية فقط'
)

username_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9_]+$',
    message='اسم المستخدم يجب أن يحتوي على أحرف إنجليزية وأرقام وشرطة سفلية فقط'
)


def validate_no_special_chars(value):
    """التحقق من عدم وجود أحرف خاصة"""
    if re.search(r'[<>"\']', value):
        raise ValidationError('لا يمكن أن يحتوي النص على أحرف خاصة مثل < > " \'')


def validate_safe_url(value):
    """التحقق من أمان الرابط"""
    if not value.startswith(('http://', 'https://')):
        raise ValidationError('الرابط يجب أن يبدأ بـ http:// أو https://')
    
    # التحقق من عدم وجود أحرف خطيرة
    dangerous_chars = ['<', '>', '"', "'", 'javascript:', 'vbscript:']
    for char in dangerous_chars:
        if char in value.lower():
            raise ValidationError('الرابط يحتوي على أحرف غير آمنة')


def validate_course_code(value):
    """التحقق من صحة كود الدورة"""
    if not re.match(r'^[A-Z]{2,4}\d{3,4}$', value):
        raise ValidationError('كود الدورة يجب أن يكون بصيغة ABC123 (2-4 أحرف كبيرة متبوعة بـ 3-4 أرقام)')


def validate_registration_code(value):
    """التحقق من صحة كود التسجيل"""
    if not re.match(r'^[A-Z0-9]{6,12}$', value):
        raise ValidationError('كود التسجيل يجب أن يكون 6-12 حرف كبير أو رقم')


def validate_positive_duration(value):
    """التحقق من أن المدة موجبة"""
    if value <= 0:
        raise ValidationError('المدة يجب أن تكون أكبر من صفر')


def validate_price(value):
    """التحقق من صحة السعر"""
    if value < 0:
        raise ValidationError('السعر لا يمكن أن يكون سالباً')
    
    if value > 10000:
        raise ValidationError('السعر لا يمكن أن يتجاوز 10,000 ريال')
