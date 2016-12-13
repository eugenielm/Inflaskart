from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=25, required=True)
    password = forms.CharField(max_length=50, min_length=8, widget=forms.PasswordInput, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class LoginForm(forms.ModelForm):
    password = forms.CharField(max_length=50, min_length=8, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']

class ShopForm(forms.Form):
    product = forms.CharField(max_length=20, required=True)
    quantity = forms.IntegerField(min_value=1, max_value=20, required=True)
