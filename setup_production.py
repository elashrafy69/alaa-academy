#!/usr/bin/env python
"""
إعداد البيانات الأولية للإنتاج
"""

import os
import sys
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alaa_academy.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Category, Course

User = get_user_model()

def create_admin_user():
    """إنشاء مستخدم مدير"""
    if not User.objects.filter(is_superuser=True).exists():
        admin = User.objects.create_superuser(
            email='admin@marketwise-academy.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
            user_type='admin'
        )
        print('✅ تم إنشاء المستخدم المدير')
        print(f'📧 البريد الإلكتروني: {admin.email}')
        print('🔑 كلمة المرور: AdminPass123!')
    else:
        print('✅ المستخدم المدير موجود بالفعل')

def create_sample_data():
    """إنشاء بيانات تجريبية"""
    
    # إنشاء فئات الدورات
    categories_data = [
        {'name': 'البرمجة وتطوير المواقع', 'description': 'دورات في البرمجة وتطوير المواقع والتطبيقات'},
        {'name': 'التسويق الرقمي', 'description': 'دورات في التسويق الإلكتروني ووسائل التواصل الاجتماعي'},
        {'name': 'التصميم الجرافيكي', 'description': 'دورات في التصميم والجرافيك والفوتوشوب'},
        {'name': 'إدارة الأعمال', 'description': 'دورات في إدارة الأعمال والمشاريع'},
        {'name': 'اللغات', 'description': 'دورات تعلم اللغات المختلفة'},
    ]
    
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        if created:
            print(f'✅ تم إنشاء فئة: {category.name}')
    
    # إنشاء مدرب تجريبي
    instructor, created = User.objects.get_or_create(
        email='instructor@marketwise-academy.com',
        defaults={
            'password': 'pbkdf2_sha256$600000$test$test',  # كلمة مرور مؤقتة
            'first_name': 'علاء',
            'last_name': 'عبد الحميد',
            'user_type': 'instructor',
            'bio': 'مدرب معتمد في التسويق الرقمي وتطوير الأعمال',
            'specialization': 'التسويق الرقمي'
        }
    )
    if created:
        print(f'✅ تم إنشاء المدرب: {instructor.get_full_name()}')
    
    # إنشاء دورات تجريبية
    programming_cat = Category.objects.get(name='البرمجة وتطوير المواقع')
    marketing_cat = Category.objects.get(name='التسويق الرقمي')
    
    courses_data = [
        {
            'title': 'أساسيات البرمجة بـ Python',
            'description': 'تعلم أساسيات البرمجة باستخدام لغة Python من الصفر حتى الاحتراف',
            'short_description': 'دورة شاملة لتعلم البرمجة بـ Python',
            'category': programming_cat,
            'instructor': instructor,
            'price': 299.00,
            'difficulty_level': 'beginner',
            'estimated_duration': 40,
            'status': 'published'
        },
        {
            'title': 'التسويق الرقمي للمبتدئين',
            'description': 'تعلم استراتيجيات التسويق الرقمي الحديثة وكيفية بناء حملات إعلانية ناجحة',
            'short_description': 'دورة شاملة في التسويق الرقمي',
            'category': marketing_cat,
            'instructor': instructor,
            'price': 199.00,
            'difficulty_level': 'beginner',
            'estimated_duration': 25,
            'status': 'published'
        },
        {
            'title': 'تطوير المواقع بـ Django',
            'description': 'تعلم تطوير المواقع الديناميكية باستخدام إطار عمل Django',
            'short_description': 'دورة متقدمة في تطوير المواقع',
            'category': programming_cat,
            'instructor': instructor,
            'price': 399.00,
            'difficulty_level': 'intermediate',
            'estimated_duration': 60,
            'status': 'published'
        }
    ]
    
    for course_data in courses_data:
        course, created = Course.objects.get_or_create(
            title=course_data['title'],
            defaults=course_data
        )
        if created:
            print(f'✅ تم إنشاء دورة: {course.title}')

def main():
    """الدالة الرئيسية"""
    print('🚀 بدء إعداد البيانات الأولية...')
    print('=' * 50)
    
    try:
        create_admin_user()
        create_sample_data()
        
        print('=' * 50)
        print('✅ تم إعداد البيانات الأولية بنجاح!')
        print('🌐 يمكنك الآن استخدام المنصة')
        print('👤 تسجيل دخول المدير:')
        print('   📧 البريد: admin@marketwise-academy.com')
        print('   🔑 كلمة المرور: AdminPass123!')
        
    except Exception as e:
        print(f'❌ خطأ في إعداد البيانات: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
