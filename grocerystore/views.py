#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
import os
import sys
import urllib
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from django.views.generic.list import ListView
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sessions.models import Session
from .models import Product, ProductCategory, ProductSubCategory, Dietary, \
                    Availability, Address, Store, Inflauser, State, Zipcode
from .forms import LoginForm, PaymentForm, SelectCategory, UserForm, AddressForm
from inflaskart_api import InflaskartClient
# from django.contrib.auth.decorators import login_required


"""
This module contains 4 functions and 11 classes:
- search_item()
- get_flaskcart()
- remove_old_items()
- log_out()
- IndexView
- StartView
- StoreView
- SubcategoriesList
- InstockList
- UserRegisterView
- UserLoginView
- CartView
- SearchView
- ProductDetailView
- CheckoutView
"""


# the cart server is running locally on port 5000
CART_HOST = "http://127.0.0.1:5000/"


def search_item(searched_item, store_id):
    """Returns a list of Availability instances whose 'product__product_name'
    contains at least one word in common with the searched item"""
    searched_words = searched_item.split(" ")
    user_store = Store.objects.get(pk=store_id)
    available_products = user_store.availability_set.all()
    search_result = []
    for word in searched_words:
        for item in available_products:
            if word.lower() in item.product.product_name.lower():
                search_result.append(item)
    return search_result


def get_flaskcart(username):
    """Returns an instance of the InflaskartClient class whose username is the
    one passed in as a parameter"""
    username_encoded = urllib.quote(urllib.quote(username))
    flask_cart_url = os.path.join(CART_HOST, username_encoded)
    flask_cart = InflaskartClient(flask_cart_url, username.decode('utf8'))
    return flask_cart


def remove_old_items(cart):
    """Removes old items from cart and returns a list of the deleted items.
    NB: cart must be an InflaskartClient instance."""
    old = []
    for item in cart.list()['items']: # if the user's cart isn't empty
        try:
            int(item['name'])
        except: # if this is an old item
            old.append(item)
            cart.delete(item['name'])

    if len(old) == 0: return None
    else: return old


@csrf_protect
def log_out(request):
    messages.success(request, "You've been logged out, %s. See ya!" % request.user.username)
    logout(request)
    return redirect('grocerystore:index')


class IndexView(View):
    """This is the Inflaskart index page, where the user chooses a store to shop in.
    Displays a search tool to look for a store, and a drop down menu with all
    available stores."""
    template_name = 'grocerystore/index.html'

    def get(self, request):
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                inflauser = Inflauser.objects.get(infla_user=self.request.user)
                return redirect('grocerystore:start', zipcode=inflauser.inflauser_address.zip_code)
        else:
            # return redirect('grocerystore:index')
            return render(self.request, 'grocerystore/index.html')

    def post(self, request):
        zipcode = self.request.POST.get('zipcode')
        return redirect('grocerystore:start', zipcode=zipcode)


class StartView(View):
    """After the user has selected a zip code where to shop."""
    template_name = 'grocerystore/start.html'
    context_object_name = "available_stores"

    def get(self, request, zipcode):
        context = {}
        context['zipcode'] = zipcode
        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if len(available_stores) == 0:
            context['no_store'] = "Sorry, there's no store available in the area you've chosen."
        else:
            context['available_stores'] = available_stores
        return render(self.request, 'grocerystore/start.html', context=context)

    def post(self, request, zipcode):
        form = self.form_class(self.request.POST)
        try:
            store_id = self.request.POST['stores'] # type unicode
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
        except: # in case the user selects the --Choose below-- label
            return redirect('grocerystore:start', zipcode=zipcode)


