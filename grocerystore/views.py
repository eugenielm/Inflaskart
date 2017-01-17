from __future__ import unicode_literals
import re
from django.shortcuts import redirect, render, get_object_or_404
from inflaskart_api import InflaskartClient
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from .forms import RegisterForm, LoginForm, PaymentForm, SelectCategory, StoreForm
from django.contrib.auth.models import User
import os
import urllib
from django.contrib import messages
from .models import Product, ProductCategory, ProductSubCategory,\
                    Dietary, Availability, Address, Store, Inflauser
from django.views.decorators.csrf import csrf_protect
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sessions.models import Session
from django.views.generic.list import ListView
import jsonpickle
# from django.contrib.auth.decorators import login_required


CART_HOST = "http://127.0.0.1:5000/"



def search_item(searched_item, store_id):
    """Returns a list of Availability instances whose 'product__product_name'
    contains at least one word in common with the searched item passed in as a parameter"""
    searched_words = searched_item.split(" ")
    user_store = Store.objects.get(pk=store_id)
    # products_in_store = user_store.product_set.all()
    available_products = user_store.availability_set.all()
    search_result = []
    for word in searched_words:
        for item in available_products:
            if word.lower() in item.product.product_name.lower():
                search_result.append(item)
    return search_result


def search_store(store):
    """Returns a list of Store instances whose 'store_name' contains at least
    one word in commun with the sought store passed in as a parameter"""
    searched_words = store.split(" ")
    stores = Store.objects.all()
    search_result = []
    for word in searched_words:
        for store in stores:
            if word.lower() in store.store_name.lower():
                search_result.append(store)
    return search_result


def get_flaskuser(username):
    """Returns an instance of the InflaskartClient class whose username is the
    one passed in as a parameter"""
    username_encoded = urllib.quote(urllib.quote(username))
    flask_user_url = os.path.join(CART_HOST, username_encoded)
    flask_user = InflaskartClient(flask_user_url, username.decode('utf8'))
    return flask_user


# def get_context_from_cart(cart, username):
#     """Returns the context to display in cart.html.
#     NB: cart["items"] are JSON encoded (ie: they're not Availability objects)"""
#     for elt in cart:
#         product_in_cart = jsonpickle.decode(cart[elt]["name"])
#         price = "%.2f" % (float(elt["qty"]) * float(product_in_cart.product_price))
#         item = [elt["name"], int(elt["qty"]), product_in_cart.product_unit, price]
#         in_cart.append(item)
#         cart_total += float(price)
#     cart_total = "Cart total: $%.2f" % cart_total
#     context = {'username': username, 'in_cart': in_cart, 'cart_total': cart_total, 'quantity_set': range(21), 'store_id': store_id,}
#     return context


class IndexView(View):
    form_class = StoreForm
    template_name = 'grocerystore/index.html'

    def get(self, request):
        store_form = self.form_class(None)
        return render(self.request, 'grocerystore/index.html', {'store_form': store_form})

    def post(self, request):
        form = self.form_class(self.request.POST)
        try:#if the user uses the search tool
            searched_store = self.request.POST.get('search')
            # if re.search(r'([\w+]+[\s]*)', searched_item):
            if searched_store.isalpha():
                messages.info(self.request, "You're looking for '%s':" % searched_store)
                searched_store = urllib.quote(searched_store.encode('utf8'))
                return redirect('grocerystore:stores_set', searched_store=searched_store)
            else:
                messages.error(self.request, "You must type in only alphabetical characters")
                return redirect('grocerystore:index')
        except:
            store_id = self.request.POST.get('stores')
            return redirect('grocerystore:store', store_id=store_id)


