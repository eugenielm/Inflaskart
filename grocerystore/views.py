from __future__ import unicode_literals
import re
from django.shortcuts import redirect, render, get_object_or_404
from inflaskart_api import InflaskartClient
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from .forms import RegisterForm, LoginForm, ShopForm, PaymentForm
from django.contrib.auth.models import User
import os
import urllib
from django.contrib import messages
from .models import Product
from django.views.decorators.csrf import csrf_protect
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sessions.models import Session
# from django.contrib.auth.decorators import login_required


CART_HOST = "http://127.0.0.1:5000/"

def get_flaskuser(username):
    """Returns an instance of the InflaskartClient class whose username is the
    one passed in as a parameter"""
    username_encoded = urllib.quote(urllib.quote(username))
    flask_user_url = os.path.join(CART_HOST, username_encoded)
    flask_user = InflaskartClient(flask_user_url, username.decode('utf8'))
    return flask_user

class IndexView(View):
    form_class = ShopForm
    template_name = 'grocerystore/index.html'

    def get(self, request):
        shop_form = self.form_class(None)
        return render(self.request, 'grocerystore/index.html', {'shop_form': shop_form,})

    def post(self, request):
        form = self.form_class(self.request.POST)
        try:#if the user chooses an item from the multiple choice menu
            product_pk = self.request.POST['product_name']
            product_to_add = Product.objects.get(pk=product_pk).product_name
            quantity_to_add = self.request.POST['quantity']
            if self.request.user.is_authenticated:
                if self.request.user.is_active:
                    flask_user = get_flaskuser(self.request.user.username)
                    flask_user.add(product_to_add, quantity_to_add)
                    messages.success(self.request, "'%s' successfully added to your cart, %s." % (product_to_add, self.request.user.username))
                else:
                    messages.error(self.request, "You must activate your account.")
            else:
                res = {'name': product_to_add, 'qty': quantity_to_add}
                self.request.session[product_pk] = res
                messages.success(self.request, "'%s' successfully added in your cart." % product_to_add)
            return redirect('grocerystore:index')

        except:#if the user uses the search tool
            searched_item = self.request.POST.get('search')
            # if re.search(r'([\w+]+[\s]*)', searched_item):
            if searched_item.isalpha():
                messages.info(self.request, "You're looking for '%s':" % searched_item)
                searched_item = urllib.quote(searched_item.encode('utf8'))
                return redirect('grocerystore:search', searched_item=searched_item)
            else:
                messages.error(self.request, "You must type in only alphabetical characters")
                return redirect('grocerystore:index')


class UserRegisterView(View):
    form_class = RegisterForm
    template_name = 'grocerystore/registration_form.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        try:
            user = User.objects.get(username=self.request.POST['username'])
            messages.error(self.request, "This username is already used, please choose another one.")
            return redirect('grocerystore:register')
        except:
            pass

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
                    flask_user = get_flaskuser(user.username)
                    try:
                        for elt in self.request.session.keys():
                            flask_user.add(self.request.session[elt]["name"], self.request.session[elt]["qty"])
                    except TypeError:
                        pass
                    login(self.request, user)
                    messages.success(self.request, "You're now registered and logged in, %s" % user.username)
                    return redirect('grocerystore:cart')

        messages.error(request, "Please use allowed characters in your username")
        return redirect('grocerystore:register')


class UserLoginForm(View):
    form_class = LoginForm
    template_name = 'grocerystore/login_form.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        username = self.request.POST['username']
        password = self.request.POST['password']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'There\'s no account with that username, please register.')
            return redirect('grocerystore:register')

        try:
            user = authenticate(username=username, password=password)
            if user.is_authenticated:
                if user.is_active:
                    flask_user = get_flaskuser(user.username)
                    try:
                        for elt in self.request.session.keys():
                            flask_user.add(self.request.session[elt]["name"], self.request.session[elt]["qty"])
                    except TypeError:
                        pass
                    login(self.request, user)
                    messages.success(self.request, "You are now logged in, %s." % user.username)
                    return redirect('grocerystore:cart')
        except AttributeError:
            messages.error(request, 'Forgot your password?')
            return redirect('grocerystore:login')


