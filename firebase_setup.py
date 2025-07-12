"""
إعداد Firebase للمشروع
"""

import os
import json
from pathlib import Path

def create_firebase_config():
    """إنشاء ملف تكوين Firebase"""
    
    config = {
        "type": "service_account",
        "project_id": "marketwise-academy-qhizq",
        "private_key_id": "your-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk-xxxxx@marketwise-academy-qhizq.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40marketwise-academy-qhizq.iam.gserviceaccount.com"
    }
    
    # حفظ ملف التكوين
    with open('firebase-service-account.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("⚠️ Please update firebase-service-account.json with your actual Firebase credentials")

def create_env_file():
    """إنشاء ملف متغيرات البيئة"""
    
    env_content = """# Firebase Service Account
GOOGLE_APPLICATION_CREDENTIALS=firebase-service-account.json

# Django Settings
DJANGO_SETTINGS_MODULE=alaa_academy.settings_production

# Database (Update with your Supabase credentials)
DATABASE_URL=postgresql://user:password@host:port/database

# Security
SECRET_KEY=your-very-secret-key-here

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file - please update with your actual values")

def setup_static_files():
    """إعداد الملفات الثابتة"""
    
    # إنشاء مجلد staticfiles إذا لم يكن موجوداً
    static_dir = Path('staticfiles')
    static_dir.mkdir(exist_ok=True)
    
    # إنشاء ملف index.html أساسي
    index_content = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>أكاديمية علاء عبد الحميد</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 600px;
            padding: 40px;
        }
        h1 {
            font-size: 3rem;
            margin-bottom: 20px;
        }
        p {
            font-size: 1.2rem;
            margin-bottom: 30px;
        }
        .btn {
            display: inline-block;
            padding: 15px 30px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
            margin: 10px;
        }
        .btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
        .loading {
            margin-top: 30px;
        }
        .spinner {
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top: 3px solid white;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 أكاديمية علاء عبد الحميد</h1>
        <p>منصة التعلم الإلكتروني المتقدمة</p>
        
        <div id="content">
            <div class="loading">
                <div class="spinner"></div>
                <p>جاري تحميل المنصة...</p>
            </div>
        </div>
        
        <script>
            // محاولة تحميل Django
            setTimeout(() => {
                fetch('/accounts/login/')
                    .then(response => {
                        if (response.ok) {
                            window.location.href = '/';
                        } else {
                            document.getElementById('content').innerHTML = `
                                <p>مرحباً بك في أكاديمية علاء عبد الحميد</p>
                                <a href="/accounts/login/" class="btn">تسجيل الدخول</a>
                                <a href="/accounts/register/" class="btn">إنشاء حساب</a>
                                <a href="/courses/" class="btn">تصفح الدورات</a>
                            `;
                        }
                    })
                    .catch(() => {
                        document.getElementById('content').innerHTML = `
                            <p>المنصة قيد الإعداد</p>
                            <p>سيتم تشغيلها قريباً...</p>
                        `;
                    });
            }, 2000);
        </script>
    </div>
</body>
</html>"""
    
    with open(static_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print("✅ Created static files")

def main():
    """الدالة الرئيسية للإعداد"""
    print("🔧 Setting up Firebase configuration...")
    
    create_firebase_config()
    create_env_file()
    setup_static_files()
    
    print("\n" + "="*50)
    print("✅ Firebase setup completed!")
    print("\n📋 Next steps:")
    print("1. Update firebase-service-account.json with your Firebase credentials")
    print("2. Update .env file with your database and email credentials")
    print("3. Run: python deploy.py")
    print("="*50)

if __name__ == '__main__':
    main()
