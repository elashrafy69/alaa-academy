@echo off
echo 🚀 بدء رفع المشروع على GitHub...

REM إعداد Git
git config user.name "Mohamed El Ashrafy"
git config user.email "mohamedelashrafy241@gmail.com"

REM إضافة remote
git remote remove origin 2>nul
git remote add origin https://github.com/mohamedelashrafy241/alaa-academy.git

REM رفع المشروع
git branch -M main
git push -u origin main

echo ✅ تم رفع المشروع بنجاح!
echo 🌐 رابط المشروع: https://github.com/mohamedelashrafy241/alaa-academy
pause
