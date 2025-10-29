from django import forms
from django.contrib.auth.forms import UserCreationForm
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from userauths.models import User, SECURITY_QUESTIONS

USER_TYPE = (
    ('Customer', 'Customer'),
    ('Vendor', 'Vendor'),
)

class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'form-control rounded'}),
        max_length=150, required=True
    )
    mobile = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Mobile Number', 'class': 'form-control rounded'}),
        max_length=15, required=True
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control rounded'}),
        max_length=254, required=True, help_text='Required. Enter a valid email address.'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control rounded'}),
        label='Password', required=True
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control rounded'}),
        label='Confirm Password', required=True
    )
    user_type = forms.ChoiceField(
        choices=USER_TYPE, widget=forms.Select(attrs={'class': 'form-control rounded'}),
        required=True, help_text='Select your user type.'
    )
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type':'date', 'class':'form-control rounded'}),
        required=True, label='Birth Date'
    )
    cnic = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'CNIC', 'class': 'form-control rounded'}),
        required=True, label='CNIC'
    )
    security_question = forms.ChoiceField(
        choices=SECURITY_QUESTIONS,
        widget=forms.Select(attrs={'class':'form-control rounded'}),
        required=True, label='Security Question'
    )
    security_answer = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Answer', 'class':'form-control rounded'}),
        required=True, label='Answer'
    )
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox, label='')

    class Meta:
        model = User
        fields = [
            'full_name', 'mobile', 'email', 'password1', 'password2', 
            'user_type', 'birth_date', 'cnic', 'security_question', 'security_answer', 'captcha'
        ]

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control rounded'}), max_length=254, required=True)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control rounded'}), label='Password', required=True)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox, label='')

    class Meta:
        model = User
        fields = ['email', 'password', 'captcha']