#!/usr/bin/env python
"""
بناء الملفات الثابتة للمشروع
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def setup_django():
    """إعداد Django"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alaa_academy.settings_production')
    
    import django
    django.setup()

def collect_static():
    """جمع الملفات الثابتة"""
    print("📦 Collecting static files...")
    
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--clear'])
        print("✅ Static files collected successfully")
        return True
    except Exception as e:
        print(f"❌ Error collecting static files: {e}")
        return False

def create_index_html():
    """إنشاء ملف index.html للصفحة الرئيسية"""
    
    index_content = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>أكاديمية علاء عبد الحميد - منصة التعلم الإلكتروني</title>
    <meta name="description" content="منصة تعليمية متقدمة تقدم دورات عالية الجودة في مختلف المجالات">
    <meta name="keywords" content="تعلم, دورات, أكاديمية, تعليم إلكتروني">
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet">
    
    <style>
        body {
            font-family: 'Cairo', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 0;
        }
        
        .hero-section {
            min-height: 100vh;
            display: flex;
            align-items: center;
            color: white;
            text-align: center;
        }
        
        .hero-content {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 60px 40px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        
        .hero-title {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .hero-subtitle {
            font-size: 1.3rem;
            margin-bottom: 40px;
            opacity: 0.9;
        }
        
        .btn-custom {
            padding: 15px 30px;
            font-size: 1.1rem;
            border-radius: 50px;
            margin: 10px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary-custom {
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.3);
            color: white;
        }
        
        .btn-primary-custom:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            color: white;
        }
        
        .btn-outline-custom {
            background: transparent;
            border: 2px solid white;
            color: white;
        }
        
        .btn-outline-custom:hover {
            background: white;
            color: #667eea;
            transform: translateY(-3px);
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-top: 50px;
        }
        
        .feature-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 20px;
            opacity: 0.8;
        }
        
        .loading-spinner {
            display: none;
            margin: 20px auto;
        }
        
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.3);
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
        
        .status-message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            display: none;
        }
        
        .status-success {
            background: rgba(40, 167, 69, 0.2);
            border: 1px solid rgba(40, 167, 69, 0.3);
        }
        
        .status-error {
            background: rgba(220, 53, 69, 0.2);
            border: 1px solid rgba(220, 53, 69, 0.3);
        }
        
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2.5rem;
            }
            
            .hero-content {
                padding: 40px 20px;
            }
            
            .btn-custom {
                display: block;
                margin: 10px auto;
                max-width: 250px;
            }
        }
    </style>
