# 🚀 دليل النشر السريع - أكاديمية علاء عبد الحميد

## 📋 **خطوات النشر على Railway (5 دقائق):**

### 1. **رفع المشروع على GitHub:**

```bash
# في مجلد المشروع، نفذ هذه الأوامر:
git remote add origin https://github.com/mohamedelashrafy241/alaa-academy.git
git branch -M main
git push -u origin main
```

### 2. **إنشاء Repository على GitHub:**
- اذهب إلى: https://github.com/new
- **Repository name:** `alaa-academy`
- **Description:** `أكاديمية علاء عبد الحميد - منصة التعلم الإلكتروني المتقدمة`
- اختر **Public**
- **لا تختر** "Add a README file"
- اضغط **"Create repository"**

### 3. **النشر على Railway:**
- اذهب إلى: https://railway.app
- سجل دخول بحساب GitHub
- اضغط **"New Project"**
- اختر **"Deploy from GitHub repo"**
- اختر repository: `alaa-academy`
- Railway سيبدأ النشر تلقائياً!

### 4. **إضافة قاعدة البيانات:**
- في Railway dashboard
- اضغط **"+ New"**
- اختر **"Database"**
- اختر **"PostgreSQL"**
- انتظر حتى يتم الإنشاء

### 5. **ربط قاعدة البيانات:**
- اضغط على قاعدة البيانات
- انسخ **"DATABASE_URL"**
- اذهب لمشروع Django
- اضغط **"Variables"**
- أضف:
  ```
  DATABASE_URL=postgresql://...
  DEBUG=False
  ALLOWED_HOSTS=.railway.app
  SECRET_KEY=your-secret-key-here
  ```

## 🎯 **معلومات مهمة:**

### **بيانات تسجيل الدخول:**
- **المدير:** admin@marketwise-academy.com
- **كلمة المرور:** AdminPass123!

### **الملفات الجاهزة:**
- ✅ `railway.json` - إعدادات Railway
- ✅ `Procfile` - أوامر التشغيل
- ✅ `requirements.txt` - المكتبات المطلوبة
- ✅ `setup_production.py` - إعداد البيانات الأولية

## 🔧 **إذا واجهت مشاكل:**

### **خطأ في البناء:**
```bash
# في Railway، أضف هذه المتغيرات:
DISABLE_COLLECTSTATIC=1
PYTHONPATH=/app
```

### **خطأ في قاعدة البيانات:**
```bash
# تأكد من إضافة DATABASE_URL صحيح
# تأكد من تشغيل migrations
```

## 📞 **للمساعدة:**
إذا واجهت أي مشكلة، أرسل لي:
1. رابط المشروع على Railway
2. رسالة الخطأ (إن وجدت)
3. سأساعدك فوراً!

---
**المشروع جاهز للنشر! 🎉**
