#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alaa_academy.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# حذف المدير القديم إذا كان موجوداً
try:
    old_admin = User.objects.get(email='admin@alaa-academy.com')
    old_admin.delete()
    print("تم حذف المدير القديم")
except User.DoesNotExist:
    print("لا يوجد مدير قديم")

# إنشاء مدير جديد
admin_user = User.objects.create_superuser(
    email='admin@alaa-academy.com',
    password='123456',
    first_name='مدير',
    last_name='النظام',
    user_type='admin'
)

print("✅ تم إنشاء المدير بنجاح!")
print("📧 البريد الإلكتروني: admin@alaa-academy.com")
print("🔑 كلمة المرور: 123456")
print("🌐 رابط لوحة التحكم: http://127.0.0.1:8000/admin/")
