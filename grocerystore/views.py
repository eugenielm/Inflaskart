#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
import os
import sys
import urllib
import re
from datetime import datetime
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from django.views.generic.list import ListView
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sessions.models import Session
from django.contrib.messages import get_messages
from .models import Product, ProductCategory, ProductSubCategory, Dietary, \
                    Availability, Address, Store, Inflauser, State, Zipcode, ItemInCart, Order
from .forms import LoginForm, PaymentForm, UserForm, AddressForm


"""
This module contains 13 views:
- UserRegisterView
- UserLoginView
- log_out()
- ProfileView
- ProfileUpdateView
- IndexView
- StartView
- StoreView
- InstockList
- SearchView
- ProductDetailView
- CartView
- CheckoutView

This module contains the function search_item, which is used in  the StoreView
and SearchView classes.
"""


CONTACT = "cowboy.de.tchernobyl@gmail.com"


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


class UserRegisterView(View):
    """Allows the user to create an account with the following fields:
    username, password, first and last names, email address"""
    form_class1 = UserForm
    form_class2 = AddressForm
    template_name = 'grocerystore/registration.html'

    def get(self, request):
        user_form = self.form_class1(None)
        address_form = self.form_class2(None)
        return render(self.request, self.template_name, {'user_form': user_form, 'address_form': address_form})

    def post(self, request):
        if 'login' in self.request.POST:
            try:
                redirect_to = self.request.GET['redirect_to']
                # use of HttpResponseRedirect to avoid DisallowedRedirect error
                return HttpResponseRedirect(reverse('grocerystore:login') + '?redirect_to=' + str(redirect_to))
            except:
                return redirect('grocerystore:login')

        form1 = self.form_class1(self.request.POST)
        form2 = self.form_class2(self.request.POST)
        try: # check if the username typed in is available
            user = User.objects.get(username=self.request.POST['username'])
            context = {'user_form': form1, 'address_form': form2}
            errors = []
            for er in form1.errors:
                if er == "username" and user.username == self.request.POST['username']:
                    context['unavailable_username'] = self.request.POST['username']
                if er == "street_address1":
                    er = "address"
                errors.append(er)
            context['errors'] = errors
            return render(self.request, self.template_name, context=context)
        except:
            pass

        if form1.is_valid() and form2.is_valid():
            inflauser_address = form2.save(commit=False)
            inflauser_address.zip_code = form2.cleaned_data['zip_code']
            if len(Store.objects.filter(delivery_area__zipcode=inflauser_address.zip_code)) == 0:
                messages.error(self.request, "Sorry, we're unable to create an account "\
                "because there's currently no store delivering in your zipcode area.")
                return redirect('grocerystore:index')
            inflauser_address.street_address1 = form2.cleaned_data['street_address1']
            inflauser_address.street_address2 = form2.cleaned_data['street_address2']
            inflauser_address.apt_nb = form2.cleaned_data['apt_nb']
            inflauser_address.other = form2.cleaned_data['other']
            inflauser_address.city = form2.cleaned_data['city']
            inflauser_address.state = form2.cleaned_data['state']
            inflauser_address.save()

            user = form1.save(commit=False)
            username = form1.cleaned_data['username']
            email = form1.cleaned_data['email']
            password = form1.cleaned_data['password']
            user.set_password(password)
            user.save()

            inflauser = Inflauser(infla_user=user, inflauser_address=inflauser_address)
            inflauser.save()

            user = authenticate(username=username, password=password)
            if user is not None:
                # updating the user's cart if they added products in their cart
                # before registering
                inflauser_zipcode = Inflauser.objects.get(infla_user=user).inflauser_address.zip_code
                not_available = False
                try: # need try in case self.request.session is empty
                    for elt in self.request.session.keys():
                        availability = Availability.objects.get(pk=int(self.request.session[elt]["name"]))
                        # check if the item is already in the cart and update its quantity
                        try:
                            item = ItemInCart.objects.filter(incart_user=user).get(incart_availability=availability)
                            item.incart_quantity = int(self.request.session[elt]["qty"])
                            item.save()
                        # create an ItemInCart instance if the item isn't in the
                        # database, and save it in the database
                        except:
                            ItemInCart.objects.create(incart_user=user,
                                                      incart_availability=availability,
                                                      incart_quantity=int(self.request.session[elt]["qty"]))
                        if not availability.store.delivery_area.all().filter(zipcode=inflauser_zipcode):
                            not_available = True
                except: # if the user didn't put anything in their cart before signing up
                    pass

                if not_available:
                    messages.error(self.request, "Before registering, you shopped "\
                    "items in a store that doesn't deliver your current address.")

                login(self.request, user)
                messages.info(self.request, "You're now registered and logged in, %s" % user.username)
                try:
                    redirect_to = self.request.GET['redirect_to']
                    # remove the first and last items which are empty strings
                    redirect_parts = redirect_to.split('/')[1:-1]
                    # proper redirection if the user is trying to checkout in a store
                    # that doesn't deliver his/her area
                    if redirect_parts[-1] == 'checkout':
                        if Store.objects.get(pk=int(redirect_parts[-2]))\
                        not in Store.objects.filter(delivery_area__zipcode=redirect_parts[1]):
                            return redirect('grocerystore:start', zipcode=inflauser.inflauser_address.zip_code)
                    return redirect(self.request.GET['redirect_to'])
                except:
                    zipcode = inflauser.inflauser_address.zip_code
                    return redirect('grocerystore:start', zipcode=zipcode)

        errors = []
        for er in form1.errors:
            errors.append(er)
        for er in form2.errors:
            errors.append(er)
        return render(self.request, self.template_name, {'user_form': form1,
                                                         'address_form': form2,
                                                         'errors': errors})