class StoreView(View):
    """This is the store index page.
    Displays a search tool to look for available products and a drop down menus
    where the user can choose a category of products."""
    form_class = SelectCategory
    template_name = 'grocerystore/store.html'

    def get(self, request, zipcode, store_id):
        category_form = self.form_class(None)
        store = Store.objects.get(pk=store_id)
        context = {'category_form': category_form, 'store_id': store_id, 'zipcode': zipcode, 'store': store}
        return render(self.request, 'grocerystore/store.html', context=context)
        try:
            store = Store.objects.get(pk=store_id)
            context = {'category_form': category_form, 'store_id': store_id, 'store': store}
            return render(self.request, 'grocerystore/store.html', context=context)
        except: # if the user try to access a non-existent store page
            messages.error(self.request, "The url you requested doesn't exist.")
            return redirect('grocerystore:index')

    def post(self, request, zipcode, store_id):
        form = self.form_class(self.request.POST)
        try: # if the user uses the search tool
            searched_item = self.request.POST.get('search')
            if searched_item.replace(" ", "").replace("-", "").isalpha():
                search_result = search_item(searched_item, store_id)
                if len(search_result) > 25:
                    messages.error(request, "too many items match your research... Please be more specific.")
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                if len(search_result) == 0:
                    messages.error(request, "unfortunately no available item matches your research at %s..." % Store.objects.get(pk=store_id))
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                messages.info(self.request, "You're looking for '%s':" % searched_item)
                searched_item = urllib.quote(searched_item.encode('utf8'))
                return redirect('grocerystore:search', zipcode=zipcode, store_id=store_id, searched_item=searched_item)
            else:
                messages.error(self.request, "You must type in only alphabetical characters")
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
        except: # if the user uses the category drop down menu
            try:
                category_id = self.request.POST.get('category')
                return redirect('grocerystore:subcategories', zipcode=zipcode, store_id=store_id, category_id=category_id)
            except: # in case the user selects the --Choose below-- label
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class SubcategoriesList(ListView):
    """This page lists all product subcategories in a store for a given category."""
    template_name = 'grocerystore/subcategories_list.html'
    context_object_name = 'subcategories'

    def get(self, request, zipcode, store_id, category_id):
        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested url doesn't exist")
            return redirect('grocerystore:start', zipcode=zipcode)
        try: # check if the category_id does exist
            category = ProductCategory.objects.get(pk=category_id)
        except:
            messages.error(self.request, "Sorry, the requested url doesn't exist")
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
        resp = super(SubcategoriesList, self).get(self, request, zipcode, store_id, category_id)
        return resp


    def get_queryset(self):
        return ProductSubCategory.objects.filter(parent__pk=int(self.kwargs['category_id']))

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SubcategoriesList, self).get_context_data(**kwargs)
        context['zipcode'] = self.kwargs['zipcode']
        context['store_id'] = self.kwargs['store_id']
        context['store'] = Store.objects.get(pk=self.kwargs['store_id'])
        context['category_id'] = self.kwargs['category_id']
        return context


