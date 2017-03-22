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
from inflaskart_api import InflaskartClient, search_item, get_flaskcart, remove_old_items


"""
This module contains 14 views:
- UserRegisterView
- UserLoginView
- log_out()
- ProfileView
- ProfileUpdateView
- IndexView
- StartView
- StoreView
- SubcategoriesList
- InstockList
- SearchView
- ProductDetailView
- CartView
- CheckoutView
"""



# the cart server is running locally on port 5000
CART_HOST = "http://127.0.0.1:5000/"



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
            return render(request, self.template_name, {'user_form': form1, 'address_form': form2})
        except:
            pass

        if form1.is_valid() and form2.is_valid():
            user = form1.save(commit=False)
            username = form1.cleaned_data['username']
            email = form1.cleaned_data['email']
            password = form1.cleaned_data['password']
            user.set_password(password)
            user.save()

            inflauser_address = form2.save(commit=False)
            inflauser_address.street_adress1 = cleaned_data['street_adress1']
            inflauser_address.street_adress2 = cleaned_data['street_adress2']
            inflauser_address.apt_nb = cleaned_data['apt_nb']
            inflauser_address.other = cleaned_data['other']
            inflauser_address.city = cleaned_data['city']
            inflauser_address.zip_code = cleaned_data['zip_code']
            inflauser_address.state = cleaned_data['state']
            inflauser_address.save()
            inflauser = Inflauser(infla_user=user, inflauser_address=inflauser_address)
            inflauser.save()

            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    flask_cart = get_flaskcart(user.username, CART_HOST)
                    deleted_items = remove_old_items(flask_cart)
                    if deleted_items:
                        msge = "Sorry, the following items had to be removed from "\
                               "your cart because there're not available anymore:"
                        for item in deleted_items:
                            msge += "\n" + item['qty'] + " " + item['name']
                        messages.info(self.request, msge)

                    # updating the user's cart if they added products in their cart
                    # before registering
                    inflauser_zipcode = Inflauser.objects.get(infla_user=user).inflauser_address.zip_code
                    not_available = False
                    for elt in self.request.session.keys():
                        product_availability_pk = self.request.session[elt]["name"]
                        flask_cart.add(product_availability_pk, self.request.session[elt]["qty"])
                        if not Availability.objects.get(pk=int(self.request.session[elt]["name"]))\
                               .store.delivery_area.all().filter(zipcode=inflauser_zipcode):
                            not_available = True
                    if not_available:
                        messages.error(self.request, "Before logging in, you shopped "\
                        "items in a store that doesn't deliver your current address.")

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
    """Allows the user to login if they're already registered."""
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
                    flask_cart = get_flaskcart(user.username, CART_HOST)
                    deleted_items = remove_old_items(flask_cart)
                    if deleted_items:
                        msge = "Sorry, the following items had to be removed from "\
                               "your cart because there're not available anymore:"
                        for item in deleted_items:
                            msge += "\n" + item['qty'] + " " + item['name']
                        messages.error(self.request, msge)

                    # updating the user's cart if they added products in their cart
                    # before registering
                    inflauser_zipcode = Inflauser.objects.get(infla_user=user).inflauser_address.zip_code
                    not_available = False
                    for elt in self.request.session.keys():
                        product_availability_pk = self.request.session[elt]["name"]
                        flask_cart.add(product_availability_pk, self.request.session[elt]["qty"])
                        if not Availability.objects.get(pk=int(self.request.session[elt]["name"]))\
                               .store.delivery_area.all().filter(zipcode=inflauser_zipcode):
                            not_available = True
                    if not_available:
                        messages.error(self.request, "Before logging in, you shopped "\
                        "items in a store that doesn't deliver your current address.")

                    login(self.request, user)
                    messages.success(self.request, "You're now logged in, %s" % user.username)
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


@csrf_protect
def log_out(request):
    messages.success(request, "You've been logged out, %s. See ya!" % request.user.username)
    logout(request)
    return redirect('grocerystore:index')


class ProfileView(LoginRequiredMixin, View):
    template_name = 'grocerystore/profile.html'
    login_url = 'grocerystore:login'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        inflauser_address = Inflauser.objects.get(infla_user=self.request.user).inflauser_address
        zipcode = inflauser_address.zip_code
        context = {'user_address': inflauser_address, 'zipcode': zipcode}
        available_stores = available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if available_stores:
            context['available_stores'] = available_stores
        return render(self.request, 'grocerystore/profile.html', context=context)

    def post(self, request):
        return redirect('grocerystore:profile_update')


