from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import Course, Category, CourseContent, Review, Enrollment

User = get_user_model()


class CourseForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الدورات"""
    
    class Meta:
        model = Course
        fields = [
            'title', 'slug', 'category', 'description', 'short_description',
            'thumbnail', 'difficulty_level', 'status', 'price', 'estimated_duration',
            'prerequisites', 'learning_objectives', 'is_featured', 'enrollment_limit'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الدورة'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الرابط المختصر'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'وصف مفصل للدورة'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'وصف مختصر'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'estimated_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'prerequisites': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'learning_objectives': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enrollment_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # إضافة JavaScript لتوليد slug تلقائياً
        self.fields['slug'].widget.attrs.update({
            'data-slug-source': 'id_title'
        })
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if Course.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('هذا الرابط المختصر مستخدم بالفعل.'))
        return slug
    
    def save(self, commit=True):
        course = super().save(commit=False)
        if self.user and not course.instructor_id:
            course.instructor = self.user
        if commit:
            course.save()
        return course


class CourseContentForm(forms.ModelForm):
    """نموذج إضافة وتعديل محتوى الدورة"""
    
    class Meta:
        model = CourseContent
        fields = [
            'title', 'description', 'content_type', 'file_url', 'file_upload',
            'duration', 'order_sequence', 'is_free', 'is_published'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان المحتوى'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content_type': forms.Select(attrs={'class': 'form-control'}),
            'file_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'رابط الملف (اختياري)'}),
            'file_upload': forms.FileInput(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'المدة بالدقائق'}),
            'order_sequence': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        # تعيين الترتيب التلقائي
        if self.course and not self.instance.pk:
            next_order = self.course.content.count() + 1
            self.fields['order_sequence'].initial = next_order
    
    def clean(self):
        cleaned_data = super().clean()
        file_url = cleaned_data.get('file_url')
        file_upload = cleaned_data.get('file_upload')
        
        if not file_url and not file_upload:
            raise forms.ValidationError(_('يجب إدخال رابط الملف أو رفع ملف.'))
        
        return cleaned_data
    
    def clean_order_sequence(self):
        order = self.cleaned_data.get('order_sequence')
        if self.course:
            existing = self.course.content.filter(order_sequence=order)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(_('هذا الترتيب مستخدم بالفعل.'))
        return order


class CategoryForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الفئات"""
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fas fa-book'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EnrollmentForm(forms.ModelForm):
    """نموذج تسجيل الطلاب في الدورات"""
    
    student_email = forms.EmailField(
        label=_('البريد الإلكتروني للطالب'),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Enrollment
        fields = ['course']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.filter(status='published')
    
    def clean_student_email(self):
        email = self.cleaned_data.get('student_email')
        try:
            student = User.objects.get(email=email, user_type='student')
            return student
        except User.DoesNotExist:
            raise forms.ValidationError(_('لا يوجد طالب بهذا البريد الإلكتروني.'))
    
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student_email')
        course = cleaned_data.get('course')
        
        if student and course:
            if Enrollment.objects.filter(student=student, course=course).exists():
                raise forms.ValidationError(_('الطالب مسجل في هذه الدورة بالفعل.'))
        
        return cleaned_data
    
    def save(self, commit=True):
        enrollment = super().save(commit=False)
        enrollment.student = self.cleaned_data['student_email']
        if commit:
            enrollment.save()
        return enrollment


class BulkEnrollmentForm(forms.Form):
    """نموذج التسجيل المجمع للطلاب"""
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(status='published'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('الدورة')
    )
    
    students_emails = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'أدخل البريد الإلكتروني لكل طالب في سطر منفصل'
        }),
        label=_('البريد الإلكتروني للطلاب')
    )
    
    def clean_students_emails(self):
        emails_text = self.cleaned_data.get('students_emails')
        emails = [email.strip() for email in emails_text.split('\n') if email.strip()]
        
        if not emails:
            raise forms.ValidationError(_('يجب إدخال بريد إلكتروني واحد على الأقل.'))
        
        valid_students = []
        invalid_emails = []
        
        for email in emails:
            try:
                student = User.objects.get(email=email, user_type='student')
                valid_students.append(student)
            except User.DoesNotExist:
                invalid_emails.append(email)
        
        if invalid_emails:
            raise forms.ValidationError(
                _('البريد الإلكتروني التالي غير صحيح: {}').format(', '.join(invalid_emails))
            )
        
        return valid_students
    
    def save(self):
        course = self.cleaned_data['course']
        students = self.cleaned_data['students_emails']
        
        enrollments = []
        for student in students:
            enrollment, created = Enrollment.objects.get_or_create(
                student=student,
                course=course
            )
            if created:
                enrollments.append(enrollment)
        
        return enrollments


class ReviewForm(forms.ModelForm):
    """نموذج تقييم الدورات"""
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} نجوم') for i in range(1, 6)],
                attrs={'class': 'form-control'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'شاركنا رأيك في الدورة...'
            }),
        }
