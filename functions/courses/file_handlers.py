"""
نظام رفع ومعالجة الملفات المتقدم
"""

import os
import uuid
import mimetypes
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from PIL import Image
import magic
from moviepy.editor import VideoFileClip
import PyPDF2
from io import BytesIO


class FileValidator:
    """فئة للتحقق من صحة الملفات"""
    
    # أنواع الملفات المسموحة
    ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv']
    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'application/msword', 
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    
    # أحجام الملفات القصوى (بالبايت)
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
    MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50 MB
    
    @staticmethod
    def validate_file_type(file, expected_type):
        """التحقق من نوع الملف"""
        # استخدام python-magic للتحقق الدقيق من نوع الملف
        file_type = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # إعادة تعيين مؤشر الملف
        
        if expected_type == 'video' and file_type not in FileValidator.ALLOWED_VIDEO_TYPES:
            raise ValidationError(f'نوع الفيديو غير مدعوم. الأنواع المدعومة: {", ".join(FileValidator.ALLOWED_VIDEO_TYPES)}')
        
        elif expected_type == 'image' and file_type not in FileValidator.ALLOWED_IMAGE_TYPES:
            raise ValidationError(f'نوع الصورة غير مدعوم. الأنواع المدعومة: {", ".join(FileValidator.ALLOWED_IMAGE_TYPES)}')
        
        elif expected_type == 'document' and file_type not in FileValidator.ALLOWED_DOCUMENT_TYPES:
            raise ValidationError(f'نوع المستند غير مدعوم. الأنواع المدعومة: {", ".join(FileValidator.ALLOWED_DOCUMENT_TYPES)}')
        
        return file_type
    
    @staticmethod
    def validate_file_size(file, file_type):
        """التحقق من حجم الملف"""
        file_size = file.size
        
        if file_type in FileValidator.ALLOWED_VIDEO_TYPES and file_size > FileValidator.MAX_VIDEO_SIZE:
            raise ValidationError(f'حجم الفيديو كبير جداً. الحد الأقصى: {FileValidator.MAX_VIDEO_SIZE // (1024*1024)} MB')
        
        elif file_type in FileValidator.ALLOWED_IMAGE_TYPES and file_size > FileValidator.MAX_IMAGE_SIZE:
            raise ValidationError(f'حجم الصورة كبير جداً. الحد الأقصى: {FileValidator.MAX_IMAGE_SIZE // (1024*1024)} MB')
        
        elif file_type in FileValidator.ALLOWED_DOCUMENT_TYPES and file_size > FileValidator.MAX_DOCUMENT_SIZE:
            raise ValidationError(f'حجم المستند كبير جداً. الحد الأقصى: {FileValidator.MAX_DOCUMENT_SIZE // (1024*1024)} MB')
    
    @staticmethod
    def validate_video_content(file):
        """التحقق من محتوى الفيديو"""
        try:
            # حفظ مؤقت للفيديو للتحقق منه
            temp_path = f'/tmp/{uuid.uuid4()}.mp4'
            with open(temp_path, 'wb') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
            
            # فحص الفيديو باستخدام moviepy
            clip = VideoFileClip(temp_path)
            duration = clip.duration
            
            # التحقق من المدة (لا تزيد عن 4 ساعات)
            if duration > 14400:  # 4 ساعات
                raise ValidationError('مدة الفيديو طويلة جداً. الحد الأقصى: 4 ساعات')
            
            clip.close()
            os.remove(temp_path)
            
            return duration
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise ValidationError(f'خطأ في معالجة الفيديو: {str(e)}')
    
    @staticmethod
    def validate_pdf_content(file):
        """التحقق من محتوى PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            # التحقق من عدد الصفحات (لا تزيد عن 500 صفحة)
            if num_pages > 500:
                raise ValidationError('عدد صفحات PDF كبير جداً. الحد الأقصى: 500 صفحة')
            
            file.seek(0)  # إعادة تعيين مؤشر الملف
            return num_pages
            
        except Exception as e:
            file.seek(0)
            raise ValidationError(f'خطأ في معالجة PDF: {str(e)}')


class FileUploadHandler:
    """معالج رفع الملفات"""
    
    @staticmethod
    def generate_unique_filename(original_filename, content_type=None):
        """توليد اسم ملف فريد"""
        # الحصول على امتداد الملف
        name, ext = os.path.splitext(original_filename)
        
        # تنظيف اسم الملف
        clean_name = slugify(name)[:50]  # أول 50 حرف فقط
        
        # إضافة UUID للتفرد
        unique_id = str(uuid.uuid4())[:8]
        
        # تحديد المجلد حسب نوع المحتوى
        if content_type == 'video':
            folder = 'videos'
        elif content_type == 'image':
            folder = 'images'
        elif content_type == 'document':
            folder = 'documents'
        else:
            folder = 'uploads'
        
        return f'{folder}/{clean_name}_{unique_id}{ext}'
    
    @staticmethod
    def process_image(file, max_width=1920, max_height=1080, quality=85):
        """معالجة وضغط الصور"""
        try:
            # فتح الصورة
            image = Image.open(file)
            
            # تحويل إلى RGB إذا كانت RGBA
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # تغيير الحجم إذا كان كبيراً
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # حفظ الصورة المضغوطة
            output = BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            return output
            
        except Exception as e:
            raise ValidationError(f'خطأ في معالجة الصورة: {str(e)}')
    
    @staticmethod
    def extract_video_thumbnail(file):
        """استخراج صورة مصغرة من الفيديو"""
        try:
            # حفظ مؤقت للفيديو
            temp_path = f'/tmp/{uuid.uuid4()}.mp4'
            with open(temp_path, 'wb') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
            
            # استخراج الصورة المصغرة
            clip = VideoFileClip(temp_path)
            
            # أخذ إطار من منتصف الفيديو
            thumbnail_time = clip.duration / 2
            thumbnail = clip.get_frame(thumbnail_time)
            
            # تحويل إلى صورة PIL
            thumbnail_image = Image.fromarray(thumbnail)
            
            # ضغط الصورة المصغرة
            thumbnail_image.thumbnail((320, 240), Image.Resampling.LANCZOS)
            
            # حفظ في buffer
            output = BytesIO()
            thumbnail_image.save(output, format='JPEG', quality=80)
            output.seek(0)
            
            clip.close()
            os.remove(temp_path)
            
            return output
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise ValidationError(f'خطأ في استخراج الصورة المصغرة: {str(e)}')
    
    @staticmethod
    def upload_file(file, content_type, course_id=None):
        """رفع الملف مع المعالجة الكاملة"""
        try:
            # التحقق من نوع الملف
            file_type = FileValidator.validate_file_type(file, content_type)
            
            # التحقق من حجم الملف
            FileValidator.validate_file_size(file, file_type)
            
            # معالجة خاصة حسب نوع الملف
            processed_file = file
            metadata = {}
            
            if content_type == 'video':
                # التحقق من محتوى الفيديو
                duration = FileValidator.validate_video_content(file)
                metadata['duration'] = duration
                
                # استخراج صورة مصغرة
                try:
                    thumbnail = FileUploadHandler.extract_video_thumbnail(file)
                    thumbnail_filename = FileUploadHandler.generate_unique_filename(
                        f"{file.name}_thumbnail.jpg", 'image'
                    )
                    thumbnail_path = default_storage.save(thumbnail_filename, thumbnail)
                    metadata['thumbnail'] = thumbnail_path
                except:
                    pass  # إذا فشل استخراج الصورة المصغرة، نتجاهل الخطأ
            
            elif content_type == 'image':
                # معالجة الصورة
                processed_file = FileUploadHandler.process_image(file)
                
            elif content_type == 'document' and file_type == 'application/pdf':
                # التحقق من محتوى PDF
                num_pages = FileValidator.validate_pdf_content(file)
                metadata['pages'] = num_pages
            
            # توليد اسم ملف فريد
            filename = FileUploadHandler.generate_unique_filename(file.name, content_type)
            
            # رفع الملف
            file_path = default_storage.save(filename, processed_file)
            
            # إرجاع معلومات الملف
            return {
                'file_path': file_path,
                'file_url': default_storage.url(file_path),
                'file_size': file.size,
                'file_type': file_type,
                'metadata': metadata
            }
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f'خطأ في رفع الملف: {str(e)}')


class FileSecurityManager:
    """مدير أمان الملفات"""
    
    @staticmethod
    def scan_file_for_malware(file):
        """فحص الملف للبحث عن البرمجيات الخبيثة"""
        # هذه دالة أساسية - يمكن تطويرها لاستخدام خدمات فحص متقدمة
        
        # فحص أساسي للامتدادات الخطيرة
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
        filename = file.name.lower()
        
        for ext in dangerous_extensions:
            if filename.endswith(ext):
                raise ValidationError('نوع الملف غير آمن')
        
        return True
    
    @staticmethod
    def generate_secure_url(file_path, expiry_hours=24):
        """توليد رابط آمن مؤقت للملف"""
        # يمكن تطوير هذه الدالة لتوليد روابط مؤقتة آمنة
        return default_storage.url(file_path)


def validate_course_file(file, content_type):
    """دالة مساعدة للتحقق من ملفات الدورة"""
    try:
        # فحص الأمان
        FileSecurityManager.scan_file_for_malware(file)
        
        # رفع ومعالجة الملف
        result = FileUploadHandler.upload_file(file, content_type)
        
        return result
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f'خطأ في معالجة الملف: {str(e)}')