class ProfileUpdateView(LoginRequiredMixin, View):
    """Allows an authenticated user to see and edit their profile."""
    template_name = 'grocerystore/profile_update.html'
    login_url = 'grocerystore:login'
    redirect_field_name = 'redirect_to'
    form_class = AddressForm

    def get(self, request):
        inflauser = Inflauser.objects.get(infla_user=self.request.user)
        inflauser_address = Inflauser.objects.get(infla_user=self.request.user).inflauser_address
        address_form = self.form_class(instance=inflauser_address)
        zipcode = inflauser_address.zip_code
        context = {'address_form': address_form, 'zipcode': zipcode}
        available_stores = available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if available_stores:
            context['available_stores'] = available_stores
        return render(self.request, 'grocerystore/profile_update.html', context=context)

    def post(self, request):
        new_first_name = self.request.POST['first_name']
        new_last_name = self.request.POST['last_name']
        user = self.request.user
        user.first_name = new_first_name
        user.last_name = new_last_name
        user.save()

        inflauser_address = Inflauser.objects.get(infla_user=user).inflauser_address
        new_address = self.form_class(self.request.POST, instance=inflauser_address)
        if new_address.is_valid():
            inflauser_address = new_address
            inflauser_address.save()
            return redirect('grocerystore:profile')

        messages.error(self.request, "Please make sure you enter valid information.")
        return render(self.request, 'grocerystore/profile_update.html', {'address_form': new_address})


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
            return render(self.request, 'grocerystore/index.html')

    def post(self, request):
        zipcode = self.request.POST.get('zipcode')
        if len(zipcode) < 4 or len(zipcode) > 5 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an valid zipcode.")
            return redirect('grocerystore:index')
        return redirect('grocerystore:start', zipcode=zipcode)