class UserLoginView(View):
    """Allows the user to login if they're already registered."""
    form_class = LoginForm
    template_name = 'grocerystore/login.html'

    def get(self, request):
        login_form = self.form_class(None)
        return render(self.request, self.template_name, {'login_form': login_form})

    def post(self, request):
        if 'signup' in self.request.POST:
            try:
                redirect_to = self.request.GET['redirect_to']
                # use of HttpResponseRedirect to avoid DisallowedRedirect error
                return HttpResponseRedirect(reverse('grocerystore:register') + '?redirect_to=' + str(redirect_to))
            except:
                return redirect('grocerystore:register')

        form = self.form_class(request.POST)
        username = self.request.POST['username']
        password = self.request.POST['password']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(self.request, "Something went wrong. Please check your"\
                                         " username and password.")
            try:
                redirect_to = self.request.GET['redirect_to']
                return redirect('grocerystore:login' + '?redirect_to=' + str(redirect_to))
            except:
                return redirect('grocerystore:login')

        if not user.is_active: # an inactive user can't log in
            messages.error(self.request, "Your account is inactive. Please "\
                                         "send an email to %s to activate it." % CONTACT)
            return redirect('grocerystore:index')

        user = authenticate(username=username, password=password)
        if user is not None:
            # updating the user's cart if they added products in their cart
            # before registering
            inflauser_zipcode = Inflauser.objects.get(infla_user=user).inflauser_address.zip_code
            not_available = False
            try: # need try in case self.request.session is empty
                for elt in self.request.session.keys():
                    availability = Availability.objects.get(pk=int(self.request.session[elt]["name"]))
                    # check if the item is already in the cart and update its quantity
                    try:
                        item = ItemInCart.objects.filter(incart_user=user)\
                        .get(incart_availability=availability)
                        item.incart_quantity = self.request.session[elt]["qty"]
                        item.save()
                    # create an ItemInCart instance if the item isn't in the
                    # database, and save it in the database
                    except:
                        ItemInCart.objects.create(incart_user=user,
                                                  incart_availability=availability,
                                                  incart_quantity=self.request.session[elt]["qty"])
                    if not availability.store.delivery_area.all().filter(zipcode=inflauser_zipcode):
                        not_available = True
            except: # the user didn't put anything in their cart before logging in
                pass

            if not_available:
                messages.error(self.request, "Before logging in, you shopped "\
                "items in a store that doesn't deliver your current address.")

            login(self.request, user)
            messages.info(self.request, "You're now logged in, %s" % user.username)
            inflauser = Inflauser.objects.get(infla_user=user)
            try:
                redirect_to = self.request.GET['redirect_to']
                redirect_parts = redirect_to.split('/')[1:-1]
                # proper redirection if the user is trying to checkout in a store
                # that doesn't deliver their area
                if redirect_parts[-1] == 'checkout':
                    if Store.objects.get(pk=int(redirect_parts[-2]))\
                    not in Store.objects.filter(delivery_area__zipcode=redirect_parts[1]):
                        return redirect('grocerystore:start', zipcode=inflauser.inflauser_address.zip_code)
                return redirect(self.request.GET['redirect_to'])
            except:
                zipcode = inflauser.inflauser_address.zip_code
                return redirect('grocerystore:start', zipcode=zipcode)

        else: # the user couldn't be authenticated because the credentials are invalid
            messages.error(self.request, "Something went wrong. Please  check "\
                                         "your username and password.")
            try:
                redirect_to = self.request.GET['redirect_to']
                return redirect('grocerystore:login' + '?redirect_to=' + str(redirect_to))
            except:
                return redirect('grocerystore:login')