class StoreView(View):
    form_class = SelectCategory
    template_name = 'grocerystore/store.html'

    def get(self, request, store_id):
        category_form = self.form_class(None)
        store = Store.objects.get(pk=store_id)
        context = {'category_form': category_form, 'store_id': store_id, 'store': store}
        return render(self.request, 'grocerystore/store.html', context=context)

    def post(self, request, store_id):
        form = self.form_class(self.request.POST)
        try:#if the user uses the search tool
            searched_item = self.request.POST.get('search')
            # if re.search(r'([\w+]+[\s]*)', searched_item):
            if searched_item.isalpha():
                search_result = search_item(searched_item, store_id)
                if len(search_result) > 25:
                    messages.error(request, "too many items match your research... Please be more specific.")
                    return redirect('grocerystore:store', store_id=store_id)
                if len(search_result) == 0:
                    messages.error(request, "unfortunately no available item matches your research at %s..." % Store.objects.get(pk=store_id))
                    return redirect('grocerystore:store', store_id=store_id)
                messages.info(self.request, "You're looking for '%s':" % searched_item)
                searched_item = urllib.quote(searched_item.encode('utf8'))
                return redirect('grocerystore:search_in_store', store_id=store_id, searched_item=searched_item)
            else:
                messages.error(self.request, "You must type in only alphabetical characters")
                return redirect('grocerystore:store', store_id=store_id)
        except:# if the user uses the category drop down menu
            category_id = self.request.POST['category']
            return redirect('grocerystore:subcategories', store_id=store_id, category_id=category_id)


class SubcategoriesList(ListView):
    template_name = 'grocerystore/subcategories_list.html'
    context_object_name = 'subcategories'

    def get_queryset(self):
        return ProductSubCategory.objects.filter(top_category__pk=int(self.kwargs['category_id']))

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SubcategoriesList, self).get_context_data(**kwargs)
        # all_subcategories = ProductSubCategory.objects.filter(top_category__pk=int(self.kwargs['category_id']))
        context['store_id'] = self.kwargs['store_id']
        context['category_id'] = self.kwargs['category_id']
        return context


class InstockList(ListView):
    template_name = 'grocerystore/instock_list.html'
    context_object_name = 'available_products'

    def get_queryset(self):
        subcategory_pk = int(self.kwargs['subcategory_id'])
        available_products = Availability.objects.filter(store__pk=int(self.kwargs['store_id']))\
                             .filter(product__product_category__pk=int(self.kwargs['subcategory_id']))
        if len(available_products) == 0:
            messages.error(self.request, "Sorry, there's no product available in this category in this store.")
        return available_products # Availability instance

    def get_context_data(self, **kwargs):
        context = super(InstockList, self).get_context_data(**kwargs)
        subcategory_pk = int(self.kwargs['subcategory_id'])
        context['store_id'] = self.kwargs['store_id']
        context['store_name'] = Store.objects.get(pk=int(self.kwargs['store_id']))
        context['category_id'] = self.kwargs['category_id']
        context['quantity_set'] = range(1, 21)
        return context

    def post(self, request, store_id, category_id, subcategory_id):
        available_products = Availability.objects.filter(store__pk=int(store_id))\
                             .filter(product__product_category__pk=int(subcategory_id))
        for product in available_products:# list of Availability instances
            try:
                quantity_to_add = int(self.request.POST[str(product.pk)])
            except TypeError:
                continue
            product_availability_pk = product.pk
            messages.success(self.request, "%s was successfully added in your cart."\
                             % product.product)

            if self.request.user.is_authenticated:
                if self.request.user.is_active:
                    flask_user = get_flaskuser(self.request.user.username)
                    flask_user.add(str(product_availability_pk), quantity_to_add)
                    return redirect('grocerystore:store', store_id=store_id)
                else:
                    messages.info(request, "You need to activate your account to proceed.")
                    return redirect('grocerystore:index')
            else: #if the user isn't authenticated
                res = {'name': str(product_availability_pk), 'qty': quantity_to_add}
                self.request.session[product_availability_pk] = res #pk of the Availability object
            return redirect('grocerystore:store', store_id=store_id)


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
                            product_availability_pk = self.request.session[elt]["name"]
                            flask_user.add(product_availability_pk, self.request.session[elt]["qty"])
                    except TypeError:
                        pass
                    login(self.request, user)
                    messages.success(self.request, "You're now registered and logged in, %s" % user.username)
                    return redirect('grocerystore:index')
                    # return redirect('grocerystore:cart', store_id=store_id)

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
                            # product = jsonpickle.encode(self.request.session[elt]["name"])
                            product_availability_pk = self.request.session[elt]["name"]
                            flask_user.add(product_availability_pk, self.request.session[elt]["qty"])
                            # flask_user.add(product, self.request.session[elt]["qty"])
                            # flask_user.add(self.request.session[elt]["name"], self.request.session[elt]["qty"])
                    except TypeError:
                        pass
                    login(self.request, user)
                    messages.success(self.request, "You are now logged in, %s." % user.username)
                    # return redirect('grocerystore:cart', store_id=store_id)
                    return redirect('grocerystore:index')
        except AttributeError:
            messages.error(request, 'Forgot your password?')
            return redirect('grocerystore:login')


