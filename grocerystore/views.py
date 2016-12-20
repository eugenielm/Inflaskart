from __future__ import unicode_literals
from django.shortcuts import redirect, render, get_object_or_404
from inflaskart_api import InflaskartClient
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from .forms import RegisterForm, LoginForm, ShopForm
from django.contrib.auth.models import User
import os
import urllib
from django.contrib import messages
from .models import Product
from django.views.decorators.csrf import csrf_protect
from django.utils.encoding import python_2_unicode_compatible
# from django.contrib.auth.decorators import login_required


CART_HOST = "http://127.0.0.1:5000/"

def get_inflauser(username):
    """Returns an instance of the InflaskartClient class whose username is the
    one passed in as a parameter"""
    username_encoded = urllib.quote(urllib.quote(username))
    infla_user_url = os.path.join(CART_HOST, username_encoded)
    infla_user = InflaskartClient(infla_user_url, username.decode('utf8'))
    return infla_user

def index(request):
    return render(request, 'grocerystore/index.html', {})


class UserRegisterView(View):
    form_class = RegisterForm
    template_name = 'grocerystore/registration_form.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            # returns User objects if credentials are correct
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, "You're now registered and logged in.")
                    return redirect('grocerystore:user_home', username=request.user.username)

        messages.error(request, "This username is already used, please choose another one.")
        return redirect('grocerystore:register')


class UserLoginForm(View):
    form_class = LoginForm
    template_name = 'grocerystore/login_form.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'There\'s no account with that username, please register.')
            return redirect('grocerystore:register')

        try:
            user = authenticate(username=username, password=password)
            if user.is_authenticated:
                if user.is_active:
                    login(request, user)
                    messages.success(request, "You are now logged in, %s." % username)
                    return redirect('grocerystore:user_home', username=request.user.username)
        except AttributeError:
            messages.error(request, 'You entered the wrong password.') #ne fonctionne pas
            return redirect('grocerystore:login')


class UserHomeView(View):
    form_class = ShopForm
    template_name = 'grocerystore/user_home.html'

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "You need to register to start shopping.")
            return redirect('grocerystore:register')

        if request.user.is_authenticated:
            add_form = self.form_class(None)
            return render(request, 'grocerystore/user_home.html', {'username': username, 'add_form': add_form,})
        else:
            messages.error(request, "You need to login to start shopping.")
            return redirect('grocerystore:index')

    def post(self, request, username):
        form = self.form_class(request.POST)
        product = request.POST['product_name']
        quantity = request.POST['quantity']
        infla_user = get_inflauser(username)
        infla_user.add(product, quantity)
        messages.success(request, "%s successfully added to your cart" % product)
        return redirect('grocerystore:user_home', username=username)


class ShowCartView(View):
    template_name = 'grocerystore/cart.html'

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "You need to register to start shopping.")
            return redirect('grocerystore:register')

        if request.user.is_authenticated:
            infla_user = get_inflauser(username)
            cart = infla_user.list()['items']
            if len(cart) == 0:
                context = {'empty_cart': "Your cart is empty, %s." % user.username}
            else:
                cart_msge = "Hi %s, you have the following items in your cart:" % user.username
                in_cart = []
                cart_total = 0
                for elt in cart:
                    product = Product.objects.get(product_name=elt["name"])
                    price = "%.2f" % (float(elt["qty"]) * float(product.product_price))
                    item = [elt["name"], int(elt["qty"]), product.product_unit, price]
                    in_cart.append(item)
                    cart_total += float(price)
                cart_total = "%.2f" % cart_total
                context = {'cart_msge': cart_msge, 'in_cart': in_cart, 'cart_total': cart_total, 'quantity_set': range(21),}
                return render(request, 'grocerystore/cart.html', context=context)

        else:
            messages.error(request, "You need to login before starting shopping.")
            return redirect('grocerystore:login')

    def post(self, request, username):
        user = get_object_or_404(User, username=username)
        if request.user.is_authenticated:
            infla_user = get_inflauser(username)
            cart = infla_user.list()['items'] # get a dictonnary whose keys are "name" and "qty"
            for item in cart:
                product_to_update = item["name"]
                try:
                    qty_to_change = int(request.POST.get(item["name"]))
                except TypeError:
                    continue
                if qty_to_change == 0:
                    infla_user.delete(product_to_update)
                    messages.success(request, "%s has been removed from your cart." % product_to_update)
                else:
                    infla_user.add(product_to_update, qty_to_change)
                    messages.success(request, "%s quantity has been updated." % product_to_update)
            return redirect('grocerystore:cart', username=username)

        else:
            return redirect('grocerystore:login_form')


@csrf_protect
def log_out(request, username):
    logout(request)
    messages.success(request, "You've been logged out, %s" % username)
    return redirect('grocerystore:index')