class InstockList(ListView):
    """This page lists all the available products in a given subcategory chosen
    by the user."""
    template_name = 'grocerystore/instock_list.html'
    context_object_name = 'available_products'

    def get(self, request, zipcode, store_id, category_id, subcategory_id):
        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)
        try: # check if the category_id does exist
            category = ProductCategory.objects.get(pk=category_id)
        except:
            messages.error(self.request, "Sorry, the requested category doesn't exist.")
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
        try: # check if the subcategory_id does exist
            subcategory = ProductSubCategory.objects.get(pk=subcategory_id)
        except:
            messages.error(self.request, "Sorry, the requested sub-category doesn't exist.")
            return redirect('grocerystore:subcategories', zipcode=zipcode, store_id=store_id, category_id=category_id)
        resp = super(InstockList, self).get(self, request, zipcode, store_id, category_id, subcategory_id)
        return resp

    def get_queryset(self):
        subcategory_pk = int(self.kwargs['subcategory_id'])
        available_products = Availability.objects.filter(store__pk=int(self.kwargs['store_id']))\
                             .filter(product__product_category__pk=int(self.kwargs['subcategory_id']))
        if len(available_products) == 0:
            messages.error(self.request, "Sorry, there's no product available in this category in this store.")
        return available_products # Availability instance

    def get_context_data(self, **kwargs):
        context = super(InstockList, self).get_context_data(**kwargs)
        context['zipcode'] = self.kwargs['zipcode']
        context['subcategory'] = ProductSubCategory.objects.get(pk=int(self.kwargs['subcategory_id']))
        context['store_id'] = self.kwargs['store_id']
        context['store'] = Store.objects.get(pk=self.kwargs['store_id'])
        context['category_id'] = self.kwargs['category_id']
        context['quantity_set'] = range(1, 21)
        return context

    def post(self, request, zipcode, store_id, category_id, subcategory_id):
        available_products = Availability.objects.filter(store__pk=int(store_id))\
                             .filter(product__product_category__pk=int(subcategory_id))
        for availability in available_products: # list of Availability instances
            try:
                quantity_to_add = int(self.request.POST.get(str(availability.pk)))
            except TypeError:
                continue
            product_availability_pk = availability.pk
            messages.success(self.request, "%s was successfully added in your cart."\
                             % availability.product)

            if self.request.user.is_authenticated:
                if self.request.user.is_active:
                    flask_cart = get_flaskcart(self.request.user.username)
                    flask_cart.add(str(product_availability_pk), quantity_to_add)
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                else:
                    messages.info(request, "You need to activate your account to proceed.")
                    return redirect('grocerystore:index')

            # if the user isn't authenticated
            res = {'name': str(product_availability_pk), 'qty': quantity_to_add}
            self.request.session[product_availability_pk] = res #pk of the Availability object
        return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class UserRegisterView(View):
    """Allows the user to create an account with the following fields:
    username, password, first and last names, email address"""
    form_class1 = UserForm
    form_class2 = AddressForm
    template_name = 'grocerystore/registration.html'

    def get(self, request):
        user_form = self.form_class1(None)
        address_form = self.form_class2(None)
        return render(request, self.template_name, {'user_form': user_form, 'address_form': address_form})

    def post(self, request):
        form1 = self.form_class1(self.request.POST)
        form2 = self.form_class2(self.request.POST)
        try: # check if the username typed in is available
            user = User.objects.get(username=self.request.POST['username'])
            messages.error(self.request, "This username is already used, please choose another one.")
            return redirect('grocerystore:register')
        except:
            pass

        if form1.is_valid() and form2.is_valid():
            user = form1.save(commit=False)
            username = form1.cleaned_data['username']
            email = form1.cleaned_data['email']
            password = form1.cleaned_data['password']
            user.set_password(password)
            user.save()

            inflauser_address = form2.save()
            inflauser = Inflauser(infla_user=user, inflauser_address=inflauser_address)
            inflauser.save()

            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    flask_cart = get_flaskcart(user.username)
                    deleted_items = remove_old_items(flask_cart)
                    if deleted_items:
                        msge = "Sorry, the following items had to be removed from "\
                               "your cart because there're not available anymore:"
                        for item in deleted_items:
                            msge += "\n" + item['qty'] + " " + item['name']
                        messages.info(self.request, msge)

                    # updating the user's cart if they added products in their cart
                    # before registering
                    for elt in self.request.session.keys():
                        product_availability_pk = self.request.session[elt]["name"]
                        flask_cart.add(product_availability_pk, self.request.session[elt]["qty"])

                    login(self.request, user)
                    messages.success(self.request, "You're now registered and logged in, %s" % user.username)
                    try:
                        return redirect(self.request.GET['redirect_to'])
                    except:
                        zipcode = inflauser.inflauser_address.zip_code
                        return redirect('grocerystore:start', zipcode=zipcode)

                else: # if the user's account is not active
                    messages.error(self.request, "Please activate your account.")
                    return redirect('grocerystore:index')

        # if the forms aren't valid or if the user couldn't be authenticated
        return render(request, self.template_name, {'user_form': form1, 'address_form': form2})