class CartView(View):
    template_name = 'grocerystore/cart.html'

    def get(self, request, store_id):
        """List the products in the current store cart
        (i.e: products from another store cart won't appear)"""
        # self.request.session['store_id'] = store_id
        user_store = Store.objects.get(pk=store_id)
        in_cart = []
        cart_total = 0
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                flask_user = get_flaskuser(self.request.user.username)
                cart = flask_user.list()['items']
                if len(cart) == 0:
                    context = {'cart_total': "Your cart is empty.",
                              'username': self.request.user.username,
                              'store_id': store_id,
                              'user_store': user_store,
                              }
                else:
                    for elt in cart:
                        product_in_cart = Availability.objects.get(pk=int(elt['name']))
                        if product_in_cart.store.pk == int(store_id):
                            price = "%.2f" % (float(elt["qty"]) * float(product_in_cart.product_price))
                            item = [product_in_cart, elt["qty"], product_in_cart.product_unit, price, product_in_cart.pk]
                            in_cart.append(item)
                            cart_total += float(price)
                        else:
                            pass
                    cart_total = "Cart total: $%.2f" % cart_total
                    context = {'username': self.request.user.username,
                              'in_cart': in_cart,
                              'cart_total': cart_total,
                              'quantity_set': range(21),
                              'store_id': store_id,
                              'user_store': user_store,
                              }
                return render(self.request, 'grocerystore/cart.html', context=context)
            else:
                messages.error(self.request, "Your account is inactive, please activate it.")
                return redirect('grocerystore:index')
        else:
            try:
                for elt in self.request.session.keys():
                    product_in_cart = Availability.objects.get(pk=int(self.request.session[elt]['name']))
                    # product_in_cart = jsonpickle.decode(self.request.session[elt]["name"])# get an Availability object
                    if product_in_cart.store.pk == int(store_id):
                        qty_in_cart = self.request.session[elt]["qty"]
                        price = "%.2f" % (float(qty_in_cart) * float(product_in_cart.product_price))
                        item = [product_in_cart, int(qty_in_cart), product_in_cart.product_unit, price, product_in_cart.pk]
                        in_cart.append(item)
                        cart_total += float(price)
                    else:
                        pass
                cart_total = "Cart total: $%.2f" % cart_total
                context = {'in_cart': in_cart,
                          'cart_total': cart_total,
                          'quantity_set': range(21),
                          'store_id': store_id,
                          'user_store': user_store,
                          }
            except KeyError:
                context = {'cart_total': "Your cart is empty.", 'store_id': store_id, 'user_store': user_store,}
            return render(self.request, 'grocerystore/cart.html', context=context)

    def post(self, request, store_id):
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                flask_user = get_flaskuser(self.request.user.username)
                cart = flask_user.list()['items'] # get a dictionary of dictionaries whose keys are "name" (value=str(Availability object pk)) and "qty" (value=int)

                if self.request.POST.get('empty'):# if the user press the "empty" button
                    if len(cart) > 0:
                        flask_user.empty_cart()
                        messages.success(request, "You've just emptied your cart at %s, %s." % (Store.objects.get(pk=int(store_id)), self.request.user.username))
                    return redirect('grocerystore:cart', store_id=store_id)

                else:
                    for elt in cart:# if the user wants to update an item quantity
                        product_to_update = Availability.objects.get(pk=int(elt['name']))
                        try:
                            qty_to_change = int(self.request.POST.get(str(product_to_update.pk)))
                        except TypeError:# loops in the cart until it hits the product to update
                            continue
                        if qty_to_change == 0:
                            flask_user.delete(elt['name'])
                            messages.success(self.request, "'%s' has been removed from your cart." % product_to_update)
                        else:
                            product_availability_pk = product_to_update.pk
                            flask_user.add(str(product_availability_pk), qty_to_change)
                            messages.success(self.request, "'%s' quantity has been updated." % product_to_update)
                    return redirect('grocerystore:cart', store_id=store_id)

            else:
                messages.error(self.request, "Your account is inactive, please activate it.")
                return redirect('grocerystore:index', store_id=store_id)

        else:# if anonymous user/session
            if self.request.POST.get('empty'):
                try:
                    for item in self.request.session.keys():
                        product_in_cart = Availability.objects.get(pk=int(self.request.session[item]["name"])) ########## ou ?: Availability.objects.get(pk=int(item["name"]))
                        if product_in_cart.store.pk == int(store_id):
                            del self.request.session[item] #ou?: del item
                    messages.success(self.request, "You've just emptied your cart at %s." % Store.objects.get(pk=int(store_id)))
                except KeyError:
                    pass
                return redirect('grocerystore:cart', store_id=store_id)

            for item in self.request.session.keys():
                product_to_update = Availability.objects.get(pk=int(self.request.session[item]["name"]))
                try:
                    qty_to_change = int(self.request.POST.get(str(product_to_update.pk)))
                except TypeError:
                    continue
                if qty_to_change == 0:
                    del self.request.session[item]
                    messages.success(self.request, "'%s' has been removed from your cart." % product_to_update)
                else:
                    self.request.session[item] = {"name": str(product_to_update.pk), "qty": qty_to_change}
                    messages.success(self.request, "'%s' quantity has been updated." % product_to_update)
            return redirect('grocerystore:cart', store_id=store_id)


