from django.shortcuts import redirect, render, get_object_or_404
from inflaskart_api import InflaskartClient
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from .forms import RegisterForm, LoginForm, ShopForm
from django.contrib.auth.models import User
import os
import urllib
# from django.contrib.auth.decorators import login_required
# from django.views.decorators.csrf import csrf_protect
# from django.views.generic.base import TemplateView


CART_HOST = "http://127.0.0.1:5000/"

def index(request):
    return render(request, 'grocerystore/index.html', {})

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
            print "user: %s" % user.username
        except User.DoesNotExist:
            print "no user with that name"
            context = {'no_account': "There's no account with that username, please"}
            return render(request, 'grocerystore/registration_form.html', context=context)
            # return redirect('grocerystore:register')

        try:
            user = authenticate(username=username, password=password)
            if user.is_authenticated:
                if user.is_active:
                    login(request, user)
                    return redirect('grocerystore:user_home', username=request.user.username)
        except AttributeError:
            return render(request, self.template_name, {'form': form,
                   'error_message': "You entered the wrong password"})

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
                    return redirect('grocerystore:user_home', username=request.user.username)

        return render(request, self.template_name, {'form': form})

class ShowCartView(View):
    template_name = 'grocerystore/cart.html'

    def get(self, request, username):
        print username
        user = get_object_or_404(User, username=username)
        print user
        if request.user.is_authenticated:
            username_encoded = urllib.quote(urllib.quote(username))
            infla_user_url = os.path.join(CART_HOST, username_encoded)
            infla_user = InflaskartClient(infla_user_url, username.decode('utf8'))
            cart = infla_user.list()

            if len(cart['items']) == 0:
                context = {'empty_cart': "Your cart is empty, %s." % username}
            else:
                in_cart = []
                for elt in cart["items"]:
                    item = "%s: " % elt["name"] + "%s" % elt["qty"]
                    in_cart.append(item)
                cart_msge = "Hi %s, you have the following items in your cart:" % username
                context = {'cart_msge': cart_msge, 'in_cart': in_cart,}
            return render(request, 'grocerystore/cart.html', context=context)
        else:
            return redirect('grocerystore:login_form')

    # def post(self, request, username):
    #     user = get_object_or_404(User, username=username)
    #     if request.user.is_authenticated:
    #         username_encoded = urllib.quote(urllib.quote(username))
    #         infla_user_url = os.path.join(CART_HOST, username_encoded)
    #         infla_user = InflaskartClient(infla_user_url, username.decode('utf8'))
    #         product = request.POST[item[1]]
    #         infla_user.delete(product)
    #         context = {'del_msge': "%s has been removed from you cart." % product}
    #         return render(request, 'grocerystore/cart.html', context=context)

# def show_cart(request, username):
#     user = get_object_or_404(User, username=username)
#     if request.user.is_authenticated:
#         username_encoded = urllib.quote(urllib.quote(username))
#         infla_user_url = os.path.join(CART_HOST, username_encoded)
#         infla_user = InflaskartClient(infla_user_url, username.decode('utf8'))
#         cart = infla_user.list()
#
#         if len(cart['items']) == 0:
#             context = {'empty_cart': "Your cart is empty, %s." % username}
#         else:
#             in_cart = []
#             for elt in cart["items"]:
#                 item = "%s: " % elt["name"] + "%s" % elt["qty"]
#                 in_cart.append(item)
#             cart_msge = "Hi %s, you have the following items in your cart:" % username
#             context = {'cart_msge': cart_msge, 'in_cart': in_cart,}
#         return render(request, 'grocerystore/cart.html', context=context)
#     else:
#         return redirect('grocerystore:login_form')

class UserHomeView(View):
    form_class = ShopForm
    template_name = 'grocerystore/user_home.html'

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            context = {'no_account': "You need to register to start shopping: "}
            return render(request, 'grocerystore/registration_form.html', context=context)

        if request.user.is_authenticated:
            add_form = self.form_class(None)
            return render(request, 'grocerystore/user_home.html', {'username': username, 'add_form': add_form})
        else:
            context = {'not_loggedin': "You need to log in to start shopping: "}
            return render(request, 'grocerystore/login_form.html', context=context)

    def post(self, request, username):
        form = self.form_class(request.POST)
        product = request.POST['product']
        quantity = request.POST['quantity']

        username_encoded = urllib.quote(urllib.quote(username))
        infla_user_url = os.path.join(CART_HOST, username_encoded)
        infla_user = InflaskartClient(infla_user_url, username.decode('utf8'))
        infla_user.add(product, quantity)

        add_form = self.form_class(None)
        context = {'success_message' : "%s successfully added to your cart" % product,
                  'add_form': add_form, 'username': username}
        return render(request, 'grocerystore/user_home.html', context=context)

#
# @csrf_protect
# def log_out(request):
#     logout(request)
#     return redirect('grocerystore:home')