@csrf_protect
def log_out(request):
    messages.info(request, "You've been logged out, %s. See ya!" % request.user.username)
    logout(request)
    return redirect('grocerystore:index')


class ProfileView(LoginRequiredMixin, View):
    template_name = 'grocerystore/profile.html'
    login_url = 'grocerystore:login'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        inflauser_address = Inflauser.objects.get(infla_user=self.request.user).inflauser_address
        user = self.request.user
        zipcode = inflauser_address.zip_code
        context = {'user': user, 'user_address': inflauser_address, 'zipcode': zipcode}
        available_stores = available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if available_stores:
            context['available_stores'] = available_stores
        return render(self.request, 'grocerystore/profile.html', context=context)

    def post(self, request):
        return redirect('grocerystore:profile_update')


class ProfileUpdateView(LoginRequiredMixin, View):
    """Allow an authenticated user to see and edit their profile - except their
    username and password."""
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
        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if available_stores:
            context['available_stores'] = available_stores
        return render(self.request, 'grocerystore/profile_update.html', context=context)

    def post(self, request):
        user = self.request.user
        inflauser_address = Inflauser.objects.get(infla_user=user).inflauser_address
        zipcode = inflauser_address.zip_code
        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        new_address = self.form_class(self.request.POST, instance=inflauser_address)
        new_email = self.request.POST['email']
        new_first_name = self.request.POST['first_name']
        new_last_name = self.request.POST['last_name']
        errors = []

        if (re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", new_email)) is not None:
            if not new_email == user.email:
                messages.info(self.request, "Your email has been updated.")
                user.email = new_email
                user.save()
        else:
            errors.append("email")

        if new_first_name.replace(" ", "").isalpha() and len(new_first_name) < 20:
            if not new_first_name == user.first_name:
                messages.info(self.request, "Your first name has been updated.")
                user.first_name = new_first_name
                user.save()
        else:
            errors.append("first name")

        if new_last_name.replace(" ", "").isalpha() and len(new_last_name) < 20:
            if not new_last_name == user.last_name:
                messages.info(self.request, "Your last name has been updated.")
                user.last_name = new_last_name
                user.save()
        else:
            errors.append("last name")

        if not new_address.is_valid() \
           or not (new_first_name.replace(" ", "").isalpha() and not new_first_name.replace("-", "").isalpha()) \
           or not (new_last_name.replace(" ", "").isalpha() and not new_last_name.replace("-", "").isalpha())\
           or not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", new_email):

            context = {'address_form': new_address,
                       'zipcode': zipcode}
            if available_stores:
                context['available_stores'] = available_stores

            for er in new_address.errors:
                if er == "street_address1":
                    er = "address"
                errors.append(er)

            context['errors'] = errors
            return render(self.request, 'grocerystore/profile_update.html', context=context)

        # if the user entered only valid information
        inflauser_address = new_address.save(commit=False)
        if len(Store.objects.filter(delivery_area__zipcode=new_address.cleaned_data['zip_code'])) == 0:
            messages.error(self.request, "Sorry, we're unable to update your zipcode "\
            "because there's no store delivering this area.")
            context = {'address_form': new_address, 'zipcode': zipcode}
            if available_stores:
                context['available_stores'] = available_stores
            return render(self.request, 'grocerystore/profile_update.html', context=context)
        inflauser_address.street_address1 = new_address.cleaned_data['street_address1']
        inflauser_address.street_address2 = new_address.cleaned_data['street_address2']
        inflauser_address.apt_nb = new_address.cleaned_data['apt_nb']
        inflauser_address.other = new_address.cleaned_data['other']
        inflauser_address.city = new_address.cleaned_data['city']
        inflauser_address.zip_code = new_address.cleaned_data['zip_code']
        inflauser_address.state = new_address.cleaned_data['state']
        inflauser_address.save()
        return redirect('grocerystore:profile')


class IndexView(View):
    """This is the Inflaskart index page, where the user chooses a store to shop in.
    Displays a search tool to look for a store, and a drop down menu with all
    available stores."""
    template_name = 'grocerystore/index.html'

    def get(self, request):
        context = {}
        storage = get_messages(self.request)
        for elt in storage:
            if elt.level_tag == 'success':
                context['hire_me'] = True
        if self.request.user.is_authenticated:
            context['username'] = self.request.user.username
            user_zipcode = Inflauser.objects.get(infla_user=self.request.user)\
                           .inflauser_address.zip_code
            context['user_zipcode'] = user_zipcode
            context['zipcode'] = Zipcode.objects.get(zipcode=user_zipcode)
            return render(self.request, 'grocerystore/index.html', context=context)
        return render(self.request, 'grocerystore/index.html')

    def post(self, request):
        zipcode = self.request.POST.get('zipcode')
        if len(zipcode) < 4 or len(zipcode) > 5 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an valid zipcode.")
            return redirect('grocerystore:index')
        return redirect('grocerystore:start', zipcode=zipcode)


class StartView(View):
    """Where the user selects a store, depending on the zip code they've selected
    (anonymous user) or the zip code area they live in (authenticated user)."""
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

        if Zipcode.objects.get(zipcode=int(zipcode)) not in store.delivery_area.all():
            messages.error(self.request, "The store you're looking for doesn't "\
                                         "deliver in the area you've chosen.")
            return redirect('grocerystore:start', zipcode=zipcode)

        all_categories = {}
        # = {'category1': [subcat1, ..., subcatN], 'category2': [subcat1, ..., subcatN], etc.}
        for category in ProductCategory.objects.all():
            for subcat in category.productsubcategory_set.all():
                try:
                    all_categories[category].append(subcat)
                except KeyError:
                    all_categories[category] = [subcat]

        context = {}
        context['all_categories'] = all_categories
        context['store'] = store
        context['store_id'] = store_id
        context['zipcode'] = zipcode
        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if len(available_stores) > 0:
            context['available_stores'] = available_stores

        return render(self.request, 'grocerystore/store.html', context=context)

    def post(self, request, zipcode, store_id):
        searched_item = self.request.POST.get('search')
        if searched_item.replace(" ", "").replace("-", "").isalpha():
            search_result = search_item(searched_item, store_id)
            if len(search_result) > 30:
                messages.error(self.request, "too many items match your research... "\
                               "Please be more specific.")
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
            if len(search_result) == 0:
                messages.error(self.request, "unfortunately no available item matches "\
                               "your research at %s..." % Store.objects.get(pk=store_id))
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
            searched_item = urllib.quote(searched_item.encode('utf8'))
            return redirect('grocerystore:search', zipcode=zipcode,
                                                   store_id=store_id,
                                                   searched_item=searched_item)
        else:
            messages.error(self.request, "You must enter only alphabetical characters")
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class InstockList(ListView):
    """This page lists all the available products in a given subcategory chosen
    by the user."""
    template_name = 'grocerystore/instock.html'
    context_object_name = 'available_products'

    def get(self, request, zipcode, store_id, category_id, subcategory_id):
        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.")
            return redirect('grocerystore:index')

        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)

        if Zipcode.objects.get(zipcode=int(zipcode)) not in store.delivery_area.all():
            messages.error(self.request, "The store you're looking for doesn't "\
                           "deliver in the area you've chosen.")
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
            return redirect('grocerystore:subcategories', zipcode=zipcode,
                                                          store_id=store_id,
                                                          category_id=category_id)

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

        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if len(available_stores) > 0:
            context['available_stores'] = available_stores

        return render(self.request, 'grocerystore/instock.html', context=context)

    def post(self, request, zipcode, store_id, category_id, subcategory_id):
        try:
            searched_item = self.request.POST.get('search')
            if searched_item.replace(" ", "").replace("-", "").isalpha():
                search_result = search_item(searched_item, store_id)
                if len(search_result) > 30:
                    messages.error(self.request, "too many items match your research... "\
                                   "Please be more specific.")
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                if len(search_result) == 0:
                    messages.error(self.request, "unfortunately no available item matches "\
                                   "your research at %s..." % Store.objects.get(pk=store_id))
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                searched_item = urllib.quote(searched_item.encode('utf8'))
                return redirect('grocerystore:search', zipcode=zipcode,
                                                       store_id=store_id,
                                                       searched_item=searched_item)
            else:
                messages.error(self.request, "You must enter only alphabetical characters")
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        except: pass

        available_products = Availability.objects.filter(store__pk=int(store_id))\
                             .filter(product__product_category__pk=int(subcategory_id))
        for availability in available_products: # list of Availability instances
            try:
                quantity_to_add = int(self.request.POST.get(str(availability.pk)))
            except TypeError:
                continue

            if self.request.user.is_authenticated:
                # check if the item is already in the cart and update its quantity
                try:
                    item = ItemInCart.objects.filter(incart_user=self.request.user)\
                           .get(incart_availability=availability)
                    item.incart_quantity = quantity_to_add
                    item.save()
                # create an ItemInCart instance if the item isn't in the
                # database, and save it in the database
                except:
                    ItemInCart.objects.create(incart_user=self.request.user,
                                              incart_availability=availability,
                                              incart_quantity=quantity_to_add)

                messages.info(self.request, "%s successfully added in your cart."\
                                 % availability.product)
                return redirect('grocerystore:instock', zipcode=zipcode,
                                                        store_id=store_id,
                                                        category_id=category_id,
                                                        subcategory_id=subcategory_id)

            else: # if the user isn't authenticated
                res = {'name': str(availability.pk), 'qty': quantity_to_add}
                self.request.session[str(availability.pk)] = res # pk of the Availability instance
                messages.info(self.request, "%s successfully added in your cart."\
                                 % availability.product)
                return redirect('grocerystore:instock', zipcode=zipcode,
                                                        store_id=store_id,
                                                        category_id=category_id,
                                                        subcategory_id=subcategory_id)


