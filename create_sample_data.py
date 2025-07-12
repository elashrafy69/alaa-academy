#!/usr/bin/env python
"""
سكريبت لإنشاء بيانات تجريبية
"""
import os
import sys
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alaa_academy.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Category, Course
from accounts.models import RegistrationCode

User = get_user_model()

def create_sample_data():
    print("إنشاء البيانات التجريبية...")
    
    # إنشاء الفئات
    categories_data = [
        {
            'name': 'التسويق الرقمي',
            'description': 'دورات متخصصة في التسويق الرقمي ووسائل التواصل الاجتماعي',
            'icon': 'fas fa-bullhorn',
            'color': '#3498db'
        },
        {
            'name': 'ريادة الأعمال',
            'description': 'دورات لتطوير المهارات الريادية وإدارة الأعمال',
            'icon': 'fas fa-rocket',
            'color': '#e74c3c'
        },
        {
            'name': 'المبيعات',
            'description': 'تطوير مهارات البيع والتفاوض',
            'icon': 'fas fa-handshake',
            'color': '#2ecc71'
        },
        {
            'name': 'التطوير الشخصي',
            'description': 'دورات لتطوير الذات والمهارات الشخصية',
            'icon': 'fas fa-user-graduate',
            'color': '#f39c12'
        }
    ]
    
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        if created:
            print(f"تم إنشاء فئة: {category.name}")
    
    # الحصول على المدير
    admin_user = User.objects.get(username='admin')
    
    # إنشاء الدورات
    courses_data = [
        {
            'title': 'أساسيات التسويق الرقمي',
            'slug': 'digital-marketing-basics',
            'description': 'تعلم أساسيات التسويق الرقمي من الصفر حتى الاحتراف. ستتعلم في هذه الدورة كيفية إنشاء استراتيجيات تسويقية فعالة، واستخدام وسائل التواصل الاجتماعي، وتحليل البيانات لتحسين الأداء.',
            'short_description': 'دورة شاملة لتعلم أساسيات التسويق الرقمي والوصول للعملاء المستهدفين',
            'category': Category.objects.get(name='التسويق الرقمي'),
            'instructor': admin_user,
            'difficulty_level': 'beginner',
            'status': 'published',
            'price': 299.00,
            'estimated_duration': 20,
            'learning_objectives': '''
• فهم مفاهيم التسويق الرقمي الأساسية
• إنشاء استراتيجيات تسويقية فعالة
• استخدام وسائل التواصل الاجتماعي للتسويق
• تحليل البيانات وقياس الأداء
• إنشاء حملات إعلانية ناجحة
            ''',
            'prerequisites': 'لا توجد متطلبات مسبقة، الدورة مناسبة للمبتدئين',
            'is_featured': True
        },
        {
            'title': 'إدارة وسائل التواصل الاجتماعي',
            'slug': 'social-media-management',
            'description': 'تعلم كيفية إدارة حسابات وسائل التواصل الاجتماعي بشكل احترافي وإنشاء محتوى جذاب يحقق أهدافك التسويقية.',
            'short_description': 'إدارة احترافية لحسابات وسائل التواصل الاجتماعي وإنشاء محتوى جذاب',
            'category': Category.objects.get(name='التسويق الرقمي'),
            'instructor': admin_user,
            'difficulty_level': 'intermediate',
            'status': 'published',
            'price': 399.00,
            'estimated_duration': 15,
            'learning_objectives': '''
• إنشاء استراتيجية محتوى فعالة
• إدارة الحسابات على منصات مختلفة
• تحليل الأداء وتحسين النتائج
• التفاعل مع الجمهور بشكل احترافي
            ''',
            'prerequisites': 'معرفة أساسية بوسائل التواصل الاجتماعي'
        },
        {
            'title': 'بناء مشروعك الناجح',
            'slug': 'successful-business-building',
            'description': 'دورة شاملة لتعلم كيفية بناء مشروع ناجح من الفكرة حتى التنفيذ، مع التركيز على الجوانب العملية والتطبيقية.',
            'short_description': 'تعلم كيفية بناء مشروع ناجح من الفكرة حتى التنفيذ',
            'category': Category.objects.get(name='ريادة الأعمال'),
            'instructor': admin_user,
            'difficulty_level': 'beginner',
            'status': 'published',
            'price': 499.00,
            'estimated_duration': 25,
            'learning_objectives': '''
• تطوير فكرة المشروع وتقييم الجدوى
• إنشاء خطة عمل شاملة
• فهم أساسيات التمويل والاستثمار
• بناء فريق عمل فعال
• تسويق المشروع وجذب العملاء
            ''',
            'prerequisites': 'الرغبة في بدء مشروع خاص'
        },
        {
            'title': 'فن البيع والإقناع',
            'slug': 'sales-and-persuasion-art',
            'description': 'تطوير مهارات البيع والإقناع من خلال تقنيات مثبتة علمياً وتطبيقات عملية في بيئات مختلفة.',
            'short_description': 'تطوير مهارات البيع والإقناع باستخدام تقنيات مثبتة علمياً',
            'category': Category.objects.get(name='المبيعات'),
            'instructor': admin_user,
            'difficulty_level': 'intermediate',
            'status': 'published',
            'price': 349.00,
            'estimated_duration': 18,
            'learning_objectives': '''
• فهم علم النفس في البيع
• تطوير مهارات التواصل والإقناع
• بناء علاقات قوية مع العملاء
• التعامل مع الاعتراضات بفعالية
• إغلاق الصفقات بنجاح
            ''',
            'prerequisites': 'خبرة أساسية في التعامل مع العملاء'
        },
        {
            'title': 'تطوير الذات والثقة بالنفس',
            'slug': 'self-development-confidence',
            'description': 'رحلة شاملة لتطوير الذات وبناء الثقة بالنفس من خلال تمارين عملية واستراتيجيات مثبتة.',
            'short_description': 'رحلة شاملة لتطوير الذات وبناء الثقة بالنفس',
            'category': Category.objects.get(name='التطوير الشخصي'),
            'instructor': admin_user,
            'difficulty_level': 'beginner',
            'status': 'published',
            'price': 0.00,  # دورة مجانية
            'estimated_duration': 12,
            'learning_objectives': '''
• فهم الذات وتحديد نقاط القوة والضعف
• بناء الثقة بالنفس والتغلب على المخاوف
• تطوير مهارات التواصل الفعال
• إدارة الوقت والأولويات
• وضع الأهداف وتحقيقها
            ''',
            'prerequisites': 'لا توجد متطلبات مسبقة',
            'is_featured': True
        }
    ]
    
    for course_data in courses_data:
        course, created = Course.objects.get_or_create(
            slug=course_data['slug'],
            defaults=course_data
        )
        if created:
            print(f"تم إنشاء دورة: {course.title}")
    
    # إنشاء أكواد تسجيل تجريبية
    codes_data = [
        {
            'code': 'WELCOME2024',
            'course': None,  # كود عام
            'max_uses': 100,
            'is_active': True,
            'created_by': admin_user
        },
        {
            'code': 'MARKETING50',
            'course': Course.objects.get(slug='digital-marketing-basics'),
            'max_uses': 50,
            'is_active': True,
            'created_by': admin_user
        }
    ]
    
    for code_data in codes_data:
        code, created = RegistrationCode.objects.get_or_create(
            code=code_data['code'],
            defaults=code_data
        )
        if created:
            print(f"تم إنشاء كود تسجيل: {code.code}")
    
    print("تم إنشاء البيانات التجريبية بنجاح!")

if __name__ == '__main__':
    create_sample_data()
