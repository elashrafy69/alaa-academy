#!/usr/bin/env python
"""
سكريبت نشر المشروع على Firebase
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """تشغيل أمر في الطرفية"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            cwd=cwd,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def setup_environment():
    """إعداد البيئة للنشر"""
    print("🔧 Setting up environment...")
    
    # تعيين متغير البيئة لإعدادات الإنتاج
    os.environ['DJANGO_SETTINGS_MODULE'] = 'alaa_academy.settings_production'
    
    # إنشاء مجلدات مطلوبة
    os.makedirs('staticfiles', exist_ok=True)
    os.makedirs('media', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    print("✅ Environment setup complete")

def collect_static_files():
    """جمع الملفات الثابتة"""
    print("📦 Collecting static files...")
    
    # تشغيل collectstatic
    if not run_command('python manage.py collectstatic --noinput'):
        print("❌ Failed to collect static files")
        return False
    
    print("✅ Static files collected")
    return True

def run_migrations():
    """تشغيل migrations"""
    print("🗄️ Running database migrations...")
    
    if not run_command('python manage.py migrate'):
        print("❌ Failed to run migrations")
        return False
    
    print("✅ Migrations completed")
    return True

def create_superuser():
    """إنشاء مستخدم مدير"""
    print("👤 Creating superuser...")
    
    # التحقق من وجود مستخدم مدير
    check_command = '''
    python manage.py shell -c "
    from django.contrib.auth import get_user_model;
    User = get_user_model();
    exists = User.objects.filter(is_superuser=True).exists();
    print('EXISTS' if exists else 'NOT_EXISTS')
    "
    '''
    
    result = subprocess.run(check_command, shell=True, capture_output=True, text=True)
    
    if 'NOT_EXISTS' in result.stdout:
        # إنشاء مستخدم مدير
        create_command = '''
        python manage.py shell -c "
        from django.contrib.auth import get_user_model;
        User = get_user_model();
        User.objects.create_superuser(
            email='admin@marketwise-academy.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
            user_type='admin'
        );
        print('Superuser created')
        "
        '''
        
        if not run_command(create_command):
            print("❌ Failed to create superuser")
            return False
        
        print("✅ Superuser created")
    else:
        print("✅ Superuser already exists")
    
    return True

def copy_project_files():
    """نسخ ملفات المشروع إلى مجلد functions"""
    print("📁 Copying project files...")
    
    # قائمة المجلدات والملفات المطلوبة
    items_to_copy = [
        'alaa_academy',
        'accounts',
        'courses',
        'analytics',
        'notifications',
        'search',
        'security',
        'templates',
        'static',
        'manage.py',
        '.env.production'
    ]
    
    functions_dir = Path('functions')
    
    for item in items_to_copy:
        src = Path(item)
        if src.exists():
            dst = functions_dir / item
            
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            
            print(f"✅ Copied {item}")
        else:
            print(f"⚠️ {item} not found, skipping")
    
    print("✅ Project files copied")

def install_firebase_cli():
    """تثبيت Firebase CLI"""
    print("🔥 Installing Firebase CLI...")
    
    # التحقق من وجود Firebase CLI
    result = subprocess.run('firebase --version', shell=True, capture_output=True)
    
    if result.returncode == 0:
        print("✅ Firebase CLI already installed")
        return True
    
    # تثبيت Firebase CLI
    if not run_command('npm install -g firebase-tools'):
        print("❌ Failed to install Firebase CLI")
        print("Please install Firebase CLI manually: npm install -g firebase-tools")
        return False
    
    print("✅ Firebase CLI installed")
    return True

def firebase_login():
    """تسجيل الدخول إلى Firebase"""
    print("🔐 Firebase login...")
    
    # التحقق من حالة تسجيل الدخول
    result = subprocess.run('firebase projects:list', shell=True, capture_output=True)
    
    if result.returncode == 0:
        print("✅ Already logged in to Firebase")
        return True
    
    print("Please login to Firebase manually:")
    print("Run: firebase login")
    
    return input("Are you logged in? (y/n): ").lower() == 'y'

def deploy_to_firebase():
    """نشر المشروع على Firebase"""
    print("🚀 Deploying to Firebase...")
    
    if not run_command('firebase deploy'):
        print("❌ Failed to deploy to Firebase")
        return False
    
    print("✅ Deployed to Firebase successfully!")
    return True

def test_deployment():
    """اختبار النشر"""
    print("🧪 Testing deployment...")
    
    import requests
    
    try:
        # اختبار الصفحة الرئيسية
        response = requests.get('https://marketwise-academy-qhizq.web.app/', timeout=30)
        
        if response.status_code == 200:
            print("✅ Homepage is accessible")
        else:
            print(f"⚠️ Homepage returned status code: {response.status_code}")
        
        # اختبار صفحة تسجيل الدخول
        response = requests.get('https://marketwise-academy-qhizq.web.app/accounts/login/', timeout=30)
        
        if response.status_code == 200:
            print("✅ Login page is accessible")
        else:
            print(f"⚠️ Login page returned status code: {response.status_code}")
        
        print("✅ Basic tests passed")
        return True
        
    except requests.RequestException as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """الدالة الرئيسية للنشر"""
    print("🚀 Starting deployment process...")
    print("=" * 50)
    
    # التحقق من Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    # خطوات النشر
    steps = [
        ("Setup Environment", setup_environment),
        ("Collect Static Files", collect_static_files),
        ("Run Migrations", run_migrations),
        ("Create Superuser", create_superuser),
        ("Copy Project Files", copy_project_files),
        ("Install Firebase CLI", install_firebase_cli),
        ("Firebase Login", firebase_login),
        ("Deploy to Firebase", deploy_to_firebase),
        ("Test Deployment", test_deployment),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        print("-" * 30)
        
        if not step_func():
            print(f"❌ Failed at step: {step_name}")
            return False
        
        print(f"✅ Completed: {step_name}")
    
    print("\n" + "=" * 50)
    print("🎉 Deployment completed successfully!")
    print("🌐 Your site is live at: https://marketwise-academy-qhizq.web.app/")
    print("👤 Admin login: admin@marketwise-academy.com / AdminPass123!")
    print("=" * 50)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