class UserLoginView(View):
    """Allows the user to login if they're already registered"""
    form_class = LoginForm
    template_name = 'grocerystore/login_form.html'

    def get(self, request):
        login_form = self.form_class(None)
        return render(self.request, self.template_name, {'login_form': login_form})

    def post(self, request):
        form = self.form_class(request.POST)
        username = self.request.POST['username']
        password = self.request.POST['password']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(self.request, 'Something went wrong. Please check your username and password.')
            try:
                redirect_to = self.request.GET['redirect_to']
                return redirect('/grocerystore/login/' + '?redirect_to=' + str(redirect_to))
            except:
                return redirect('grocerystore:login')

        try:
            user = authenticate(username=username, password=password)
            if user.is_authenticated:
                if user.is_active:
                    flask_cart = get_flaskcart(user.username)
                    deleted_items = remove_old_items(flask_cart)
                    if deleted_items:
                        msge = "Sorry, the following items had to be removed from "\
                               "your cart because there're not available anymore:"
                        for item in deleted_items:
                            msge += "\n" + item['qty'] + " " + item['name']
                        messages.info(self.request, msge)

                    for elt in self.request.session.keys():
                        product_availability_pk = self.request.session[elt]["name"]
                        flask_cart.add(product_availability_pk, self.request.session[elt]["qty"])

                    login(self.request, user)
                    messages.success(self.request, "You're now registered and logged in, %s" % user.username)
                    inflauser = Inflauser.objects.get(infla_user=user)
                    try:
                        return redirect(self.request.GET['redirect_to'])
                    except:
                        zipcode = inflauser.inflauser_address.zip_code
                        return redirect('grocerystore:start', zipcode=zipcode)

                else: # if the user's account is not active
                    messages.error(self.request, "Please activate your account.")
                    return redirect('grocerystore:index')

        except AttributeError: # the user couldn't be authenticated
            messages.error(self.request, 'Something went wrong. Please check your username and password.')
            try:
                redirect_to = self.request.GET['redirect_to']
                return redirect('/grocerystore/login/' + '?redirect_to=' + str(redirect_to))
            except:
                return redirect('grocerystore:login')


class CartView(View):
    """Display what's in the cart of the store the user's shopping in."""
    template_name = 'grocerystore/cart.html'

    def get(self, request, zipcode, store_id):
        """List the products in the current store cart.
        (i.e: products from another store cart won't be listed)"""
        # self.request.session['store_id'] = store_id
        user_store = Store.objects.get(pk=store_id)
        in_cart = []
        cart_total = 0
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                print get_flaskcart(self.request.user.username).list()
                user_cart = get_flaskcart(self.request.user.username).list()['items']
                if len(user_cart) == 0:
                    context = {'cart_total': "Your cart is empty.",
                              'username': self.request.user.username,
                              'zipcode': zipcode,
                              'store_id': store_id,
                              'user_store': user_store,
                              }
                else:
                    for elt in user_cart:
                        product_in_cart = Availability.objects.get(pk=int(elt['name']))
                        if product_in_cart.store.pk == int(store_id):
                            product_id = product_in_cart.product.pk
                            price = "%.2f" % (float(elt["qty"]) * float(product_in_cart.product_price))
                            item = [product_in_cart.product, elt["qty"], product_in_cart.product_unit, price, product_in_cart.pk, product_id]
                            in_cart.append(item)
                            cart_total += float(price)
                        else:
                            pass
                    cart_total = "Cart total: $%.2f" % cart_total
                    context = {'username': self.request.user.username,
                              'in_cart': in_cart,
                              'cart_total': cart_total,
                              'quantity_set': range(21),
                              'zipcode': zipcode,
                              'store_id': store_id,
                              'user_store': user_store,
                              'not_empty': True,
                              }
                return render(self.request, 'grocerystore/cart.html', context=context)
            else:
                messages.error(self.request, "Your account is inactive, please activate it.")
                return redirect('grocerystore:index')
        else: # if user is anonymous
            try:
                for elt in self.request.session.keys():
                    product_in_cart = Availability.objects.get(pk=int(self.request.session[elt]['name']))
                    if product_in_cart.store.pk == int(store_id):
                        qty_in_cart = self.request.session[elt]["qty"]
                        product_id = product_in_cart.product.pk
                        price = "%.2f" % (float(qty_in_cart) * float(product_in_cart.product_price))
                        item = [product_in_cart, int(qty_in_cart), product_in_cart.product_unit, price, product_in_cart.pk, product_id]
                        in_cart.append(item)
                        cart_total += float(price)
                    else:
                        pass
                cart_total = "Cart total: $%.2f" % cart_total
                context = {'in_cart': in_cart,
                          'cart_total': cart_total,
                          'quantity_set': range(21),
                          'zipcode': zipcode,
                          'store_id': store_id,
                          'user_store': user_store,
                          'not_empty': True,
                          }
            except KeyError:
                context = {'cart_total': "Your cart is empty.", 'zipcode': zipcode, 'store_id': store_id, 'user_store': user_store,}
            return render(self.request, 'grocerystore/cart.html', context=context)

    def post(self, request, zipcode, store_id):
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                # flask_user = get_flaskuser(self.request.user.username)
                # cart = flask_user.list()['items'] # get a dictionary of dictionaries whose keys are "name" (value=str(Availability object pk)) and "qty" (value=int)
                flask_cart = get_flaskcart(self.request.user.username)
                user_cart = flask_cart.list()['items']
                if self.request.POST.get('empty'):# if the user press the "empty" button
                    if len(user_cart) > 0:
                        flask_cart.empty_cart()
                        messages.success(request, "You've just emptied your cart at %s, %s." % (Store.objects.get(pk=int(store_id)), self.request.user.username))
                    return redirect('grocerystore:cart', zipcode=zipcode, store_id=store_id)

                else:
                    for elt in user_cart:# if the user wants to update an item quantity
                        product_to_update = Availability.objects.get(pk=int(elt['name']))
                        try:
                            qty_to_change = int(self.request.POST.get(str(product_to_update.pk)))
                        except TypeError:# loops in the cart until it hits the product to update
                            continue
                        if qty_to_change == 0:
                            flask_cart.delete(elt['name'])
                            messages.success(self.request, "'%s' has been removed from your cart." % product_to_update)
                        else:
                            product_availability_pk = product_to_update.pk
                            flask_cart.add(str(product_availability_pk), qty_to_change)
                            messages.success(self.request, "'%s' quantity has been updated." % product_to_update)
                    return redirect('grocerystore:cart', zipcode=zipcode, store_id=store_id)

            else:
                messages.error(self.request, "Your account is inactive, please activate it.")
                return redirect('grocerystore:index')

        else: # if anonymous user/session
            if self.request.POST.get('empty'):
                try:
                    for item in self.request.session.keys():
                        product_in_cart = Availability.objects.get(pk=int(self.request.session[item]["name"])) ########## ou ?: Availability.objects.get(pk=int(item["name"]))
                        if product_in_cart.store.pk == int(store_id):
                            del self.request.session[item] #ou?: del item
                    messages.success(self.request, "You've just emptied your cart at %s." % Store.objects.get(pk=int(store_id)))
                except KeyError:
                    pass
                return redirect('grocerystore:cart', zipcode=zipcode, store_id=store_id)

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
            return redirect('grocerystore:cart', zipcode=zipcode, store_id=store_id)


