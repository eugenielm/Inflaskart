from django import forms
from django.contrib.auth.models import User
from .models import Product, ProductCategory, ProductSubCategory, Dietary, Store, Address, Availability, Inflauser
from datetime import date, datetime
from calendar import monthrange

class RegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=25, required=True)
    password = forms.CharField(max_length=50, min_length=8, widget=forms.PasswordInput, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email']

class LoginForm(forms.ModelForm):
    password = forms.CharField(max_length=50, min_length=8, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']

class StoreForm(forms.Form):
    stores = forms.ModelChoiceField(label='Choose a store', queryset=Store.objects.all(), empty_label="--Choose below--")

class SelectCategory(forms.Form):
    category = forms.ModelChoiceField(label='Choose a category', queryset=ProductCategory.objects.all(), empty_label="--Choose below--")


class CheckoutForm(forms.Form):
    card_digits = forms.DecimalField(max_digits=16, decimal_places=0, required=True)
    exp_date = forms.DateField(required=True)
    secure_digits = forms.DecimalField(max_digits=3, decimal_places=0, required=True)

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


# Piste pour recherche de produits multi menus dans formulaire:
#     product_category = forms.ModelChoiceField(label='Choose a category', queryset=ProductCategory.objects.all(), empty_label="--Choose below--")
#     product_subcategory1 = forms.ModelChoiceField(label='Choose a sub-category', queryset=ProductSubCategory.objects.none(), empty_label="--Choose below--")
#     product_subcategory2 = forms.ModelChoiceField(label='Choose a sub-sub-category', queryset=ProductSubSubCategory.objects.none(), empty_label="--Choose below--")
#     final_choice = forms.ModelChoiceField(label='Choose an item', queryset=Product.objects.none(), empty_label="--Choose below--")
#     quantity = forms.IntegerField(min_value=1, max_value=20, required=True)
#
#     def __init__(self, *args, **kwargs):
#         super(ShopForm, self).__init__(self, *args, **kwargs)
#         product_category = forms.ModelChoiceField(label='Choose a category', queryset=ProductCategory.objects.all(), empty_label="--Choose below--")
#         if product_category:
#             self.fields['product_subcategory1'] = forms.ModelChoiceField(label='Choose a sub-category', queryset=ProductSubCategory.objects.filter(top_category__top_category=product_category.top_category), empty_label="--Choose below--")
#         if product_subcategory1:
#             self.fields['product_subcategory2'] = forms.ModelChoiceField(label='Choose a sub-sub-category', queryset=ProductSubSubCategory.objects.filter(sub_category_1=product_subcategory1), empty_label="--Choose below--")
#         if product_subcategory2:
#             self.fields['final_choice'] = forms.ModelChoiceField(label='Choose an item', queryset=Product.objects.filter(product_category=product_subcategory2), empty_label="--Choose below--")