class CartView(View):
    template_name = 'grocerystore/cart.html'

    def get(self, request):
        in_cart = []
        cart_total = 0
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                flask_user = get_flaskuser(self.request.user.username)
                cart = flask_user.list()['items']
                if len(cart) == 0:
                    context = {'cart_total': "Your cart is empty.", 'username': self.request.user.username,}
                else:
                    for elt in cart:
                        product = Product.objects.get(product_name=elt["name"])
                        price = "%.2f" % (float(elt["qty"]) * float(product.product_price))
                        item = [elt["name"], int(elt["qty"]), product.product_unit, price]
                        in_cart.append(item)
                        cart_total += float(price)
                    cart_total = "Cart total: $%.2f" % cart_total
                    context = {'username': self.request.user.username, 'in_cart': in_cart, 'cart_total': cart_total, 'quantity_set': range(21),}
                return render(self.request, 'grocerystore/cart.html', context=context)
            else:
                messages.error(self.request, "Your account is inactive, please activate it.")
                return redirect('grocerystore:index')
        else:
            try:
                for elt in self.request.session.keys():
                    product_name = self.request.session[elt]["name"]
                    product_qty = self.request.session[elt]["qty"]
                    product = Product.objects.get(product_name=product_name)
                    price = "%.2f" % (float(product_qty) * float(product.product_price))
                    item = [product_name, int(product_qty), product.product_unit, price]
                    in_cart.append(item)
                    cart_total += float(price)
                cart_total = "Cart total: $%.2f" % cart_total
                context = {'in_cart': in_cart, 'cart_total': cart_total, 'quantity_set': range(21),}
            except KeyError:
                context = {'cart_total': "Your cart is empty.",}
            return render(self.request, 'grocerystore/cart.html', context=context)

    def post(self, request):
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                flask_user = get_flaskuser(self.request.user.username)
                cart = flask_user.list()['items'] # get a dictionary of dictionaries whose keys are "name" and "qty"

                if self.request.POST.get('empty'):# if the user press the "empty" button
                    if len(cart) > 0:
                        cart = flask_user.empty_cart()
                        messages.success(request, "You've just emptied your cart, %s." % self.request.user.username)
                    return redirect('grocerystore:cart')

                for elt in cart:# if the user wants to update an item quantity
                    product_to_update = elt["name"]
                    try:
                        qty_to_change = int(self.request.POST.get(elt["name"]))
                    except TypeError:# loops in the cart until it hits the product to update
                        continue
                    if qty_to_change == 0:
                        flask_user.delete(product_to_update)
                        messages.success(self.request, "'%s' has been removed from your cart." % product_to_update)
                    else:
                        flask_user.add(product_to_update, qty_to_change)
                        messages.success(self.request, "'%s' quantity has been updated." % product_to_update)
                return redirect('grocerystore:cart')

            else:
                messages.error(self.request, "Your account is inactive, please activate it.")
                return redirect('grocerystore:index')

        else:# if anonymous user/session
            if self.request.POST.get('empty'):
                cart = Session.objects.all()
                if len(cart) > 0:
                    cart.delete()
                    messages.success(self.request, "You've just emptied your cart.")
                return redirect('grocerystore:cart')

            for elt in self.request.session.keys():
                product_to_update = self.request.session[elt]["name"]
                try:
                    qty_to_change = int(self.request.POST.get(self.request.session[elt]["name"]))
                except TypeError:
                    continue
                if qty_to_change == 0:
                    del self.request.session[elt]
                    messages.success(self.request, "'%s' has been removed from your cart." % product_to_update)
                else:
                    self.request.session[elt] = {"name": product_to_update, "qty": qty_to_change}
                    messages.success(self.request, "'%s' quantity has been updated." % product_to_update)
            return redirect('grocerystore:cart')


def search_item(item):
    """Returns a list of Product instances whose 'product_name' contains at least
    one word in commun with the sought item passed in as a parameter"""
    searched_words = item.split(" ")
    products_available = Product.objects.all()
    search_result = []
    for word in searched_words:
        for product in products_available:
            if word.lower() in product.product_name.lower():
                search_result.append(product)
    return search_result


class SearchView(View):
    template_name = 'grocerystore/search.html'

    def get(self, request, searched_item):
        searched_item = urllib.unquote(searched_item)
        search_result = search_item(searched_item)
        if len(search_result) > 25:
            messages.error(request, "too many items match your research... Please be more specific.")
            return redirect('grocerystore:index')
        if len(search_result) == 0:
            messages.error(request, "unfortunately no available item matches your research...")
            return redirect('grocerystore:index')
        context = {'search_result': search_result, 'quantity_set': range(1, 21),}
        return render(request, 'grocerystore/search.html', context=context)

    def post(self, request, searched_item):
        searched_item = urllib.unquote(searched_item)
        search_result = search_item(searched_item)
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                flask_user = get_flaskuser(self.request.user.username)
                for product in search_result:
                    product_to_add = product.product_name
                    try:
                        quantity_to_add = int(self.request.POST.get(product.product_name))
                    except TypeError:
                        continue
                    flask_user.add(product_to_add, quantity_to_add)
                    messages.success(request, "'%s' successfully added to your cart" % product_to_add)
                return redirect('grocerystore:index')
            else:
                messages.info(request, "You need to activate your account to proceed.")
                return redirect('grocerystore:index')#create a page to activate inactive accounts
        else:
            for product in search_result:
                product_to_add = product.product_name
                try:
                    quantity_to_add = int(self.request.POST.get(product.product_name))
                except TypeError:
                    continue
                res = {'name': product_to_add, 'qty': quantity_to_add}
                self.request.session[product.pk] = res
                messages.success(request, "%s was successfully added in your cart." % product_to_add)
            return redirect('grocerystore:index')


class CheckoutView(LoginRequiredMixin, View):
    form_class = PaymentForm
    template_name = 'grocerystore/checkout.html'
    login_url = 'grocerystore:login'
    # next_url = 'grocerystore:checkout'
    # redirect_field_name = 'redirect_to'

    def get(self, request):
        payment_form = self.form_class(None)
        context = {'username': self.request.user.username, 'payment_form': payment_form,}
        return render(self.request, "grocerystore/checkout.html", context=context)

    def post(self, request):
        return redirect('grocerystore:congrats')

def congrats(request):
    messages.success(request, "Congratulations %s, your order was successfully processed." % request.user.username)
    return render(request, 'grocerystore/congrats.html')

@csrf_protect
def log_out(request):
    messages.success(request, "You've been logged out, %s. See ya!" % request.user.username)
    logout(request)
    return redirect('grocerystore:index')