class SearchView(View):
    """Displays a list of available products (in a given store) after the user
    uses the search tool of the store page"""
    template_name = 'grocerystore/search.html'

    def get(self, request, zipcode, store_id, searched_item):
        store = Store.objects.get(pk=store_id)
        searched_item = urllib.unquote(searched_item)
        search_result = search_item(searched_item, store_id)
        available_products = []
        if len(search_result) > 0:
            for availability in search_result: # NotaBene: availablity is an Availability instance
                product_price = float(availability.product_price)
                product_unit = availability.product_unit
                product_id = availability.product.pk
                available_products.append([availability, product_price, product_unit, product_id])
            context = {'available_products': available_products,
                      'quantity_set': range(1, 21),
                      'zipcode': zipcode,
                      'store_id': store_id,
                      'store': store,
                      }
            return render(self.request, 'grocerystore/search.html', context=context)
        else: # in case the search result is empty but still the user types the searched_item in the url
            messages.error(self.request, "unfortunately no available item matches your research at %s" % store)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

    def post(self, request, zipcode, store_id, searched_item):
        """When an item is added to the user cart, its "name" is the
        corresponding Availability object pk turned into a string"""
        searched_item = urllib.unquote(searched_item)
        search_result = search_item(searched_item, store_id)
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                flask_cart = get_flaskcart(self.request.user.username)
                for product_to_add in search_result:
                    product_availability_pk = product_to_add.pk
                    try:
                        quantity_to_add = int(self.request.POST.get(str(product_to_add.pk)))
                    except TypeError:
                        continue
                    flask_cart.add(str(product_availability_pk), quantity_to_add)
                    messages.success(self.request, "'%s' successfully added to your cart" % product_to_add)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
            else:
                messages.info(request, "You need to activate your account to proceed.")
                return redirect('grocerystore:index')
        else: # if the user is anonymous
            for product_to_add in search_result:
                try:
                    quantity_to_add = int(self.request.POST.get(str(product_to_add.pk)))
                    messages.success(request, "%s was successfully added in your cart." % product_to_add)
                except TypeError:
                    continue
                product_availability_pk = product_to_add.pk
                res = {'name': str(product_availability_pk), 'qty': quantity_to_add}
                self.request.session[product_to_add.pk] = res # pk of the Availability object
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class ProductDetailView(View):
    template_name = 'grocerystore/detail.html'

    def get_queryset(self):
        quantity_set = range(1, 21)
        return quantity_set

    def get(self, request, zipcode, store_id, product_id):
        store = Store.objects.get(pk=store_id)
        product = Product.objects.get(pk=product_id)
        product_availability = Availability.objects.filter(product=product).get(store=store)
        other_availabilities = Availability.objects.filter(product=product).filter(store__delivery_area__zipcode=zipcode).exclude(pk=product_availability.pk)
        context = {}
        if len(other_availabilities) > 0:
            context['other_availabilities'] = other_availabilities
        if len(product.product_dietary.all()) > 0:
            context['product_dietaries'] = product.product_dietary.all()
        context['zipcode'] = zipcode
        context['store_id'] = store_id
        context['store'] = store
        context['product'] = product
        context['product_availability'] = product_availability
        context['product_brand_or_variety'] = product.product_brand_or_variety
        context['product_description'] = product.product_description
        context['product_pic'] = product.product_pic
        context['user_id_required'] = product.user_id_required
        context['quantity_set'] = range(1, 21)

        return render(self.request, 'grocerystore/detail.html', context=context)

    def post(self, request, zipcode, store_id, product_id):
        """When an item is added to the user cart, its "name" key is the
        corresponding Availability object pk turned into a string"""
        quantity_to_add = int(self.request.POST.get(str(product_id)))
        store = Store.objects.get(pk=store_id)
        product = Product.objects.get(pk=product_id)
        availability_id = Availability.objects.filter(store=store).get(product=product).pk
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                flask_cart = get_flaskcart(self.request.user.username)
                flask_cart.add(str(availability_id), quantity_to_add)
                messages.success(self.request, "'%s' successfully added to your cart" % product)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
            else:
                messages.info(request, "You need to activate your account to proceed.")
                return redirect('grocerystore:index')
        else:# if the user is anonymous
            res = {'name': str(availability_id), 'qty': quantity_to_add}
            self.request.session[availability_id] = res #pk of the Availability object
            messages.success(self.request, "'%s' successfully added to your cart" % product)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class CheckoutView(LoginRequiredMixin, View):
    form_class = PaymentForm
    template_name = 'grocerystore/checkout.html'
    login_url = 'grocerystore:login'
    redirect_field_name = 'redirect_to'

    def get(self, request, zipcode, store_id):
        payment_form = self.form_class(None)
        user_cart = get_flaskcart(self.request.user.username).list()['items']
        cart_total = 0
        for elt in user_cart:
            product_in_cart = Availability.objects.get(pk=int(elt['name']))
            if product_in_cart.store.pk == int(store_id):
                product_id = product_in_cart.product.pk
                price = "%.2f" % (float(elt["qty"]) * float(product_in_cart.product_price))
                cart_total += float(price)

        context = {'username': self.request.user.username,
                  'zipcode': zipcode,
                  'store_id': store_id,
                  'payment_form': payment_form,
                  'amount_to_pay': cart_total,
                  'store': Store.objects.get(pk=store_id),}
        return render(self.request, "grocerystore/checkout.html", context=context)

    def post(self, request, zipcode, store_id):
        """Empties the cart and redirect to the start shopping page.
        NB: this is a fake check out (there's no security page to pay)."""
        flask_cart = get_flaskcart(self.request.user.username)
        flask_cart.empty_cart()
        messages.success(self.request, "Congratulations for your purchase!")
        return redirect('grocerystore:start', zipcode=zipcode)
