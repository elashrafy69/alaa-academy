# 🎓 أكاديمية علاء عبد الحميد

منصة التعلم الإلكتروني المتقدمة - تعلم مهارات جديدة واحصل على شهادات معتمدة

## ✨ المميزات

- 🎯 **نظام إدارة المستخدمين المتقدم** - طلاب، مدربين، ومدراء
- 📚 **إدارة الدورات الشاملة** - إنشاء وإدارة الدورات والمحتوى
- 🎥 **دعم المحتوى المتعدد** - فيديو، صوت، نصوص، وملفات
- 📊 **نظام التقييم والمتابعة** - تتبع تقدم الطلاب والإحصائيات
- 🏆 **شهادات إتمام معتمدة** - شهادات PDF قابلة للتحقق
- 💳 **نظام الدفع المتكامل** - دعم طرق دفع متعددة
- 📱 **تصميم متجاوب** - يعمل على جميع الأجهزة
- 🔒 **أمان متقدم** - حماية البيانات والمحتوى

## 🚀 التقنيات المستخدمة

- **Backend**: Django 5.2.1 + Python 3.11
- **Frontend**: Bootstrap 5 + JavaScript
- **Database**: PostgreSQL (Supabase)
- **Storage**: Firebase Storage
- **Hosting**: Railway
- **Authentication**: Django Auth + Custom User Model

## 📦 التثبيت والتشغيل

### 1. استنساخ المشروع
```bash
git clone https://github.com/your-username/alaa-academy.git
cd alaa-academy
```

### 2. إنشاء البيئة الافتراضية
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows
```

### 3. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 4. إعداد متغيرات البيئة
```bash
cp .env.example .env
# قم بتحديث المتغيرات في ملف .env
```

### 5. تشغيل المشروع
```bash
python manage.py migrate
python manage.py collectstatic
python setup_production.py
python manage.py runserver
```

## 🔧 الإعداد للإنتاج

### متغيرات البيئة المطلوبة:
```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:port/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

## 👤 معلومات تسجيل الدخول الافتراضية

**المدير:**
- البريد الإلكتروني: `admin@marketwise-academy.com`
- كلمة المرور: `AdminPass123!`

## 📚 الوثائق

### نماذج البيانات الرئيسية:

#### User (المستخدم)
- أنواع المستخدمين: admin, instructor, student
- معلومات شخصية كاملة
- نظام صلاحيات متقدم

#### Course (الدورة)
- معلومات الدورة الأساسية
- مستويات الصعوبة
- نظام التسعير
- حالات النشر

#### CourseContent (محتوى الدورة)
- أنواع محتوى متعددة
- ترتيب المحتوى
- تتبع التقدم

#### Enrollment (التسجيل)
- تسجيل الطلاب في الدورات
- تتبع التقدم
- نظام الإكمال

## 🛠️ المساهمة

1. Fork المشروع
2. إنشاء branch جديد (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push إلى Branch (`git push origin feature/amazing-feature`)
5. فتح Pull Request

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

## 📞 التواصل

- **الموقع**: [https://marketwise-academy.com](https://marketwise-academy.com)
- **البريد الإلكتروني**: admin@marketwise-academy.com

## 🙏 شكر خاص

شكر خاص لجميع المساهمين في تطوير هذه المنصة التعليمية المتقدمة.

---

**أكاديمية علاء عبد الحميد** - منصة التعلم الإلكتروني المتقدمة 🎓
