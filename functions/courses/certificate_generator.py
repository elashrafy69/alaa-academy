"""
نظام توليد الشهادات المتقدم
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import Color, black, white, blue
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO
import os
from django.conf import settings
from django.utils import timezone
import qrcode
from PIL import Image, ImageDraw


class CertificateGenerator:
    """مولد الشهادات المتقدم"""
    
    def __init__(self):
        self.width, self.height = landscape(A4)
        self.margin = 1 * inch
        
        # الألوان
        self.primary_color = Color(0.4, 0.49, 0.92)  # #667eea
        self.secondary_color = Color(0.46, 0.29, 0.64)  # #764ba2
        self.text_color = Color(0.17, 0.24, 0.31)  # #2c3e50
        self.light_gray = Color(0.95, 0.95, 0.95)
        
    def generate_certificate(self, enrollment):
        """توليد شهادة PDF"""
        buffer = BytesIO()
        
        # إنشاء الـ PDF
        p = canvas.Canvas(buffer, pagesize=landscape(A4))
        
        # رسم الخلفية والإطار
        self._draw_background(p)
        self._draw_border(p)
        
        # رسم الهيدر
        self._draw_header(p)
        
        # رسم المحتوى الرئيسي
        self._draw_main_content(p, enrollment)
        
        # رسم الفوتر
        self._draw_footer(p, enrollment)
        
        # رسم QR Code
        self._draw_qr_code(p, enrollment)
        
        # إنهاء الـ PDF
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer
    
    def _draw_background(self, p):
        """رسم الخلفية"""
        # خلفية متدرجة (محاكاة)
        p.setFillColor(white)
        p.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        # إضافة عناصر زخرفية
        p.setFillColor(self.light_gray)
        p.setStrokeColor(self.light_gray)
        
        # دوائر زخرفية في الخلفية
        for i in range(5):
            x = (i + 1) * (self.width / 6)
            y = self.height - 50
            p.circle(x, y, 20, fill=1, stroke=0)
            
        for i in range(5):
            x = (i + 1) * (self.width / 6)
            y = 50
            p.circle(x, y, 20, fill=1, stroke=0)
    
    def _draw_border(self, p):
        """رسم الإطار"""
        # الإطار الخارجي
        p.setStrokeColor(self.primary_color)
        p.setLineWidth(4)
        p.rect(self.margin/2, self.margin/2, 
               self.width - self.margin, self.height - self.margin, 
               fill=0, stroke=1)
        
        # الإطار الداخلي
        p.setStrokeColor(self.secondary_color)
        p.setLineWidth(2)
        p.rect(self.margin/2 + 10, self.margin/2 + 10, 
               self.width - self.margin - 20, self.height - self.margin - 20, 
               fill=0, stroke=1)
        
        # خط علوي وسفلي ملون
        p.setFillColor(self.primary_color)
        p.rect(self.margin/2, self.height - self.margin/2 - 10, 
               self.width - self.margin, 10, fill=1, stroke=0)
        p.rect(self.margin/2, self.margin/2, 
               self.width - self.margin, 10, fill=1, stroke=0)
    
    def _draw_header(self, p):
        """رسم الهيدر"""
        # شعار الأكاديمية (دائرة مع أيقونة)
        center_x = self.width / 2
        logo_y = self.height - 120
        
        # دائرة الشعار
        p.setFillColor(self.primary_color)
        p.circle(center_x, logo_y, 40, fill=1, stroke=0)
        
        # أيقونة التخرج (نص بديل)
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredText(center_x, logo_y - 8, "🎓")
        
        # عنوان الشهادة
        p.setFillColor(self.text_color)
        p.setFont("Helvetica-Bold", 36)
        p.drawCentredText(center_x, logo_y - 80, "Certificate of Completion")
        
        # اسم الأكاديمية
        p.setFont("Helvetica", 18)
        p.drawCentredText(center_x, logo_y - 110, "Alaa Abdulhamid Academy")
    
    def _draw_main_content(self, p, enrollment):
        """رسم المحتوى الرئيسي"""
        center_x = self.width / 2
        content_y = self.height - 280
        
        # نص "هذا يشهد أن"
        p.setFillColor(self.text_color)
        p.setFont("Helvetica", 16)
        p.drawCentredText(center_x, content_y, "This is to certify that")
        
        # اسم الطالب
        student_name = enrollment.student.get_full_name()
        p.setFont("Helvetica-Bold", 28)
        p.drawCentredText(center_x, content_y - 40, student_name)
        
        # خط تحت الاسم
        name_width = p.stringWidth(student_name, "Helvetica-Bold", 28)
        line_start = center_x - (name_width / 2) - 20
        line_end = center_x + (name_width / 2) + 20
        p.setStrokeColor(self.primary_color)
        p.setLineWidth(2)
        p.line(line_start, content_y - 50, line_end, content_y - 50)
        
        # نص "أكمل بنجاح"
        p.setFont("Helvetica", 16)
        p.drawCentredText(center_x, content_y - 80, "has successfully completed")
        
        # اسم الدورة
        course_title = enrollment.course.title
        p.setFont("Helvetica-Bold", 22)
        p.setFillColor(self.primary_color)
        p.drawCentredText(center_x, content_y - 120, course_title)
        
        # معلومات الدورة
        p.setFillColor(self.text_color)
        p.setFont("Helvetica", 12)
        
        # إحصائيات الدورة
        stats_y = content_y - 160
        stats = [
            f"Duration: {enrollment.course.estimated_duration} hours",
            f"Lessons: {enrollment.course.total_lessons}",
            f"Level: {enrollment.course.get_difficulty_level_display()}"
        ]
        
        # رسم الإحصائيات في صناديق
        box_width = 150
        box_height = 30
        start_x = center_x - (len(stats) * box_width) / 2
        
        for i, stat in enumerate(stats):
            box_x = start_x + (i * box_width)
            
            # صندوق الإحصائية
            p.setFillColor(self.light_gray)
            p.rect(box_x, stats_y - 15, box_width - 10, box_height, fill=1, stroke=0)
            
            # نص الإحصائية
            p.setFillColor(self.text_color)
            p.drawCentredText(box_x + (box_width - 10) / 2, stats_y, stat)
    
    def _draw_footer(self, p, enrollment):
        """رسم الفوتر"""
        footer_y = 120
        
        # التاريخ
        date_x = self.margin + 100
        p.setFont("Helvetica", 12)
        p.setFillColor(self.text_color)
        p.drawCentredText(date_x, footer_y + 20, "Date of Issue")
        p.setFont("Helvetica-Bold", 14)
        issue_date = enrollment.completion_date or timezone.now()
        p.drawCentredText(date_x, footer_y, issue_date.strftime("%B %d, %Y"))
        
        # خط التوقيع
        p.setStrokeColor(self.text_color)
        p.line(date_x - 60, footer_y - 10, date_x + 60, footer_y - 10)
        
        # المدرب
        instructor_x = self.width - self.margin - 100
        p.setFont("Helvetica", 12)
        p.drawCentredText(instructor_x, footer_y + 20, "Instructor")
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredText(instructor_x, footer_y, enrollment.course.instructor.get_full_name())
        
        # خط التوقيع
        p.line(instructor_x - 60, footer_y - 10, instructor_x + 60, footer_y - 10)
        
        # رقم الشهادة
        cert_number = enrollment.certificate.certificate_number
        p.setFont("Helvetica", 10)
        p.setFillColor(Color(0.5, 0.5, 0.5))
        p.drawCentredText(self.width / 2, 60, f"Certificate No: {cert_number}")
        p.drawCentredText(self.width / 2, 45, "Verify at: academy.alaa-abdulhamid.com")
    
    def _draw_qr_code(self, p, enrollment):
        """رسم QR Code للتحقق"""
        # إنشاء QR Code
        qr_data = f"https://academy.alaa-abdulhamid.com/verify/{enrollment.certificate.certificate_number}"
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # تحويل QR إلى صورة
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # حفظ QR مؤقتاً
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # رسم QR Code على الـ PDF
        qr_x = self.width / 2 - 30
        qr_y = 80
        p.drawInlineImage(qr_buffer, qr_x, qr_y, width=60, height=60)
    
    def generate_verification_qr(self, certificate_number):
        """توليد QR Code للتحقق"""
        qr_data = f"https://academy.alaa-abdulhamid.com/verify/{certificate_number}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        return qr.make_image(fill_color="black", back_color="white")


def generate_certificate_pdf(enrollment):
    """دالة مساعدة لتوليد شهادة PDF"""
    generator = CertificateGenerator()
    return generator.generate_certificate(enrollment)