class StartView(View):
    """After the user has selected a zip code where to shop or has looged in."""
    template_name = 'grocerystore/start.html'
    context_object_name = "available_stores"

    def get(self, request, zipcode):
        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.")
            return redirect('grocerystore:index')
        context = {}
        context['zipcode'] = zipcode
        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if len(available_stores) > 0:
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
    Displays a search tool to look for available products and a dropdown menu
    where the user can choose a category of products."""
    form_class = SelectCategory
    template_name = 'grocerystore/store.html'

    def get(self, request, zipcode, store_id):
        if len(zipcode) < 4 or len(zipcode) > 5 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.")
            return redirect('grocerystore:index')
        try:
            store = Store.objects.get(pk=store_id)
        except: # if the user try to access a non-existent store page
            messages.error(self.request, "The store you're looking for doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)

        context = {}
        context['category_form'] = self.form_class(None)
        context['store'] = Store.objects.get(pk=store_id)
        context['store_id'] = store_id
        context['zipcode'] = zipcode
        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode).exclude(pk=store_id)
        if len(available_stores) > 0:
            context['available_stores'] = available_stores

        return render(self.request, 'grocerystore/store.html', context=context)

    def post(self, request, zipcode, store_id):
        form = self.form_class(self.request.POST)
        try: # if the user uses the search tool
            searched_item = self.request.POST.get('search')
            if searched_item.replace(" ", "").replace("-", "").isalpha():
                search_result = search_item(searched_item, store_id)
                if len(search_result) > 30:
                    messages.error(request, "too many items match your research... Please be more specific.")
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                if len(search_result) == 0:
                    messages.error(request, "unfortunately no available item matches your research at %s..." % Store.objects.get(pk=store_id))
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
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

    def get(self, request, zipcode, store_id, category_id):
        """Prevent the user from manually entering a non-existing URL in their browser"""
        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the store you're looking for doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)
        try: # check if the category_id does exist
            category = ProductCategory.objects.get(pk=category_id)
        except:
            messages.error(self.request, "Sorry, the category you're looking for doesn't exist.")
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        context = {}
        context['zipcode'] = zipcode
        context['store_id'] = store_id
        context['store'] = Store.objects.get(pk=int(store_id))
        context['category_id'] = category_id
        context['subcategories'] = ProductSubCategory.objects.filter(parent__pk=int(category_id))
        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode).exclude(pk=store_id)
        if len(available_stores) > 0:
            context['available_stores'] = available_stores

        return render(self.request, 'grocerystore/subcategories_list.html', context=context)


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

        context = {}
        context['zipcode'] = zipcode
        context['subcategory'] = ProductSubCategory.objects.get(pk=int(subcategory_id))
        context['store_id'] = store_id
        context['store'] = Store.objects.get(pk=int(store_id))
        context['category_id'] = category_id
        context['quantity_set'] = range(1, 21)

        available_products = Availability.objects.filter(store__pk=int(store_id))\
                             .filter(product__product_category__pk=int(subcategory_id))
        context['available_products'] = available_products

        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode).exclude(pk=store_id)
        if len(available_stores) > 0:
            context['available_stores'] = available_stores

        return render(self.request, 'grocerystore/instock_list.html', context=context)

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
                    flask_cart = get_flaskcart(self.request.user.username, CART_HOST)
                    flask_cart.add(str(product_availability_pk), quantity_to_add)
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                else:
                    messages.info(request, "You need to activate your account to proceed.")
                    print "user is not active"
                    return redirect('grocerystore:start', zipcode=zipcode)
            else:
                # if the user isn't authenticated
                res = {'name': str(product_availability_pk), 'qty': quantity_to_add}
                self.request.session[product_availability_pk] = res #pk of the Availability object
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class SearchView(View):
    """Displays a list of available products (in a given store) after the user
    uses the search tool of the store page"""
    template_name = 'grocerystore/search.html'

    def get(self, request, zipcode, store_id, searched_item):
        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)
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
                      'searched_item': searched_item,
                      }
            available_stores = Store.objects.filter(delivery_area__zipcode=zipcode).exclude(pk=store_id)
            if len(available_stores) > 0:
                context['available_stores'] = available_stores
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
                flask_cart = get_flaskcart(self.request.user.username, CART_HOST)
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
                return redirect('grocerystore:start', zipcode=zipcode)
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

    def get(self, request, zipcode, store_id, product_id):
        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)
        try: # check if the product_id does exist
            product = Product.objects.get(pk=product_id)
        except:
            messages.error(self.request, "Sorry, the requested product doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)
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
        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if len(available_stores) > 0:
            context['available_stores'] = available_stores

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
                flask_cart = get_flaskcart(self.request.user.username, CART_HOST)
                flask_cart.add(str(availability_id), quantity_to_add)
                messages.success(self.request, "'%s' successfully added to your cart" % product)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
            else:
                messages.info(request, "You need to activate your account to proceed.")
                return redirect('grocerystore:start', zipcode=zipcode)
        else:# if the user is anonymous
            res = {'name': str(availability_id), 'qty': quantity_to_add}
            self.request.session[availability_id] = res #pk of the Availability object
            messages.success(self.request, "'%s' successfully added to your cart" % product)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class CartView(View):
    """Display what's in the cart of the store the user's shopping in."""
    template_name = 'grocerystore/cart.html'

    def get(self, request, zipcode):
        """List the products in all the user carts."""
        all_carts = {}
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                user_cart = get_flaskcart(self.request.user.username, CART_HOST).list()['items']
                if len(user_cart) == 0:
                    context = {'username': self.request.user.username,
                              'zipcode': zipcode,
                              }
                else:
                    # all_carts = { store1: cart1, store2: cart2 }
                    # NB: cart : [[elt1], [elt2],..., [eltN], cart_total]
                    for item in user_cart:
                        item_availability_pk = int(item['name'])
                        item_availability = Availability.objects.get(pk=item_availability_pk)
                        item_store = item_availability.store
                        # be sure to show only the carts of the stores that deliver at the user address
                        if not item_store.delivery_area.all().filter(zipcode=zipcode):
                            continue
                        item_product = item_availability.product
                        item_price = "%.2f" % (float(item["qty"]) * float(item_availability.product_price))
                        elt = [item_product, item["qty"], item_availability.product_unit, item_price, item_availability_pk, item_product.pk]
                        try:
                            all_carts[item_store].append(elt)
                        except KeyError:
                            all_carts[item_store] = [elt]

                    for cart in all_carts.values():
                        cart_total = 0
                        for elt in cart:
                            cart_total += float(elt[3])
                        cart.append("%.2f" % cart_total)

                    context = {'username': self.request.user.username,
                               'all_carts': all_carts,
                               'quantity_set': range(21),
                               'zipcode': zipcode,}

                    available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
                    if len(available_stores) > 0:
                        context['available_stores'] = available_stores

                return render(self.request, 'grocerystore/cart.html', context=context)

            else:
                messages.error(self.request, "Your account is inactive, please activate it.")
                return redirect('grocerystore:index')

        else: # if user is anonymous
            context = {}
            context['zipcode'] = zipcode
            available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
            if len(available_stores) > 0:
                context['available_stores'] = available_stores

            try:
                for item in self.request.session.keys():
                    item_availability_pk = int(self.request.session[item]['name'])
                    item_availability = Availability.objects.get(pk=item_availability_pk)
                    item_store = item_availability.store
                    # be sure to show only the carts of the stores that deliver at the user address
                    if not item_store.delivery_area.all().filter(zipcode=zipcode):
                        continue
                    item_product = item_availability.product
                    item_price = "%.2f" % (float(self.request.session[item]["qty"]) * float(item_availability.product_price))
                    elt = [item_product, self.request.session[item]["qty"], item_availability.product_unit, item_price, item_availability_pk, item_product.pk]
                    try:
                        all_carts[item_store].append(elt)
                    except KeyError:
                        all_carts[item_store] = [elt]

                for cart in all_carts.values():
                    cart_total = 0
                    for elt in cart:
                        cart_total += float(elt[3])
                    cart.append("%.2f" % cart_total)

                context['all_carts'] = all_carts
                context['quantity_set'] = range(21)

            except KeyError:
                pass

            return render(self.request, 'grocerystore/cart.html', context=context)

    def post(self, request, zipcode):
        if self.request.user.is_authenticated:
            if self.request.user.is_active:
                flask_cart = get_flaskcart(self.request.user.username, CART_HOST)
                user_cart = flask_cart.list()['items']
                store_pks = []
                for elt in user_cart:
                    if Availability.objects.get(pk=elt["name"]).store.pk not in store_pks:
                        store_pks.append(Availability.objects.get(pk=int(elt["name"])).store.pk)

                for i in store_pks: # if the user wants to empty a cart
                    try:
                        if self.request.POST['empty '+str(i)]:
                            for item in user_cart:
                                if Availability.objects.get(pk=int(item["name"])).store.pk == i:
                                    flask_cart.delete(item["name"])
                            messages.success(self.request, "You've just emptied your cart at %s." % Store.objects.get(pk=i))
                        return redirect('grocerystore:cart', zipcode=zipcode)
                    except:
                        continue

                for elt in user_cart: # if the user wants to update an item quantity
                    product_to_update = Availability.objects.get(pk=int(elt['name']))
                    try:
                        qty_to_change = int(self.request.POST.get(str(product_to_update.pk)))
                    except TypeError: # loops in the cart until it hits the product to update
                        continue
                    if qty_to_change == 0:
                        flask_cart.delete(elt['name'])
                        messages.success(self.request, "'%s' has been removed from your cart." % product_to_update)
                    else:
                        flask_cart.add(str(product_to_update.pk), qty_to_change)
                        messages.success(self.request, "'%s' quantity has been updated." % product_to_update)

                return redirect('grocerystore:cart', zipcode=zipcode)

            else:
                messages.error(self.request, "Your account is inactive, please activate it.")
                return redirect('grocerystore:index')

        else: # if anonymous user
            store_pks = []
            for item in self.request.session.keys():
                if Availability.objects.get(pk=int(self.request.session[item]["name"])).store.pk not in store_pks:
                    store_pks.append(Availability.objects.get(pk=int(self.request.session[item]["name"])).store.pk)

            for i in store_pks: # if the user wants to empty a cart
                try:
                    if self.request.POST['empty '+str(i)]:
                        for item in self.request.session.keys():
                            if Availability.objects.get(pk=int(self.request.session[item]["name"])).store.pk == i:
                                del self.request.session[item]
                        messages.success(self.request, "You've just emptied your cart at %s." % Store.objects.get(pk=i))
                    return redirect('grocerystore:cart', zipcode=zipcode)
                except:
                    continue

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
            return redirect('grocerystore:cart', zipcode=zipcode)


class CheckoutView(LoginRequiredMixin, View):
    form_class = PaymentForm
    template_name = 'grocerystore/checkout.html'
    login_url = 'grocerystore:login'
    redirect_field_name = 'redirect_to'

    def get(self, request, zipcode, store_id):
        user_cart = get_flaskcart(self.request.user.username, CART_HOST).list()['items']
        try:
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the store you want to check "\
                          "out from doesn't exist.")
        if not user_cart:
            context = {'empty_cart': 'You need to put items in your cart to checkout!',
                       'zipcode': zipcode,
                       'store_id': store_id,
                       'store': store,
                       }
            return render(self.request, 'grocerystore/checkout.html', context=context)

        payment_form = self.form_class(None)
        cart_total = 0
        for elt in user_cart:
            product_in_cart = Availability.objects.get(pk=int(elt['name']))
            if product_in_cart.store.pk == int(store_id):
                product_id = product_in_cart.product.pk
                price = float(elt["qty"]) * float(product_in_cart.product_price)
                cart_total += float(price)
        cart_total = "%.2f" % cart_total
        context = {'username': self.request.user.username,
                  'zipcode': zipcode,
                  'store_id': store_id,
                  'payment_form': payment_form,
                  'amount_to_pay': cart_total,
                  'store': store,
                  }
        return render(self.request, "grocerystore/checkout.html", context=context)

    def post(self, request, zipcode, store_id):
        """Empties the cart and redirect to the start shopping page.
        NB: this is a fake check out (there's no security page to pay)."""
        payment_data = self.form_class(self.request.POST)
        if payment_data.is_valid():
            flask_cart = get_flaskcart(self.request.user.username, CART_HOST)
            flask_cart.empty_cart()
            messages.success(self.request, "Congratulations for your purchase!")
            return redirect('grocerystore:start', zipcode=zipcode)
        messages.error(self.request, "Please be sure to enter valid credit cart information.")
        return redirect('grocerystore:checkout', zipcode=zipcode, store_id=store_id)