class SearchView(View):
    """Displays a list of available products (in a given store) after the user
    uses the search tool of the store page"""
    template_name = 'grocerystore/search.html'

    def get(self, request, zipcode, store_id, searched_item):
        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.")
            return redirect('grocerystore:index')

        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)

        if Zipcode.objects.get(zipcode=int(zipcode)) not in store.delivery_area.all():
            messages.error(self.request, "The store you're looking for doesn't deliver in the area you've chosen.")
            return redirect('grocerystore:start', zipcode=zipcode)

        store = Store.objects.get(pk=store_id)
        searched_item = urllib.unquote(searched_item)
        search_result = search_item(searched_item, store_id)
        available_products = []
        if len(search_result) > 0:
            for availability in search_result: # NB: availablity is an Availability instance
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
            available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
            if len(available_stores) > 0:
                context['available_stores'] = available_stores
            return render(self.request, 'grocerystore/search.html', context=context)

        else: # in case the search result is empty but still the user types the searched_item in the url
            messages.error(self.request, "unfortunately no available item matches your research at %s" % store)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

    def post(self, request, zipcode, store_id, searched_item):
        """When an item is added to the user cart, its "name" is the
        corresponding Availability object pk turned into a string"""
        try: # in case the user uses the search tool in the navigation bar
            new_searched_item = self.request.POST.get('search')
            if new_searched_item.replace(" ", "").replace("-", "").isalpha():
                search_result = search_item(new_searched_item, store_id)
                if len(search_result) > 30:
                    messages.error(self.request, "too many items match your research... "\
                                   "Please be more specific.")
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                if len(search_result) == 0:
                    messages.error(self.request, "unfortunately no available item matches "\
                                   "your research at %s..." % Store.objects.get(pk=store_id))
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                new_searched_item = urllib.quote(new_searched_item.encode('utf8'))
                return redirect('grocerystore:search', zipcode=zipcode,
                                                       store_id=store_id,
                                                       searched_item=new_searched_item)
            else:
                messages.error(self.request, "You must enter only alphabetical characters")
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
        except: pass

        # if the user wants to add one of the displayed products in their cart
        searched_item = urllib.unquote(searched_item)
        search_result = search_item(searched_item, store_id)
        if self.request.user.is_authenticated:
            for availability in search_result:
                try:
                    quantity_to_add = int(self.request.POST.get(str(availability.pk)))
                except TypeError:
                    continue
                # check if the item is already in the cart and update its quantity
                try:
                    item = ItemInCart.objects.filter(incart_user=self.request.user)\
                           .get(incart_availability=availability)
                    item.incart_quantity = quantity_to_add
                    item.save()
                # create an ItemInCart instance if the item isn't in the
                # database, and save it in the database
                except:
                    ItemInCart.objects.create(incart_user=self.request.user,
                                              incart_availability=availability,
                                              incart_quantity=quantity_to_add)
                messages.info(self.request, "'%s' successfully added to your cart" % availability)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        else: # if the user is anonymous
            for availability in search_result:
                try:
                    quantity_to_add = int(self.request.POST.get(str(availability.pk)))
                    messages.info(self.request, "%s successfully added in your cart." % availability)
                except TypeError:
                    continue
                res = {'name': str(availability.pk), 'qty': quantity_to_add}
                self.request.session[str(availability.pk)] = res # pk of the Availability instance
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class ProductDetailView(View):
    template_name = 'grocerystore/detail.html'

    def get(self, request, zipcode, store_id, product_id):
        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.")
            return redirect('grocerystore:index')

        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)

        if Zipcode.objects.get(zipcode=int(zipcode)) not in store.delivery_area.all():
            messages.error(self.request, "The store you're looking for doesn't "\
                           "deliver in the area you've chosen.")
            return redirect('grocerystore:start', zipcode=zipcode)

        try: # check if the product_id does exist
            product = Product.objects.get(pk=product_id)
        except:
            messages.error(self.request, "Sorry, the requested product doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)

        try: # check if the product is available in the chosen store
            product_availability = Availability.objects.filter(product=product).get(store=store)
        except:
            messages.error(self.request, "Sorry, the requested URL doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)

        other_availabilities = Availability.objects.filter(product=product)\
                               .filter(store__delivery_area__zipcode=zipcode)\
                               .exclude(pk=product_availability.pk)
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
        try:
            quantity_to_add = int(self.request.POST.get(str(product_id)))
        except: # if the user uses the search tool in the navigation bar
            searched_item = self.request.POST.get('search')
            if searched_item.replace(" ", "").replace("-", "").isalpha():
                search_result = search_item(searched_item, store_id)
                if len(search_result) > 30:
                    messages.error(self.request, "too many items match your research... "\
                                   "Please be more specific.")
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                if len(search_result) == 0:
                    messages.error(self.request, "unfortunately no available item matches "\
                                   "your research at %s..." % Store.objects.get(pk=store_id))
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                searched_item = urllib.quote(searched_item.encode('utf8'))
                return redirect('grocerystore:search', zipcode=zipcode,
                                                       store_id=store_id,
                                                       searched_item=searched_item)
            else:
                messages.error(self.request, "You must enter only alphabetical characters")
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        store = Store.objects.get(pk=store_id)
        product = Product.objects.get(pk=product_id)
        availability = Availability.objects.filter(store=store).get(product=product)
        if self.request.user.is_authenticated:
            # check if the item is already in the cart and update its quantity
            try:
                item = ItemInCart.objects.filter(incart_user=self.request.user)\
                       .get(incart_availability=availability)
                item.incart_quantity = quantity_to_add
                item.save()
            # create an ItemInCart instance if the item isn't in the
            # database, and save it in the database
            except:
                ItemInCart.objects.create(incart_user=self.request.user,
                                          incart_availability=availability,
                                          incart_quantity=quantity_to_add)
            messages.info(self.request, "'%s' successfully added to your cart" % product)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
        else: # if the user is anonymous
            res = {'name': str(availability.pk), 'qty': quantity_to_add}
            self.request.session[str(availability.pk)] = res # pk of the Availability instance
            messages.info(self.request, "'%s' successfully added to your cart" % product)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class CartView(View):
    """Display what's in the user's cart, ie. everything they've shopped in
    different stores (if the user is authenticated, display only the items in
    stores delivering the user's address)."""
    template_name = 'grocerystore/cart.html'

    def get(self, request, zipcode):
        """List the products in all the user carts."""
        # for the dictionary all_carts below, keys are store instances, and for
        # each key the associated value is a list of all the items in the cart
        # (there's one cart per store), the last element of each list being
        # the cart total for each store
        all_carts = {}
        context = {'zipcode': zipcode,}

        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.")
            return redirect('grocerystore:index')

        if self.request.user.is_authenticated:
            context['username'] = self.request.user.username
            available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
            if len(available_stores) > 0:
                context['available_stores'] = available_stores

            user_cart = ItemInCart.objects.filter(incart_user=self.request.user)
            for item in user_cart:
                item_availability = item.incart_availability
                item_product = item_availability.product
                item_qty = item.incart_quantity
                item_unit = item_availability.product_unit
                item_price = "%.2f" % (float(item_qty) * float(item_availability.product_price))
                elt = [item_product, item_qty, item_unit, item_price,
                       item_availability.pk, item_product.pk, item_availability.product_price]
                item_store = item_availability.store

                try:
                    all_carts[item_store].append(elt)
                except KeyError:
                    all_carts[item_store] = [elt]

            user_zipcode = Inflauser.objects.get(infla_user=self.request.user).inflauser_address.zip_code
            for store, cart in all_carts.items(): # cart is a list of elts (elts are lists too)
                cart_total = 0
                # True is for a store that delivers the user's address
                if store.delivery_area.all().filter(zipcode=user_zipcode):
                    cart.append(True)
                else: cart.append(False)

                for elt in cart[:-1]:
                    cart_total += float(elt[3]) # elt[3]=item_price
                cart.append("%.2f" % cart_total)

            context['all_carts'] = all_carts
            context['quantity_set'] = range(21)

            return render(self.request, 'grocerystore/cart.html', context=context)

        else: # if the user is anonymous
            available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
            if len(available_stores) > 0:
                context['available_stores'] = available_stores

            try:
                for item in self.request.session.keys():
                    item_availability_pk = int(self.request.session[item]['name'])
                    item_availability = Availability.objects.get(pk=item_availability_pk)
                    item_store = item_availability.store
                    item_product = item_availability.product
                    item_price = "%.2f" % (float(self.request.session[item]["qty"])\
                    * float(item_availability.product_price))
                    elt = [item_product, self.request.session[item]["qty"],
                           item_availability.product_unit, item_price,
                           item_availability_pk, item_product.pk, item_availability.product_price]

                    try:
                        all_carts[item_store].append(elt)
                    except KeyError:
                        all_carts[item_store] = [elt]

                for store, cart in all_carts.items():
                    cart_total = 0
                    # True is for a store that delivers the user's address
                    if store.delivery_area.all().filter(zipcode=zipcode):
                        cart.append(True)
                    else: cart.append(False)

                    for elt in cart[:-1]:
                        cart_total += float(elt[3])
                    cart.append("%.2f" % cart_total)

                context['all_carts'] = all_carts
                context['quantity_set'] = range(21)

            except KeyError: # if the anonymous user hasn't put anything in their cart
                pass

            return render(self.request, 'grocerystore/cart.html', context=context)

    def post(self, request, zipcode):
        if self.request.user.is_authenticated:
            user_cart = ItemInCart.objects.filter(incart_user=self.request.user)
            store_pks = []
            for item in user_cart:
                if item.incart_availability.store.pk not in store_pks:
                    store_pks.append(item.incart_availability.store.pk)

            for i in store_pks: # if the user wants to empty their cart in a given store
                try:
                    if self.request.POST['empty '+str(i)]:
                        for item in user_cart:
                            if item.incart_availability.store.pk == i:
                                item.delete()
                        messages.info(self.request, "You've just emptied your cart at %s."\
                        % Store.objects.get(pk=i))
                    return redirect('grocerystore:cart', zipcode=zipcode)
                except:
                    continue

            for elt in user_cart: # if the user wants to update an item quantity
                product_to_update = elt.incart_availability
                try:
                    qty_to_change = int(self.request.POST.get(str(product_to_update.pk)))
                except TypeError: # loops in the cart until it hits the product to update
                    continue
                # if the user wants to remove an item from their cart
                if qty_to_change == 0:
                    elt.delete()
                else:
                    elt.incart_quantity = qty_to_change
                    elt.save()

            return redirect('grocerystore:cart', zipcode=zipcode)

        else: # if anonymous user
            store_pks = []
            # getting a list of all the stores'pk from which the user has added
            # items in their cart (the cart being stored in request.session)
            for item in self.request.session.keys():
                if Availability.objects.get(pk=int(self.request.session[item]["name"])).store.pk not in store_pks:
                    store_pks.append(Availability.objects.get(pk=int(self.request.session[item]["name"])).store.pk)

            for i in store_pks: # if the user wants to empty a cart, iterate through all stores involved
                try:
                    if self.request.POST['empty '+str(i)]:
                        for item in self.request.session.keys():
                            if Availability.objects.get(pk=int(self.request.session[item]["name"])).store.pk == i:
                                del self.request.session[item]
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
                else:
                    self.request.session[item] = {"name": str(product_to_update.pk), "qty": qty_to_change}
            return redirect('grocerystore:cart', zipcode=zipcode)


class CheckoutView(LoginRequiredMixin, View):
    form_class = PaymentForm
    template_name = 'grocerystore/checkout.html'
    login_url = 'grocerystore:login'
    redirect_field_name = 'redirect_to'

    def get(self, request, zipcode, store_id):
        # if the user enters an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.")
            return redirect('grocerystore:index')

        try:
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the store you want to check "\
                          "out from doesn't exist.")
            return redirect('grocerystore:start', zipcode=zipcode)

        user_cart = ItemInCart.objects.filter(incart_user=self.request.user)
        if not user_cart: # if the user's cart is totally empty
            messages.error(self.request, "You need to put items in your cart to checkout!")
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        context = {'zipcode': zipcode,
                   'store_id': store_id,
                   'store': store,
                   'username': self.request.user.username,
                   'payment_form': self.form_class(None)}

        if Zipcode.objects.get(zipcode=self.request.user.inflauser.inflauser_address.zip_code) not in store.delivery_area.all():
            context['pickup'] = True

        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if available_stores:
            context['available_stores'] = available_stores

        cart_total = float(0)
        in_cart = []
        for item in user_cart:
            if item.incart_availability.store.pk == int(store_id):
                availability = item.incart_availability
                product = availability.product
                quantity = item.incart_quantity
                item_price = availability.product_price
                item_total = float(item_price * quantity)
                cart_total += item_total
                item_total = "%.2f" % item_total
                item_unit = availability.product_unit
                elt = [product, quantity, item_price, item_unit, item_total]
                in_cart.append(elt)

        cart_total = "%.2f" % cart_total

        if float(cart_total) == 0.00:
            messages.info(self.request, "You must put items in your cart to be able "\
                                        "to place an order!")
            return redirect('grocerystore:store', zipcode=zipode, store_id=store_id)

        context['cart_total'] = cart_total
        context['in_cart'] = in_cart

        return render(self.request, "grocerystore/checkout.html", context=context)

    def post(self, request, zipcode, store_id):
        """Empties the cart and redirect to the index shopping page.
        NB: this is a fake checkout!"""
        try:
            searched_item = self.request.POST.get('search')
            if searched_item.replace(" ", "").replace("-", "").isalpha():
                search_result = search_item(searched_item, store_id)
                if len(search_result) > 30:
                    messages.error(self.request, "too many items match your research... "\
                                   "Please be more specific.")
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                if len(search_result) == 0:
                    messages.error(self.request, "unfortunately no available item matches "\
                                   "your research at %s..." % Store.objects.get(pk=store_id))
                    return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
                searched_item = urllib.quote(searched_item.encode('utf8'))
                return redirect('grocerystore:search', zipcode=zipcode,
                                                       store_id=store_id,
                                                       searched_item=searched_item)
            else:
                messages.error(self.request, "You must enter only alphabetical characters")
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        except: pass

        payment_data = self.form_class(self.request.POST)
        if payment_data.is_valid():
            # would normally require money transfer from the user's bank
            # and to send purchased items list and user's address to delivery company
            user_cart = ItemInCart.objects.filter(incart_user=self.request.user)
            user = self.request.user
            user_address = Inflauser.objects.get(infla_user=user).inflauser_address
            store = Store.objects.get(pk=store_id)

            for item in user_cart:
                if item.incart_availability.store.pk == int(store_id):
                    try:
                        order_data['items'].append({
                            'product_pk': item.incart_availability.product.pk,
                            'product_name': item.incart_availability.product.product_name,
                            'product_price': str(item.incart_availability.product_price), # float and decimal types aren't JSON serializable
                            'product_qty': item.incart_quantity,
                            'product_unit': item.incart_availability.product_unit,
                            })
                    except: # if order_data doesn't exist yet
                        purchase_date = []
                        purchase_date.append(datetime.now().year)
                        purchase_date.append(datetime.now().month)
                        purchase_date.append(datetime.now().day)
                        purchase_date.append(datetime.now().hour)
                        purchase_date.append(datetime.now().second)
                        order_data = {
                        'purchase_date': purchase_date, # a datetime.datetime object isn't JSON serializable
                        'order_nb': "",
                        'user': {
                            'user_pk': user.pk,
                            'username': user.username, # type unicode
                            'user_email': user.email,
                            'user_firstname': user.first_name,
                            'user_lastname': user.last_name,
                            'user_address': {
                                'street_address1': user_address.street_address1,
                                'street_address2': user_address.street_address2,
                                'apt_nb': user_address.apt_nb,
                                'other': user_address.other,
                                'city': user_address.city,
                                'zip_code': user_address.zip_code,
                                'state_name': user_address.state.state_name,
                                'state_postal_code': user_address.state.state_postal_code,
                                },
                            },
                        'store': {
                            'store_pk': store_id,
                            'store_name': store.store_name,
                            'store_address': {
                                'store_location': store.store_location,
                                'store_address': store.store_address,
                                'store_city': store.store_city,
                                'store_zipcode': store.store_zipcode,
                                'store_state': store.store_state.state_name,
                                'store_state_postal_code': store.store_state.state_postal_code,
                                },
                            },
                        'items': [{
                            'product_pk': item.incart_availability.product.pk,
                            'product_name': item.incart_availability.product.product_name,
                            'product_price': str(item.incart_availability.product_price), # float and decimal types aren't JSON serializable
                            'product_qty': item.incart_quantity,
                            'product_unit': item.incart_availability.product_unit,
                            }],
                        }

                    item.delete()

            order = Order.objects.create(order_data=order_data)
            order.order_data['order_nb'] = int(10000 + order.pk)
            order.save()
            messages.success(self.request, "Congratulations for your virtual purchase!")
            return redirect('grocerystore:index')

        messages.error(self.request, "Please be sure to enter valid credit cart information.")
        return redirect('grocerystore:checkout', zipcode=zipcode, store_id=store_id)
