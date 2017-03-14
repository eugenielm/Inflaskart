#-*- coding: UTF-8 -*-
from datetime import date, datetime
from calendar import monthrange
from django import forms
from django.contrib.auth.models import User
from .models import Product, ProductCategory, ProductSubCategory, Dietary, \
                    Store, Address, Availability, Inflauser, State, Zipcode

class UserForm(forms.ModelForm):
    password = forms.CharField(max_length=50, min_length=8, widget=forms.PasswordInput)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

class AddressForm(forms.ModelForm):
    zip_code = forms.RegexField(max_length=5, min_length=4, regex=r'^[0-9]{4,5}$', error_messages={'invalid': "Please enter a valid ZIP code.", 'required': "Please fill in this field."})

    class Meta:
        model = Address
        fields = '__all__'

class LoginForm(forms.ModelForm):
    password = forms.CharField(max_length=50, min_length=8, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']

class SelectCategory(forms.Form):
    """Displays a drop down menu with all the product categories available
    in a given store"""
    category = forms.ModelChoiceField(label='Choose a category',
                                      queryset=ProductCategory.objects.all(),
                                      empty_label="--Choose below--",
                                      widget=forms.Select(attrs={'onChange':'submit();'}))

class CheckoutForm(forms.Form):
    card_digits = forms.RegexField(regex=r'^[1-9][0-9]{12,15}$') # the number of digits limitation doesn't work
    exp_date = forms.DateField(required=True)
    secure_digits = forms.DecimalField(max_digits=3, decimal_places=0)

class CreditCardField(forms.IntegerField):
    """ copied and pasted from http://codekarate.com/blog/django-credit-card-payment-form"""
    def get_cc_type(self, number):
        """
        Gets credit card type given number. Based on values from Wikipedia page
        "Credit card number".
        http://en.wikipedia.org/w/index.php?title=Credit_card_number"""
        number = str(number)
        #group checking by ascending length of number
        if len(number) == 13:
            if number[0] == "4":
                return "Visa"
        elif len(number) == 14:
            if number[:2] == "36":
                return "MasterCard"
        elif len(number) == 15:
            if number[:2] in ("34", "37"):
                return "American Express"
        elif len(number) == 16:
            if number[:4] == "6011":
                return "Discover"
            if number[:2] in ("51", "52", "53", "54", "55"):
                return "MasterCard"
            if number[0] == "4":
                return "Visa"
        return "Unknown"

    def clean(self, value):
        """Check if given CC number is valid and one of the
        card types we accept"""
        if value and (len(value) < 13 or len(value) > 16):
            raise forms.ValidationError("Please enter in a valid credit card number.")
        elif self.get_cc_type(value) not in ("Visa", "MasterCard", "American Express", "Discover"):
            raise forms.ValidationError("Please enter in a Visa, Master Card"+\
                  "Discover, or American Express credit card number.")
        return super(CreditCardField, self).clean(value)

class PaymentForm(forms.Form):
    number = CreditCardField(required = True, label = "Card Number")
    first_name = forms.CharField(required=True, label="Card Holder First Name", max_length=30)
    last_name = forms.CharField(required=True, label="Card Holder Last Name", max_length=30)
    expire_month = forms.ChoiceField(required=True, choices=[(x, x) for x in xrange(1, 13)])
    expire_year = forms.ChoiceField(required=True, choices=[(x, x) for x in xrange(date.today().year, date.today().year + 15)])
    cvv_number = forms.IntegerField(required = True, label = "CVV Number", max_value = 9999,
                                    widget = forms.TextInput(attrs={'size': '4'}))

    def __init__(self, *args, **kwargs):
        self.payment_data = kwargs.pop('payment_data', None)
        super(PaymentForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(PaymentForm, self).clean()
        expire_month = cleaned_data.get('expire_month')
        expire_year = cleaned_data.get('expire_year')

        if expire_year in forms.fields.EMPTY_VALUES:
            #raise forms.ValidationError("You must select a valid Expiration year.")
            self._errors["expire_year"] = self.error_class(["You must select a valid Expiration year."])
            del cleaned_data["expire_year"]
        if expire_month in forms.fields.EMPTY_VALUES:
            #raise forms.ValidationError("You must select a valid Expiration month.")
            self._errors["expire_month"] = self.error_class(["You must select a valid Expiration month."])
            del cleaned_data["expire_month"]

        year = int(expire_year)
        month = int(expire_month)
        # find last day of the month
        day = monthrange(year, month)[1]
        expire = date(year, month, day)

        if date.today() > expire:
            #raise forms.ValidationError("The expiration date you entered is in the past.")
            self._errors["expire_year"] = self.error_class(["The expiration date you entered is in the past."])

        return cleaned_data