</head>
<body>
    <div class="hero-section">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="hero-content">
                        <h1 class="hero-title">
                            <i class="fas fa-graduation-cap me-3"></i>
                            أكاديمية علاء عبد الحميد
                        </h1>
                        <p class="hero-subtitle">
                            منصة التعلم الإلكتروني المتقدمة - تعلم مهارات جديدة واحصل على شهادات معتمدة
                        </p>
                        
                        <div id="main-buttons">
                            <a href="#" class="btn-custom btn-primary-custom" onclick="checkDjangoApp('/accounts/login/')">
                                <i class="fas fa-sign-in-alt me-2"></i>
                                تسجيل الدخول
                            </a>
                            <a href="#" class="btn-custom btn-outline-custom" onclick="checkDjangoApp('/accounts/register/')">
                                <i class="fas fa-user-plus me-2"></i>
                                إنشاء حساب جديد
                            </a>
                            <a href="#" class="btn-custom btn-primary-custom" onclick="checkDjangoApp('/courses/')">
                                <i class="fas fa-book me-2"></i>
                                تصفح الدورات
                            </a>
                        </div>
                        
                        <div class="loading-spinner" id="loadingSpinner">
                            <div class="spinner"></div>
                            <p>جاري تحميل المنصة...</p>
                        </div>
                        
                        <div class="status-message" id="statusMessage"></div>
                        
                        <div class="features">
                            <div class="feature-card">
                                <div class="feature-icon">
                                    <i class="fas fa-video"></i>
                                </div>
                                <h5>دورات فيديو تفاعلية</h5>
                                <p>محتوى عالي الجودة مع إمكانية التفاعل والمتابعة</p>
                            </div>
                            
                            <div class="feature-card">
                                <div class="feature-icon">
                                    <i class="fas fa-certificate"></i>
                                </div>
                                <h5>شهادات معتمدة</h5>
                                <p>احصل على شهادات إتمام معتمدة عند إنهاء الدورات</p>
                            </div>
                            
                            <div class="feature-card">
                                <div class="feature-icon">
                                    <i class="fas fa-users"></i>
                                </div>
                                <h5>مجتمع تعليمي</h5>
                                <p>تفاعل مع المدربين والطلاب الآخرين</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        function showLoading() {
            document.getElementById('loadingSpinner').style.display = 'block';
            document.getElementById('statusMessage').style.display = 'none';
        }
        
        function hideLoading() {
            document.getElementById('loadingSpinner').style.display = 'none';
        }
        
        function showStatus(message, isError = false) {
            const statusEl = document.getElementById('statusMessage');
            statusEl.textContent = message;
            statusEl.className = 'status-message ' + (isError ? 'status-error' : 'status-success');
            statusEl.style.display = 'block';
        }
        
        function checkDjangoApp(url) {
            showLoading();
            
            fetch(url)
                .then(response => {
                    hideLoading();
                    if (response.ok) {
                        showStatus('تم تحميل المنصة بنجاح! جاري التوجيه...');
                        setTimeout(() => {
                            window.location.href = url;
                        }, 1000);
                    } else {
                        showStatus('المنصة قيد الإعداد، يرجى المحاولة لاحقاً', true);
                    }
                })
                .catch(error => {
                    hideLoading();
                    showStatus('المنصة قيد الإعداد، يرجى المحاولة لاحقاً', true);
                    console.error('Error:', error);
                });
        }
        
        // فحص تلقائي للمنصة عند تحميل الصفحة
        window.addEventListener('load', function() {
            setTimeout(() => {
                fetch('/')
                    .then(response => {
                        if (response.ok && response.url !== window.location.href) {
                            // إذا كان Django يعمل وتم إعادة التوجيه
                            window.location.href = '/';
                        }
                    })
                    .catch(() => {
                        // Django غير متاح حالياً
                        console.log('Django app not ready yet');
                    });
            }, 2000);
        });
    </script>
</body>
</html>"""
    
    # حفظ الملف في مجلد staticfiles
    staticfiles_dir = Path('staticfiles')
    staticfiles_dir.mkdir(exist_ok=True)
    
    with open(staticfiles_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print("✅ Created index.html")

def optimize_static_files():
    """تحسين الملفات الثابتة"""
    print("🔧 Optimizing static files...")
    
    staticfiles_dir = Path('staticfiles')
    
    # إنشاء ملف robots.txt
    robots_content = """User-agent: *
Allow: /

Sitemap: https://marketwise-academy-qhizq.web.app/sitemap.xml
"""
    
    with open(staticfiles_dir / 'robots.txt', 'w') as f:
        f.write(robots_content)
    
    # إنشاء ملف manifest.json
    manifest_content = """{
    "name": "أكاديمية علاء عبد الحميد",
    "short_name": "أكاديمية علاء",
    "description": "منصة التعلم الإلكتروني المتقدمة",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#667eea",
    "theme_color": "#667eea",
    "icons": [
        {
            "src": "/static/images/icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/static/images/icon-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}"""
    
    with open(staticfiles_dir / 'manifest.json', 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    
    print("✅ Static files optimized")

def main():
    """الدالة الرئيسية"""
    print("🏗️ Building static files...")
    print("=" * 40)
    
    # إعداد Django
    setup_django()
    
    # جمع الملفات الثابتة
    if not collect_static():
        return False
    
    # إنشاء ملف index.html
    create_index_html()
    
    # تحسين الملفات الثابتة
    optimize_static_files()
    
    print("=" * 40)
    print("✅ Static files built successfully!")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