class StoresSetList(ListView):
    template_name = 'grocerystore/stores_set.html'
    context_object_name = 'available_stores'

    def get_queryset(self):
        searched_store = urllib.unquote(self.kwargs['searched_store'])
        return search_store(searched_store)


class SearchView(View):
    template_name = 'grocerystore/search_in_store.html'

    def get(self, request, store_id, searched_item):
        searched_item = urllib.unquote(searched_item)
        search_result = search_item(searched_item, store_id)
        available_products = []
        for available in search_result: #available is an Availability instance
            product_price = int(available.product_price)
            product_unit = available.product_unit
            available_products.append([available, product_price, product_unit])
        context = {'available_products': available_products, 'quantity_set': range(1, 21), 'store_id': store_id}
        return render(request, 'grocerystore/search_in_store.html', context=context)

    def post(self, request, store_id, searched_item):
        """When an item is added to the user cart, its "name" is the
        corresponding Availability object pk turned into a string"""
        searched_item = urllib.unquote(searched_item)
        search_result = search_item(searched_item, store_id)
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                flask_user = get_flaskuser(self.request.user.username)
                for product_to_add in search_result:
                    product_availability_pk = product_to_add.pk
                    # json_encoded_product = jsonpickle.encode(product_to_add) #encode the Availability object in json
                    # print "json_encoded_product: ", json_encoded_product
                    try:
                        quantity_to_add = int(self.request.POST.get(str(product_to_add.pk)))
                    except TypeError:
                        continue
                    # flask_user.add(json_encoded_product, quantity_to_add)
                    flask_user.add(str(product_availability_pk), quantity_to_add)
                    messages.success(request, "'%s' successfully added to your cart" % product_to_add)
                return redirect('grocerystore:store', store_id=store_id)
            else:
                messages.info(request, "You need to activate your account to proceed.")
                return redirect('grocerystore:index')
        else:# if the user is anonymous
            for product_to_add in search_result:
                try:
                    quantity_to_add = int(self.request.POST[str(product_to_add.pk)])
                    messages.success(request, "%s was successfully added in your cart." % product_to_add)
                except TypeError:
                    continue
                # json_encoded_product = jsonpickle.encode(product_to_add)
                product_availability_pk = product_to_add.pk
                res = {'name': str(product_availability_pk), 'qty': quantity_to_add}
                self.request.session[product_to_add.pk] = res #pk of the Availability object
            return redirect('grocerystore:store', store_id=store_id)


class CheckoutView(LoginRequiredMixin, View):
    form_class = PaymentForm
    template_name = 'grocerystore/checkout.html'
    login_url = 'grocerystore:login'
    # next_url = 'grocerystore:checkout'
    # redirect_field_name = 'redirect_to'

    def get(self, request, store_id):
        payment_form = self.form_class(None)
        context = {'username': self.request.user.username, 'payment_form': payment_form,}
        return render(self.request, "grocerystore/checkout.html", context=context)

    def post(self, request, store_id):
        return redirect('grocerystore:congrats')

def congrats(request):
    messages.success(request, "Congratulations %s, your order was successfully processed." % request.user.username)
    return render(request, 'grocerystore/congrats.html')

@csrf_protect
def log_out(request):
    messages.success(request, "You've been logged out, %s. See ya!" % request.user.username)
    logout(request)
    return redirect('grocerystore:index')
