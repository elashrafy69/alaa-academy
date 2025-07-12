#!/usr/bin/env python
"""
سكريبت لإنشاء مستخدم مدير
"""
import os
import sys
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alaa_academy.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# إنشاء مستخدم مدير
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@alaa-academy.com',
        password='admin123',
        first_name='علاء',
        last_name='عبد الحميد',
        user_type='admin',
        is_staff=True,
        is_superuser=True,
        is_verified=True
    )
    print(f"تم إنشاء المستخدم المدير: {admin_user.username}")
else:
    print("المستخدم المدير موجود بالفعل")

# إنشاء مستخدم طالب للاختبار
if not User.objects.filter(username='student').exists():
    student_user = User.objects.create_user(
        username='student',
        email='student@example.com',
        password='student123',
        first_name='أحمد',
        last_name='محمد',
        user_type='student',
        is_verified=True
    )
    print(f"تم إنشاء المستخدم الطالب: {student_user.username}")
else:
    print("المستخدم الطالب موجود بالفعل")
