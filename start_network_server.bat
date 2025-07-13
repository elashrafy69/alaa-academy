@echo off
echo 🌐 بدء تشغيل خادم أكاديمية علاء على الشبكة المحلية...
echo.
echo 📡 عنوان IP المحلي: 192.168.1.18
echo 🔗 الرابط المحلي: http://192.168.1.18:8000
echo 🏠 الرابط المحلي: http://localhost:8000
echo.
echo 🔑 بيانات تسجيل الدخول:
echo    📧 البريد: admin@alaa-academy.com
echo    🔐 كلمة المرور: 123456
echo.
echo ⚠️  تأكد من أن جهاز الكمبيوتر والأجهزة الأخرى على نفس الشبكة
echo.
echo 🚀 بدء الخادم...
echo.

REM تفعيل البيئة الافتراضية
call venv\Scripts\activate

REM تشغيل الخادم على جميع العناوين
python manage.py runserver 0.0.0.0:8000

echo.
echo ⏹️ تم إيقاف الخادم
pause
