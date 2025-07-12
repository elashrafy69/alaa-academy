#!/usr/bin/env python
import os
import sys
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alaa_academy.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# التحقق من وجود مستخدم مدير
if not User.objects.filter(is_superuser=True).exists():
    # إنشاء مستخدم مدير
    User.objects.create_superuser(
        email='admin@marketwise-academy.com',
        password='AdminPass123!',
        first_name='Admin',
        last_name='User',
        user_type='admin'
    )
    print('✅ Superuser created successfully!')
    print('Email: admin@marketwise-academy.com')
    print('Password: AdminPass123!')
else:
    print('✅ Superuser already exists')
