#!/usr/bin/env python3
"""
سكريبت النشر التلقائي على Vercel
"""
import subprocess
import sys
import os
import webbrowser
import time

def run_command(command, description):
    """تشغيل أمر مع عرض الوصف"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - تم بنجاح")
            return True
        else:
            print(f"❌ خطأ في {description}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ خطأ في {description}: {str(e)}")
        return False

def main():
    print("🚀 بدء النشر التلقائي لأكاديمية علاء على Vercel")
    print("=" * 50)
    
    # التحقق من وجود Node.js
    print("🔍 التحقق من Node.js...")
    if not run_command("node --version", "فحص Node.js"):
        print("❌ Node.js غير مثبت. يرجى تثبيت Node.js أولاً من: https://nodejs.org")
        return
    
    # تثبيت Vercel CLI
    if not run_command("npm install -g vercel", "تثبيت Vercel CLI"):
        print("❌ فشل في تثبيت Vercel CLI")
        return
    
    # رفع آخر التحديثات على GitHub
    print("\n📤 رفع التحديثات على GitHub...")
    run_command("git add .", "إضافة الملفات")
    run_command('git commit -m "Ready for Vercel deployment"', "حفظ التغييرات")
    run_command("git push origin main", "رفع على GitHub")
    
    # فتح رابط Vercel للنشر السريع
    print("\n🌐 فتح Vercel للنشر...")
    vercel_url = "https://vercel.com/new/clone?repository-url=https://github.com/elashrafy69/alaa-academy"
    webbrowser.open(vercel_url)
    
    print("\n" + "=" * 50)
    print("🎉 تم إعداد كل شيء للنشر!")
    print("\n📋 الخطوات التالية:")
    print("1. ✅ تم فتح Vercel في المتصفح")
    print("2. 🔑 سجل دخول بحساب GitHub")
    print("3. 🚀 اضغط 'Deploy' لبدء النشر")
    print("4. ⏱️ انتظر 2-3 دقائق للنشر")
    print("5. 🌍 ستحصل على رابط المشروع")
    
    print("\n🔧 متغيرات البيئة المطلوبة:")
    env_vars = {
        "DEBUG": "False",
        "SECRET_KEY": "django-production-secret-key-alaa-academy-2024-secure-key-change-this",
        "USE_POSTGRES": "True",
        "DATABASE_URL": "postgresql://postgres.srnyumtbsyxiqkvwkcpi:AlaaAcademy2024Production!@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        "ALLOWED_HOSTS": ".vercel.app",
        "SECURE_SSL_REDIRECT": "True",
        "SECURE_HSTS_SECONDS": "31536000",
        "SESSION_COOKIE_SECURE": "True",
        "CSRF_COOKIE_SECURE": "True"
    }
    
    for key, value in env_vars.items():
        print(f"   {key}={value}")
    
    print("\n🎯 بيانات تسجيل الدخول:")
    print("   📧 البريد: admin@alaa-academy.com")
    print("   🔐 كلمة المرور: 123456")
    
    print("\n🌟 المشروع جاهز للنشر!")

if __name__ == "__main__":
    main()
