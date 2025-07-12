#!/usr/bin/env python3
"""
سكريبت نشر المشروع على PythonAnywhere
"""

import os
import subprocess
import sys

def run_command(command):
    """تشغيل أمر في الطرفية"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    """الدالة الرئيسية للنشر"""
    
    print("🚀 بدء نشر المشروع على PythonAnywhere...")
    print("=" * 60)
    
    # خطوات النشر
    steps = [
        "تحديث pip",
        "تثبيت المتطلبات", 
        "جمع الملفات الثابتة",
        "تشغيل migrations",
        "إنشاء البيانات الأولية"
    ]
    
    commands = [
        "pip install --upgrade pip",
        "pip install -r requirements.txt",
        "python manage.py collectstatic --noinput",
        "python manage.py migrate",
        "python setup_production.py"
    ]
    
    for i, (step, command) in enumerate(zip(steps, commands), 1):
        print(f"\n📋 الخطوة {i}: {step}")
        print("-" * 40)
        
        if not run_command(command):
            print(f"❌ فشل في الخطوة: {step}")
            return False
        
        print(f"✅ تمت الخطوة: {step}")
    
    print("\n" + "=" * 60)
    print("🎉 تم نشر المشروع بنجاح!")
    print("🌐 المشروع جاهز للاستخدام")
    print("👤 معلومات تسجيل الدخول:")
    print("   📧 البريد: admin@marketwise-academy.com")
    print("   🔑 كلمة المرور: AdminPass123!")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
