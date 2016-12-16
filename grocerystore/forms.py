from django import forms
from django.contrib.auth.models import User
from .models import Product

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

CHOICES = []
for product in Product.objects.order_by('product_name'):
    CHOICES.append((product.product_name, product.product_name + " ($" + str(product.product_price) + " / " + product.product_unit + ")"),)

class ShopForm(forms.Form):
    product_name = forms.ChoiceField(label='Choose an item', choices=CHOICES)
    quantity = forms.IntegerField(min_value=1, max_value=30, required=True)
