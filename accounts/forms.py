from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import RegistrationCode

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """نموذج إنشاء مستخدم مخصص"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'البريد الإلكتروني'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'الاسم الأول'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم العائلة'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رقم الهاتف (اختياري)'
        })
    )
    
    registration_code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'كود التسجيل (اختياري)'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'registration_code', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تخصيص widgets
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'اسم المستخدم'
        })
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'كلمة المرور'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'تأكيد كلمة المرور'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('هذا البريد الإلكتروني مستخدم بالفعل.'))
        return email
    
    def clean_registration_code(self):
        code = self.cleaned_data.get('registration_code')
        if code:
            try:
                reg_code = RegistrationCode.objects.get(code=code)
                if not reg_code.is_available:
                    raise forms.ValidationError(_('كود التسجيل غير صالح أو منتهي الصلاحية.'))
                return code
            except RegistrationCode.DoesNotExist:
                raise forms.ValidationError(_('كود التسجيل غير موجود.'))
        return code
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number')
        user.registration_code = self.cleaned_data.get('registration_code')
        user.user_type = 'student'  # افتراضياً طالب
        
        if commit:
            user.save()
            
            # استخدام كود التسجيل إذا كان موجود
            if user.registration_code:
                try:
                    reg_code = RegistrationCode.objects.get(code=user.registration_code)
                    reg_code.use_code()
                    
                    # تسجيل الطالب في الدورة إذا كان الكود مرتبط بدورة
                    if reg_code.course:
                        from courses.models import Enrollment
                        Enrollment.objects.get_or_create(
                            student=user,
                            course=reg_code.course,
                            defaults={'registration_code_used': reg_code}
                        )
                except RegistrationCode.DoesNotExist:
                    pass
        
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """نموذج تسجيل دخول مخصص"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'اسم المستخدم أو البريد الإلكتروني'
        })
        
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'كلمة المرور'
        })


class UserProfileForm(forms.ModelForm):
    """نموذج تحديث الملف الشخصي"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'profile_picture', 'bio', 'date_of_birth'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('هذا البريد الإلكتروني مستخدم بالفعل.'))
        return email


class RegistrationCodeForm(forms.ModelForm):
    """نموذج إنشاء كود تسجيل"""
    
    class Meta:
        model = RegistrationCode
        fields = ['code', 'course', 'max_uses', 'expiry_date', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إنشاء كود عشوائي إذا لم يكن موجود
        if not self.instance.pk and not self.initial.get('code'):
            import random
            import string
            self.initial['code'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class StudentEditForm(forms.ModelForm):
    """نموذج تعديل بيانات الطالب للمدير"""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'bio', 'is_active'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الأول'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الأخير'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'البريد الإلكتروني'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'نبذة شخصية'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'email': 'البريد الإلكتروني',
            'phone_number': 'رقم الهاتف',
            'date_of_birth': 'تاريخ الميلاد',
            'bio': 'نبذة شخصية',
            'is_active': 'حساب نشط'
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # التحقق من عدم وجود بريد إلكتروني مكرر
            existing_user = User.objects.filter(email=email).exclude(pk=self.instance.pk)
            if existing_user.exists():
                raise forms.ValidationError('هذا البريد الإلكتروني مستخدم بالفعل')
        return email


class StudentSearchForm(forms.Form):
    """نموذج البحث في الطلاب"""

    search = forms.CharField(
        label='البحث',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'البحث بالاسم، البريد الإلكتروني، أو الهاتف...'
        })
    )

    status = forms.ChoiceField(
        label='الحالة',
        choices=[
            ('', 'جميع الحالات'),
            ('active', 'نشط'),
            ('inactive', 'غير نشط'),
            ('enrolled', 'مسجل في دورات')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    date_filter = forms.ChoiceField(
        label='تاريخ التسجيل',
        choices=[
            ('', 'جميع التواريخ'),
            ('today', 'اليوم'),
            ('week', 'آخر أسبوع'),
            ('month', 'آخر شهر')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
