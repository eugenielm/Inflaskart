#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
import os
import sys
import urllib
import re
from datetime import datetime, timedelta
import time
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sessions.models import Session
from django.contrib.messages import get_messages
from .models import Product, ProductCategory, ProductSubCategory, Dietary, \
                    Availability, Address, Store, Inflauser, State, Zipcode, \
                    ItemInCart, Order, ProductPurchase
from .forms import LoginForm, PaymentForm, UserForm, AddressForm


"""
This module contains 15 views:
- UserRegisterView
- UserLoginView
- log_out()
- ProfileView
- ProfileUpdateView
- IndexView
- StartView
- StoreView
- Instock
- BuyAgainView
- SearchView
- ProductDetailView
- CartView
- CheckoutView
- OrdersHistory

This module contains the function search_item, which is used in the search tool
(in the navigation menu bar once the user has chosen a store to shop in).
"""

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


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
    """Allow the user to create an account."""
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
                # use of HttpResponseRedirect to avoid DisallowedRedirect warning
                return HttpResponseRedirect(reverse('grocerystore:login') + '?redirect_to=' + str(redirect_to))
            except:
                return redirect('grocerystore:login')

        form1 = self.form_class1(self.request.POST)
        form2 = self.form_class2(self.request.POST)

        try: # if the username typed in is unavailable
            user = User.objects.get(username=self.request.POST['username'])
            context = {'user_form': form1, 'address_form': form2}
            context['unavailable_username'] = self.request.POST['username']
            return render(self.request, self.template_name, context=context)

        except: pass

        if form1.is_valid() and form2.is_valid(): # if the username is available and all the information is valid
            inflauser_address = form2.save(commit=False)

            city = ""
            for part in form2.cleaned_data['city'].split()[:-1]:
                city += (part.capitalize() + " ")
            city += form2.cleaned_data['city'].split()[-1].capitalize()

            inflauser_address.zip_code = form2.cleaned_data['zip_code']
            inflauser_address.street_address1 = form2.cleaned_data['street_address1']
            inflauser_address.street_address2 = form2.cleaned_data['street_address2']
            inflauser_address.apt_nb = form2.cleaned_data['apt_nb']
            inflauser_address.other = form2.cleaned_data['other']
            inflauser_address.city = city
            inflauser_address.state = form2.cleaned_data['state']
            inflauser_address.save()

            user = form1.save(commit=False)

            capitalized_last_name = ""
            # a last name can contain either white spaces or hyphens (but not both)
            if "-" in form1.cleaned_data['last_name']:
                for part in form1.cleaned_data['last_name'].split("-")[:-1]:
                    capitalized_last_name += (part.capitalize() + "-")
                capitalized_last_name += form1.cleaned_data['last_name'].split("-")[-1].capitalize()
            else:
                for part in form1.cleaned_data['last_name'].split()[:-1]:
                    capitalized_last_name += (part.capitalize() + " ")
                capitalized_last_name += form1.cleaned_data['last_name'].split()[-1].capitalize()

            capitalized_first_name = ""
            # a last name can contain either white spaces or hyphens (but not both)
            if "-" in form1.cleaned_data['first_name']:
                for part in form1.cleaned_data['first_name'].split("-")[:-1]:
                    capitalized_first_name += (part.capitalize() + "-")
                capitalized_first_name += form1.cleaned_data['first_name'].split("-")[-1].capitalize()
            else:
                for part in form1.cleaned_data['first_name'].split()[:-1]:
                    capitalized_first_name += (part.capitalize() + " ")
                capitalized_first_name += form1.cleaned_data['first_name'].split()[-1].capitalize()

            user.username = form1.cleaned_data['username']
            user.email = form1.cleaned_data['email']
            user.first_name = capitalized_first_name
            user.last_name = capitalized_last_name
            password = form1.cleaned_data['password']
            user.set_password(password)
            user.save()

            inflauser = Inflauser(infla_user=user, inflauser_address=inflauser_address)
            inflauser.save()

            user = authenticate(username=user.username, password=password)
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
                messages.success(self.request, "You're now registered and logged in, %s" % user.username)
                try:
                    return redirect(self.request.GET['redirect_to'])
                except:
                    zipcode = inflauser.inflauser_address.zip_code
                    return redirect('grocerystore:start', zipcode=zipcode)

        for er in form1.errors:
            if er == "first_name":
                er = "first name"
            if er == "last_name":
                er = "last name"
            messages.error(self.request, "Invalid %s" % er)

        for er in form2.errors:
            if er == "street_address1":
                er = "address"
            if er == "street_address2":
                er = "address (line2)"
            messages.error(self.request, "Invalid %s" % er)

        context = {'user_form': form1, 'address_form': form2}

        return render(self.request, self.template_name, context=context)


class UserLoginView(View):
    """Allow the user to login if they're already registered."""
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
                                         " username and password.", fail_silently=True)
            try:
                redirect_to = self.request.GET['redirect_to']
                return HttpResponseRedirect(reverse('grocerystore:login') + '?redirect_to=' + str(redirect_to))
            except:
                return redirect('grocerystore:login')

        if not user.is_active: # an inactive user can't log in
            messages.error(self.request, "Your account is inactive. Please "\
                                         "send us an email to activate it.", fail_silently=True)
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

            login(self.request, user)
            inflauser = Inflauser.objects.get(infla_user=user)
            try:
                return redirect(self.request.GET['redirect_to'])
            except:
                zipcode = inflauser.inflauser_address.zip_code
                return redirect('grocerystore:start', zipcode=zipcode)

        else: # the user couldn't be authenticated because the password is invalid
            messages.error(self.request, "Something went wrong. Please  check "\
                                           "your username and password.", fail_silently=True)
            try:
                redirect_to = self.request.GET['redirect_to']
                return HttpResponseRedirect(reverse('grocerystore:login') + '?redirect_to=' + str(redirect_to))
            except:
                return redirect('grocerystore:login')


@csrf_protect
def log_out(request):
    messages.success(request, "You've been logged out, %s. See ya!" % request.user.username, fail_silently=True)
    logout(request)
    return redirect('grocerystore:index')


class ProfileView(LoginRequiredMixin, View):
    """Where an authenticated user can see their profile information."""
    template_name = 'grocerystore/profile.html'
    login_url = 'grocerystore:login'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        inflauser_address = Inflauser.objects.get(infla_user=self.request.user).inflauser_address
        user = self.request.user
        zipcode = inflauser_address.zip_code
        context = {'user': user, 'user_address': inflauser_address, 'zipcode': zipcode}
        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if available_stores:
            context['available_stores'] = available_stores
        return render(self.request, self.template_name, context=context)


class ProfileUpdateView(LoginRequiredMixin, View):
    """Allow an authenticated user to edit their profile info - except their
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
        return render(self.request, self.template_name, context=context)

    def post(self, request):
        user = self.request.user
        inflauser_address = Inflauser.objects.get(infla_user=user).inflauser_address
        zipcode = inflauser_address.zip_code
        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        new_address = self.form_class(self.request.POST, instance=inflauser_address)
        new_email = self.request.POST['email']
        new_first_name = self.request.POST['first_name']
        new_last_name = self.request.POST['last_name']

        if (re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", new_email)) is not None:
            if not new_email == user.email:
                user.email = new_email
                user.save()
        else:
            user.email = new_email
            messages.error(self.request, "Please enter a valid email.", fail_silently=True)

        if new_first_name.replace(" ", "").replace("-","").isalpha() and len(new_first_name) < 20:
            if not new_first_name == user.first_name:
                # NB: str.capwords() raises a UnicodeEncodeError
                capitalized_first_name = ""
                # a first name can contain either white spaces or a hyphens (but not both)
                if "-" in new_first_name:
                    for part in new_first_name.split("-")[:-1]:
                        capitalized_first_name += (part.capitalize() + "-")
                    capitalized_first_name += new_first_name.split("-")[-1].capitalize()
                else:
                    for part in new_first_name.split()[:-1]:
                        capitalized_first_name += (part.capitalize() + " ")
                    capitalized_first_name += new_first_name.split()[-1].capitalize()

                user.first_name = capitalized_first_name
                user.save()
        else:
            # keep the invalid first name the user has just entered - without saving it in the db
            user.first_name = new_first_name
            messages.error(self.request, "Please enter a valid first name.", fail_silently=True)

        if new_last_name.replace(" ", "").replace("-","").isalpha() and len(new_last_name) < 20:
            if not new_last_name == user.last_name:
                capitalized_last_name = ""
                # a last name can contain either white spaces or hyphens (but not both)
                if "-" in new_last_name:
                    for part in new_last_name.split("-")[:-1]:
                        capitalized_last_name += (part.capitalize() + "-")
                    capitalized_last_name += new_last_name.split("-")[-1].capitalize()
                else:
                    for part in new_last_name.split()[:-1]:
                        capitalized_last_name += (part.capitalize() + " ")
                    capitalized_last_name += new_last_name.split()[-1].capitalize()
                user.last_name = capitalized_last_name
                user.save()
        else:
            # keep the invalid last name the user has just entered - without saving it in the db
            user.last_name = new_last_name
            messages.error(self.request, "Please enter a valid last name.", fail_silently=True)

        if not new_address.is_valid() \
           or not new_first_name.replace(" ", "").replace("-", "").isalpha() \
           or not new_last_name.replace(" ", "").replace("-", "").isalpha() \
           or not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", new_email):
            context = {'address_form': new_address,
                       'zipcode': zipcode}
            if available_stores:
                context['available_stores'] = available_stores

            for er in new_address.errors:
                if er == "street_address1":
                    er = "address"
                if er == "street_address2":
                    er = "address (line 2)"
                messages.error(self.request, "Please enter a valid %s." % er, fail_silently=True)

            return render(self.request, self.template_name, context=context)

        # if the user entered only valid information
        inflauser_address = new_address.save(commit=False)

        city = ""
        for part in new_address.cleaned_data['city'].split()[:-1]:
            city += (part.capitalize() + " ")
        city += new_address.cleaned_data['city'].split()[-1].capitalize()

        inflauser_address.street_address1 = new_address.cleaned_data['street_address1']
        inflauser_address.street_address2 = new_address.cleaned_data['street_address2']
        inflauser_address.apt_nb = new_address.cleaned_data['apt_nb']
        inflauser_address.other = new_address.cleaned_data['other']
        inflauser_address.city = city
        inflauser_address.zip_code = new_address.cleaned_data['zip_code']
        inflauser_address.state = new_address.cleaned_data['state']
        inflauser_address.save()
        messages.success(self.request, "Your profile has been successfully updated.", fail_silently=True)
        return redirect('grocerystore:profile')


class IndexView(View):
    """This is the Inflaskart index page, where the user chooses an area to shop in.
    Display a drop down menu with all available ZIP codes (located in SF), and
    either a login and register buttons, or -if the user is authenticated- a
    shortcut button to shop in the area where they live."""
    template_name = 'grocerystore/index.html'

    def get(self, request):
        context = {}
        zipcode_set = ["-- Choose a ZIP code area to shop in --"]
        with open(os.path.join(APP_ROOT, 'zipcodes_list.txt')) as f:
            available_zipcodes = f.read().strip().split(",")
        for zipcode in available_zipcodes:
            zipcode_set.append(zipcode)
        context['zipcode_set'] = zipcode_set

        storage = get_messages(self.request)
        for elt in storage:
            if elt.level_tag == 'info':
                context['hire_me'] = True

        if self.request.user.is_authenticated:
            context['username'] = self.request.user.username
            context['zipcode'] = Inflauser.objects.get(infla_user=self.request.user)\
                                 .inflauser_address.zip_code
            context['zipcode_set'][0] = "-- Shop elsewhere --"
        return render(self.request, self.template_name, context=context)

    def post(self, request):
        return redirect('grocerystore:start', zipcode=self.request.POST.get('zipcode_choice'))


class StartView(View):
    """Where the user selects a store, depending on the zip code they've selected."""
    template_name = 'grocerystore/start.html'
    context_object_name = "available_stores"

    def get(self, request, zipcode):
        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.", fail_silently=True)
            return redirect('grocerystore:index')

        try: # check if there's at least one store that delivers the chosen zipcode
            # Zipcode objects are instanciated when a store wants to add it to its deliveray area
            zipcode_obj = Zipcode.objects.get(zipcode=int(zipcode))
        except: # if there aren't any stores that deliver the chosen zipcode area
            messages.error(self.request, "There's no store available in the area "\
                                         "you've chosen.", fail_silently=True)
            return redirect('grocerystore:index')

        context = {}
        try:
            context['zipcode'] = Zipcode.objects.get(zipcode=zipcode)
        except: # if there's no store that delivers the requested zipcode
            messages.error(self.request, "There is no store available in the %s area, "\
                          "please try another zip code" % zipcode, fail_silently=True)
            return redirect('grocerystore:index')

        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if len(available_stores) > 0:
            context['available_stores'] = available_stores
        return render(self.request, self.template_name, context=context)

    def post(self, request, zipcode):
        form = self.form_class(self.request.POST)
        try:
            store_id = self.request.POST['stores'] # type unicode
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
        except: # in case the user selects the --Choose below-- label
            return redirect('grocerystore:start', zipcode=zipcode)


class StoreView(View):
    """This is the store index page.
    Display the categories and sub-categories if/for available products, and -
    for authenticated users-, a link to re-place previous orders in this store
    and a shortcut to see/add products already bought in this store."""
    template_name = 'grocerystore/store.html'

    def get(self, request, zipcode, store_id):
        if len(zipcode) < 4 or len(zipcode) > 5 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.", fail_silently=True)
            return redirect('grocerystore:index')
        try:
            store = Store.objects.get(pk=store_id)
        except: # if the user try to access a non-existent store page
            messages.error(self.request, "The store you're looking for doesn't exist.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        try: # check if the chosen store delivers the chosen zipcode
            zipcode_obj = Zipcode.objects.get(zipcode=int(zipcode))
            if zipcode_obj not in store.delivery_area.all():
                messages.error(self.request, "The store you're looking for doesn't "\
                                             "deliver in the area you've chosen.", fail_silently=True)
                return redirect('grocerystore:start', zipcode=zipcode)
        except: # if there aren't any stores that deliver the chosen zipcode area
            messages.error(self.request, "There's no store available in the area "\
                                         "you've chosen.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        all_categories = {}
        # = {'category1': [subcat1, ..., subcatN], 'category2': [subcat1, ..., subcatN], etc.}
        for category in ProductCategory.objects.all():
            for subcat in category.productsubcategory_set.all():
                # a category shouldn't be displayed if the store has nothing in stock for it
                if Availability.objects.filter(store=store).filter(product__product_category=subcat):
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

        if self.request.user.is_authenticated:
            user = self.request.user
            user_orders = Order.objects.filter(data__user__user_pk=user.pk)\
                          .filter(data__store__store_pk=store_id)
            if user_orders:
                context['purchases_here'] = True

        return render(self.request, 'grocerystore/store.html', context=context)

    def post(self, request, zipcode, store_id):
        searched_item = self.request.POST.get('search')
        if searched_item.replace(" ", "").replace("-", "").isalpha():
            return redirect('grocerystore:search', zipcode=zipcode,
                                                   store_id=store_id,
                                                   searched_item=urllib.quote(searched_item.encode('utf8')))
        else:
            messages.error(self.request, "You must enter only alphabetical characters", fail_silently=True)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class Instock(View):
    """This page displays all the available products in a given sub-category chosen
    by the user."""
    template_name = 'grocerystore/instock.html'

    def get(self, request, zipcode, store_id, category_id, subcategory_id):
        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.", fail_silently=True)
            return redirect('grocerystore:index')

        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        try: # check if the chosen store delivers the chosen zipcode
            zipcode_obj = Zipcode.objects.get(zipcode=int(zipcode))
            if zipcode_obj not in store.delivery_area.all():
                messages.error(self.request, "The store you're looking for doesn't "\
                                             "deliver in the area you've chosen.", fail_silently=True)
                return redirect('grocerystore:start', zipcode=zipcode)
        except: # check if there're stores available in the chosen zipcode
            messages.error(self.request, "There's no store available in the area "\
                                         "you've chosen.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        try: # check if the category_id does exist
            category = ProductCategory.objects.get(pk=category_id)
        except:
            messages.error(self.request, "Sorry, the requested category doesn't exist.", fail_silently=True)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
        try: # check if the subcategory_id does exist
            subcategory = ProductSubCategory.objects.get(pk=subcategory_id)
            if subcategory.parent != category:
                messages.error(self.request, "Sorry, the requested sub-category doesn't exist)", fail_silently=True)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
        except:
            messages.error(self.request, "Sorry, the requested sub-category doesn't exist.", fail_silently=True)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        context = {}
        context['zipcode'] = zipcode
        context['subcategory'] = ProductSubCategory.objects.get(pk=int(subcategory_id))
        context['store_id'] = store_id
        context['store'] = store
        context['category_id'] = category_id
        context['quantity_set'] = range(1, 21)

        available_products = Availability.objects.filter(store__pk=int(store_id))\
                             .filter(product__product_category__pk=int(subcategory_id))
        context['available_products'] = available_products

        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if len(available_stores) > 0:
            context['available_stores'] = available_stores

        return render(self.request, self.template_name, context=context)

    def post(self, request, zipcode, store_id, category_id, subcategory_id):
        try:
            searched_item = self.request.POST.get('search')
            if searched_item.replace(" ", "").replace("-", "").isalpha():
                return redirect('grocerystore:search', zipcode=zipcode,
                                                       store_id=store_id,
                                                       searched_item=urllib.quote(searched_item.encode('utf8')))
            else:
                messages.error(self.request, "You must enter only alphabetical characters", fail_silently=True)
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
                    item.incart_quantity += quantity_to_add
                    item.save()
                    messages.success(self.request, "'%s' quantity successfully updated."\
                                                % availability.product, fail_silently=True)
                # create an ItemInCart instance if the item isn't in the
                # database, and save it in the database
                except:
                    ItemInCart.objects.create(incart_user=self.request.user,
                                              incart_availability=availability,
                                              incart_quantity=quantity_to_add)

                    messages.success(self.request, "'%s' successfully added in your cart."\
                                                % availability.product, fail_silently=True)

                messages.info(self.request, "%s" % Store.objects.get(pk=store_id), fail_silently=True)
                return redirect('grocerystore:instock', zipcode=zipcode,
                                                        store_id=store_id,
                                                        category_id=category_id,
                                                        subcategory_id=subcategory_id)

            else: # if the user isn't authenticated
                try: # check if the item is already in the user's cart
                    new_qty = self.request.session[str(availability.pk)]['qty'] + quantity_to_add
                    self.request.session[str(availability.pk)] = {'name': str(availability.pk), 'qty': new_qty}
                    messages.success(self.request, "'%s' quantity successfully updated."\
                                                % availability.product, fail_silently=True)
                except:
                    self.request.session[str(availability.pk)] = {'name': str(availability.pk), 'qty': quantity_to_add}
                    messages.success(self.request, "'%s' successfully added in your cart."\
                                                % availability.product, fail_silently=True)

                messages.info(self.request, "%s" % Store.objects.get(pk=store_id), fail_silently=True)
                return redirect('grocerystore:instock', zipcode=zipcode,
                                                        store_id=store_id,
                                                        category_id=category_id,
                                                        subcategory_id=subcategory_id)


class BuyAgainView(LoginRequiredMixin, View):
    """This page lists all the available products in a given store that the user
    (who must be authenticated) has bought at least once in this store."""
    template_name = 'grocerystore/buyagain.html'
    login_url = 'grocerystore:login'
    redirect_field_name = 'redirect_to'

    def get(self, request, zipcode, store_id):
        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.", fail_silently=True)
            return redirect('grocerystore:index')

        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        try: # check if the chosen store delivers the chosen zipcode
            zipcode_obj = Zipcode.objects.get(zipcode=int(zipcode))
            if zipcode_obj not in store.delivery_area.all():
                messages.error(self.request, "The store you're looking for doesn't "\
                                             "deliver in the area you've chosen.", fail_silently=True)
                return redirect('grocerystore:start', zipcode=zipcode)
        except: # if there aren't any stores that deliver the chosen zipcode area
            messages.error(self.request, "There's no store available in the area "\
                                         "you've chosen.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        user = self.request.user
        context = {}
        context['zipcode'] = zipcode
        context['store_id'] = store_id
        context['store'] = store
        context['quantity_set'] = range(1, 21)

        available_here = []
        try:
            bought_here = ProductPurchase.objects.filter(customer=user)\
                           .filter(purchase_store=store)
            # keep only the available products already bought in this store
            for item in bought_here:
                try:
                    available_here.append(Availability.objects.filter(store=store)\
                    .get(product=item.bought_product))
                except: continue
        except: pass # if the user has never placed any order in this store

        if available_here:
            context['available_products'] = available_here

        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if len(available_stores) > 0:
            context['available_stores'] = available_stores

        return render(self.request, self.template_name, context=context)

    def post(self, request, zipcode, store_id):
        user = self.request.user
        store = Store.objects.get(pk=store_id)
        try:
            searched_item = self.request.POST.get('search')
            if searched_item.replace(" ", "").replace("-", "").isalpha():
                return redirect('grocerystore:search', zipcode=zipcode,
                                                       store_id=store_id,
                                                       searched_item=urllib.quote(searched_item.encode('utf8')))
            else:
                messages.error(self.request, "You must enter only alphabetical characters", fail_silently=True)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        except: pass # if the user doesn't use the search tool

        # get list of the products bought by the user in this specific store
        bought_here = ProductPurchase.objects.filter(customer=user).filter(purchase_store=store)

        # filter the available products
        available_here = []
        for item in bought_here:
            try:
                available_here.append(Availability.objects.filter(store=store)\
                .get(product=item.bought_product))
            except: continue

        for availability in available_here: # list of Availability instances
            try:
                quantity_to_add = int(self.request.POST.get(str(availability.pk)))
            except TypeError:
                continue

            try:
                item = ItemInCart.objects.filter(incart_user=user)\
                       .get(incart_availability=availability)
                item.incart_quantity += quantity_to_add
                item.save()
                messages.success(self.request, "'%s' quantity successfully updated" \
                                 % availability.product, fail_silently=True)

            # create an ItemInCart instance if the item isn't in the
            # cart, and save it in the database
            except:
                ItemInCart.objects.create(incart_user=user,
                                          incart_availability=availability,
                                          incart_quantity=quantity_to_add)

                messages.success(self.request, "'%s' successfully added in your cart."\
                                 % availability.product, fail_silently=True)

            messages.info(self.request, "%s" % Store.objects.get(pk=store_id), fail_silently=True)
            return redirect('grocerystore:buyagain', zipcode=zipcode,
                                                     store_id=store_id)


class SearchView(View):
    """Display a list of available products (in a given store) after the user
    uses the search tool in the navigation menu bar.
    This view uses the search_item function."""
    template_name = 'grocerystore/search.html'

    def get(self, request, zipcode, store_id, searched_item):
        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.", fail_silently=True)
            return redirect('grocerystore:index')

        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        try: # check if the chosen store delivers the chosen zipcode
            zipcode_obj = Zipcode.objects.get(zipcode=int(zipcode))
            if zipcode_obj not in store.delivery_area.all():
                messages.error(self.request, "The store you're looking for doesn't "\
                                             "deliver in the area you've chosen.", fail_silently=True)
                return redirect('grocerystore:start', zipcode=zipcode)
        except: # if there aren't any stores that deliver the chosen zipcode area
            messages.error(self.request, "There's no store available in the area "\
                                         "you've chosen.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        context = {'quantity_set': range(1, 21),
                  'zipcode': zipcode,
                  'store_id': store_id,
                  'store': store,
                  'searched_item': searched_item}

        available_stores = Store.objects.filter(delivery_area__zipcode=int(zipcode))
        if len(available_stores) > 0:
            context['available_stores'] = available_stores

        searched_item = urllib.unquote(searched_item)
        search_result = search_item(searched_item, store_id)

        if len(search_result) > 30:
            messages.error(self.request, "too many items match your research, "\
                           "please be more specific.", fail_silently=True)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        elif len(search_result) > 0:
            available_products = []
            for availability in search_result: # NB: availablity is an Availability instance
                product_price = float(availability.product_price)
                product_unit = availability.product_unit
                product_id = availability.product.pk
                available_products.append([availability, product_price, product_unit, product_id])

            context['available_products'] = available_products

            return render(self.request, self.template_name, context=context)

        else: # in case the search result is empty, search in other stores in the same zipcode area
            search_result = []
            stores_around = Store.objects.filter(delivery_area=zipcode_obj).exclude(pk=store_id)
            for help_store in stores_around:
                search_result.extend(search_item(searched_item, help_store.pk))

            if search_result:
                other_availabilities = []
                for availability in search_result: # NB: availablity is an Availability instance
                    product_price = float(availability.product_price)
                    product_unit = availability.product_unit
                    product_id = availability.product.pk
                    product_store = availability.store
                    product_store_id = product_store.pk
                    other_availabilities.append([availability, product_price, product_unit,
                                               product_id, product_store, product_store_id])

                context['other_availabilities'] = other_availabilities
                return render(self.request, self.template_name, context=context)

            else:
                messages.error(self.request, "unfortunately no available item matches your research at %s" \
                              % store, fail_silently=True)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

    def post(self, request, zipcode, store_id, searched_item):
        """When an item is added to the user cart, its "name" is the
        corresponding Availability object pk turned into a string"""
        try: # in case the user uses the search tool in the navigation bar
            new_searched_item = self.request.POST.get('search')
            if new_searched_item.replace(" ", "").replace("-", "").isalpha():
                return redirect('grocerystore:search', zipcode=zipcode,
                                                       store_id=store_id,
                                                       searched_item=urllib.quote(new_searched_item.encode('utf8')))
            else:
                messages.error(self.request, "You must enter only alphabetical characters", fail_silently=True)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)
        except: pass

        # if the user wants to add one of the displayed products in their cart
        searched_item = urllib.unquote(searched_item)
        search_result = search_item(searched_item, store_id)

        if not search_result: # ie. there're results in other stores that deliver the same zipcode area
            zipcode_obj = Zipcode.objects.get(zipcode=int(zipcode))
            search_result = []
            stores_around = Store.objects.filter(delivery_area=zipcode_obj).exclude(pk=store_id)
            for store in stores_around:
                search_result.extend(search_item(searched_item, store.pk))

            for result in search_result:
                try:
                    self.request.POST.get(str(result.pk))
                except: continue

                new_store = result.store
                messages.warning(self.request, "You're now shopping at %s." % new_store, fail_silently=True)
                return HttpResponseRedirect(reverse('grocerystore:detail', kwargs={
                                                    'zipcode': zipcode,
                                                    'store_id': new_store.pk,
                                                    'product_id': result.product.pk,}) \
                                                    + '?go_back=' + str(store_id)\
                                                    + '&searched_item=' + str(urllib.quote(searched_item.encode('utf8'))))

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
                    messages.success(self.request, "'%s' quantity successfully updated."\
                                                % availability.product, fail_silently=True)
                # create an ItemInCart instance if the item isn't in the
                # database, and save it in the database
                except:
                    ItemInCart.objects.create(incart_user=self.request.user,
                                              incart_availability=availability,
                                              incart_quantity=quantity_to_add)
                    messages.success(self.request, "'%s' successfully added in your cart" \
                                     % availability.product, fail_silently=True)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        else: # if the user is anonymous
            for availability in search_result:
                try:
                    quantity_to_add = int(self.request.POST.get(str(availability.pk)))
                except TypeError:
                    continue

                # once the quantity_to_add has been catched
                try: # check if the item is already in the user's cart
                    new_qty = self.request.session[str(availability.pk)]['qty'] + quantity_to_add
                    self.request.session[str(availability.pk)] = {'name': str(availability.pk), 'qty': new_qty}
                    messages.success(self.request, "'%s' quantity successfully updated."\
                                     % availability.product, fail_silently=True)
                except:
                    self.request.session[str(availability.pk)] = {'name': str(availability.pk), 'qty': quantity_to_add}
                    messages.success(self.request, "'%s' successfully added in your cart."\
                                     % availability.product, fail_silently=True)

                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        # in case the product the user wants to put in their cart isn't available anymore
        # (eg: if the product availability was removed while the user was looking at the page)
        return redirect('grocerystore:search', zipcode=zipcode, store_id=store_id)


class ProductDetailView(View):
    """Display all the details about a given item, including other availabilities
    in other stores in the same zip code area."""
    template_name = 'grocerystore/detail.html'

    def get(self, request, zipcode, store_id, product_id):
        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.", fail_silently=True)
            return redirect('grocerystore:index')

        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        try: # check if the chosen store delivers the chosen zipcode
            zipcode_obj = Zipcode.objects.get(zipcode=int(zipcode))
            if zipcode_obj not in store.delivery_area.all():
                messages.error(self.request, "The store you're looking for doesn't "\
                                             "deliver in the area you've chosen.", fail_silently=True)
                return redirect('grocerystore:start', zipcode=zipcode)
        except: # if there aren't any stores that deliver the chosen zipcode area
            messages.error(self.request, "There's no store available in the area "\
                                         "you've chosen.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        try: # check if the product_id does exist
            product = Product.objects.get(pk=product_id)
        except:
            messages.error(self.request, "Sorry, the requested product doesn't exist.", fail_silently=True)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        try: # check if the product is available in the chosen store
            product_availability = Availability.objects.filter(product=product).get(store=store)
        except:
            messages.error(self.request, "Sorry, the requested product isn't available in "\
                           "the store you've chosen.", fail_silently=True)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        context = {}
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
        try:
            context['go_back'] = int(self.request.GET['go_back']) # this is a store pk
            context['searched_item'] = self.request.GET['searched_item']
        except: pass

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
                return redirect('grocerystore:search', zipcode=zipcode,
                                                       store_id=store_id,
                                                       searched_item=urllib.quote(searched_item.encode('utf8')))
            else:
                messages.error(self.request, "You must enter only alphabetical characters", fail_silently=True)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        store = Store.objects.get(pk=store_id)
        product = Product.objects.get(pk=product_id)
        availability = Availability.objects.filter(store=store).get(product=product)

        if self.request.user.is_authenticated:
            # check if the item is already in the cart and update its quantity
            try:
                item = ItemInCart.objects.filter(incart_user=self.request.user)\
                       .get(incart_availability=availability)
                item.incart_quantity += quantity_to_add
                item.save()
                messages.success(self.request, "'%s' quantity successfully updated" \
                                 % product, fail_silently=True)
            # create an ItemInCart instance if the item isn't in the
            # database, and save it in the database
            except:
                ItemInCart.objects.create(incart_user=self.request.user,
                                          incart_availability=availability,
                                          incart_quantity=quantity_to_add)
                messages.success(self.request, "'%s' successfully added in your cart" % product, fail_silently=True)
            try:
                go_back_to = self.request.GET['go_back']
                messages.info(self.request, "Go back to %s" % Store.objects.get(pk=int(go_back_to)), fail_silently=True)
                messages.info(self.request, "Keep shopping at %s" % store, fail_silently=True)
                return HttpResponseRedirect(reverse('grocerystore:detail', kwargs={
                                                    'zipcode': zipcode,
                                                    'store_id': store_id,
                                                    'product_id': product_id,}) \
                                                    + '?go_back=' + str(go_back_to))
            except:
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        else: # if the user is anonymous
            try: # check if the item is already in the user's cart
                new_qty = self.request.session[str(availability.pk)]['qty'] + quantity_to_add
                self.request.session[str(availability.pk)] = {'name': str(availability.pk), 'qty': new_qty}
                messages.success(self.request, "'%s' quantity successfully updated."\
                                                % product, fail_silently=True)
            except:
                self.request.session[str(availability.pk)] = {'name': str(availability.pk), 'qty': quantity_to_add}
                messages.success(self.request, "'%s' successfully added in your cart."\
                                                % product, fail_silently=True)
            try:
                go_back_to = self.request.GET['go_back']
                messages.info(self.request, "Go back to %s" % Store.objects.get(pk=int(go_back_to)), fail_silently=True)
                messages.info(self.request, "Keep shopping at %s" % store, fail_silently=True)
                return HttpResponseRedirect(reverse('grocerystore:detail', kwargs={
                                                    'zipcode': zipcode,
                                                    'store_id': store_id,
                                                    'product_id': product_id,}) \
                                                    + '?go_back=' + str(go_back_to))
            except:
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)


class CartView(View):
    """Display the user's cart(s), ie. everything they've shopped in different
    stores and different zip code areas (if the user is authenticated, this
    includes their carts in stores that may not deliver their home address)."""
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
            messages.error(self.request, "You are looking for an invalid zipcode.", fail_silently=True)
            return redirect('grocerystore:index')

        if self.request.user.is_authenticated:
            user_zipcode = Inflauser.objects.get(infla_user=self.request.user).inflauser_address.zip_code
            context['username'] = self.request.user.username
            context['user_zipcode'] = user_zipcode
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
                       item_availability.pk, item_product.pk, item_availability.product_price,
                       item_availability.store.store_zipcode]
                item_store = item_availability.store

                try:
                    all_carts[item_store].append(elt)
                except KeyError:
                    all_carts[item_store] = [elt]

            if all_carts:
                for store, cart in all_carts.items(): # cart is a list of elts (elts are lists too)
                    cart_total = 0
                    for elt in cart:
                        cart_total += float(elt[3]) # elt[3]=item_price

                    if cart_total < 30:
                        cart.append('delivery_fee')
                    else:
                        cart.append('no_delivery_fee')

                    # True is for a store that delivers the user's address
                    if store.delivery_area.all().filter(zipcode=user_zipcode):
                        cart.append('delivery')
                    else:
                        cart.append('pickup')

                    cart.append("%.2f" % cart_total)

                context['all_carts'] = all_carts
                context['quantity_set'] = range(21)

            else:
                try: # the zip code area where the user is shopping (which may not
                     # be an area where delivery is available)
                    context['area'] = Zipcode.objects.get(zipcode=int(zipcode))
                except: pass

            return render(self.request, self.template_name, context=context)

        else: # if the user is anonymous
            available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
            if len(available_stores) > 0:
                context['available_stores'] = available_stores

            for item in self.request.session.keys():
                item_availability_pk = int(self.request.session[item]['name'])
                item_availability = Availability.objects.get(pk=item_availability_pk)
                item_store = item_availability.store
                item_product = item_availability.product
                item_price = "%.2f" % (float(self.request.session[item]["qty"])\
                * float(item_availability.product_price))
                elt = [item_product, self.request.session[item]["qty"],
                       item_availability.product_unit, item_price,
                       item_availability_pk, item_product.pk, item_availability.product_price,
                       item_availability.store.store_zipcode]

                try:
                    all_carts[item_store].append(elt)
                except KeyError:
                    all_carts[item_store] = [elt]

            if all_carts:
                for store, cart in all_carts.items():
                    cart_total = 0

                    for elt in cart:
                        cart_total += float(elt[3])

                    if cart_total < 30:
                        cart.append('delivery_fee')
                    else:
                        cart.append('no_delivery_fee')

                    # True is for a store that delivers the current zipcode area
                    if store.delivery_area.all().filter(zipcode=zipcode):
                        cart.append('delivery')
                    else:
                        cart.append('pickup')

                    cart.append("%.2f" % cart_total)

                context['all_carts'] = all_carts
                context['quantity_set'] = range(21)

            else: # if the anonymous user hasn't put anything in their cart
                try:
                    context['area'] = Zipcode.objects.get(zipcode=zipcode)
                except: pass

            return render(self.request, self.template_name, context=context)

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
                        messages.success(self.request, "You've just emptied your cart at %s."\
                        % Store.objects.get(pk=i), fail_silently=True)
                    return redirect('grocerystore:cart', zipcode=zipcode)
                except:
                    continue

            for i in store_pks: # if the user wants to checkout in a given store
                try:
                    if self.request.POST['checkout '+str(i)]:
                        return redirect('grocerystore:checkout', zipcode=Store.objects.get(pk=i).store_zipcode, store_id=i)
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

            for i in store_pks: # if the user wants to checkout in a given store
                try:
                    if self.request.POST['checkout '+str(i)]:
                        return redirect('grocerystore:checkout', zipcode=Store.objects.get(pk=i).store_zipcode, store_id=i)
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
    """Last page where the user can check their cart before placing their order;
    the user enters their credit card info and chooses a delivery time (if delivery
    is available - otherwise they're given the location where they can pick up
    their order and when)."""
    form_class = PaymentForm
    template_name = 'grocerystore/checkout.html'
    login_url = 'grocerystore:login'
    redirect_field_name = 'redirect_to'

    def get(self, request, zipcode, store_id):
        # if the user enters an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.", fail_silently=True)
            return redirect('grocerystore:index')

        try:
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the store you want to check "\
                                         "out from doesn't exist.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        user_cart = ItemInCart.objects.filter(incart_user=self.request.user)
        if not user_cart: # if the user's cart is totally empty
            messages.error(self.request, "You need to put items in your cart to checkout!", fail_silently=True)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        context = {'zipcode': zipcode,
                   'store_id': store_id,
                   'store': store,
                   'username': self.request.user.username,
                   'payment_form': self.form_class(None)}

        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if available_stores:
            context['available_stores'] = available_stores

        cart_total = float(0)
        in_cart = []
        sales_tax = float(0.00)
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
                if product.taxability:
                    # NB: need to use a sales tax API in real life ;-)
                    # 8.5% is the sales tax rate in San Francisco county
                    sales_tax += float(float(item_price) * float(quantity) * 8.5 / 100)
                elt = [product, quantity, item_price, item_unit, item_total]
                in_cart.append(elt)

        if float(cart_total) == 0.00:
            messages.error(self.request, "You must put items in your cart to be able "\
                                         "to place an order!", fail_silently=True)
            return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        # calculating service fee before adding sales taxes
        service = float(cart_total * 0.10)
        cart_total += service
        context['service'] = "%.2f" % service

        # adding sales taxes (if applicable)
        if sales_tax > float(0.00):
            cart_total += sales_tax
            context['sales_tax'] = "%.2f" % sales_tax

        now = datetime.now()

        try: # check wether the customer can be delivered or not, and if they heve
             # to pay a delivery fee or not
            user_zipcode = Zipcode.objects.get(zipcode=self.request.user.inflauser.inflauser_address.zip_code)
            if cart_total < 30 and user_zipcode in store.delivery_area.all():
                cart_total += 5.00
                context['delivery_fee'] = True
            elif user_zipcode not in store.delivery_area.all():
                # if the user's address can't be delivered by the store they're checking out at
                one_day_delta = timedelta(hours=24)
                deadline = now + one_day_delta
                context['pickup'] = True
                context['deadline'] = deadline
        except: # if the user's address zip code cant't be delivered by any store
            one_day_delta = timedelta(hours=24)
            deadline = now + one_day_delta
            context['pickup'] = True
            context['deadline'] = deadline

        context['cart_total'] = "%.2f" % cart_total
        context['in_cart'] = in_cart

        today = str(now.month) + "/" + str(now.day)
        tomorrow = str((now.today() + timedelta(days=1)).month) + "/" + str((now.today() + timedelta(days=1)).day)
        if now.hour >= 19 and now.hour < 24:
            delivery_time_set = ["tomorrow %s, 11am-1pm" % tomorrow, "tomorrow %s, 1pm-3pm" % tomorrow, "tomorrow %s, 3pm-5pm" % tomorrow, "tomorrow %s, 5pm-8pm" % tomorrow]
        elif now.hour >= 18:
            delivery_time_set = ["today %s, 7pm-9pm" % today, "tomorrow %s, 11am-1pm" % tomorrow, "tomorrow %s, 1pm-3pm" % tomorrow, "tomorrow %s, 3pm-5pm" % tomorrow]
        elif now.hour >= 17:
            delivery_time_set = ["today %s, 6pm-8pm" % today, "tomorrow %s, 11am-1pm" % tomorrow, "tomorrow %s, 1pm-3pm" % tomorrow, "tomorrow %s, 3pm-5pm" % tomorrow]
        elif now.hour >= 16:
            delivery_time_set = ["today %s, 5pm-7pm" % today, "today %s, 7pm-9pm" % today, "tomorrow %s, 11am-1pm" % tomorrow, "tomorrow %s, 1pm-3pm" % tomorrow]
        elif now.hour >= 15:
            delivery_time_set = ["today %s, 4pm-6pm" % today, "today %s, 6pm-8pm" % today, "tomorrow %s, 11am-1pm" % tomorrow, "tomorrow %s, 1pm-3pm" % tomorrow]
        elif now.hour >= 14:
            delivery_time_set = ["today %s, 3pm-5pm" % today, "today %s, 5pm-7pm" % today, "today %s, 7pm-9pm" % today, "tomorrow %s, 11am-1pm" % tomorrow]
        elif now.hour >= 13:
            delivery_time_set = ["today %s, 2pm-4pm" % today, "today %s, 4pm-6pm" % today, "today %s, 6pm-8pm" % today, "tomorrow %s, 11am-1pm" % tomorrow]
        elif now.hour >= 12:
            delivery_time_set = ["today %s, 1pm-3pm" % today, "today %s, 3pm-5pm" % today, "today %s, 5pm-7pm" % today, "today %s, 7pm-9pm" % today]
        elif now.hour >= 11:
            delivery_time_set = ["today %s, noon-2pm" % today, "today %s, 2pm-4pm" % today, "today %s, 4pm-6pm" % today, "today %s, 6pm-8pm" % today]
        else:
            delivery_time_set = ["today %s, 11am-1pm" % today, "today %s, 1pm-3pm" % today, "today %s, 3pm-5pm" % today, "today %s, 5pm-7pm" % today]

        context['delivery_time_set'] = delivery_time_set

        return render(self.request, self.template_name, context=context)

    def post(self, request, zipcode, store_id):
        """Empty the cart, store order data in the db, and redirect to the index
        page. NB: this is a virtual checkout!"""
        try:
            searched_item = self.request.POST.get('search')
            if searched_item.replace(" ", "").replace("-", "").isalpha():
                return redirect('grocerystore:search', zipcode=zipcode,
                                                       store_id=store_id,
                                                       searched_item=urllib.quote(searched_item.encode('utf8')))
            else:
                messages.error(self.request, "You must enter only alphabetical characters", fail_silently=True)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        except: pass

        store = Store.objects.get(pk=store_id)
        try:
            user_zipcode = Zipcode.objects.get(zipcode=self.request.user.inflauser.inflauser_address.zip_code)
            if user_zipcode in store.delivery_area.all():
                try:
                    delivery_time = self.request.POST['delivery_time']
                except:
                    messages.error(self.request, "Please select a delivery time.", fail_silently=True)
                    return redirect('grocerystore:checkout', zipcode=zipcode, store_id=store_id)
            else:
                delivery_time = "pick up"
        except:
            delivery_time = "pick up"

        payment_data = self.form_class(self.request.POST)

        if payment_data.is_valid() and not delivery_time == "--- Choose a delivery time ---":
            # would normally require money transfer from the user's bank
            # and to send purchased items list and user's address to delivery company
            user_cart = ItemInCart.objects.filter(incart_user=self.request.user)
            user = self.request.user
            user_address = Inflauser.objects.get(infla_user=user).inflauser_address
            store = Store.objects.get(pk=store_id)
            order_total = 0.00

            for item in user_cart:
                if item.incart_availability.store.pk == int(store_id):
                    try: # NB: a picture isn't JSON serializable
                        order_data['items'].append({
                            'product_pk': item.incart_availability.product.pk,
                            'availability_pk': item.incart_availability.pk,
                            'product_name': item.incart_availability.product.product_name,
                            'unit_price': str(item.incart_availability.product_price), # float and decimal types aren't JSON serializable
                            'product_qty': item.incart_quantity,
                            'total_item_price': "%.2f" % (float(item.incart_availability.product_price) * item.incart_quantity),
                            'product_unit': item.incart_availability.product_unit,
                            })
                        order_total += float(item.incart_availability.product_price) * item.incart_quantity
                    except: # if order_data hasn't been declared yet, ie. it's the first loop of the iteration
                        # a datetime.datetime object isn't JSON serializable
                        purchase_date = []
                        purchase_date.append(datetime.now().year)
                        purchase_date.append(datetime.now().month)
                        purchase_date.append(datetime.now().day)
                        purchase_date.append(datetime.now().hour)
                        purchase_date.append(datetime.now().second)
                        order_data = {
                        'purchase_date': purchase_date,
                        'order_nb': "",
                        'order_total': "",
                        'delivery_time': delivery_time,
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
                            'availability_pk': item.incart_availability.pk,
                            'product_name': item.incart_availability.product.product_name,
                            'unit_price': str(item.incart_availability.product_price), # float and decimal types aren't JSON serializable
                            'product_qty': item.incart_quantity,
                            'total_item_price': "%.2f" % (float(item.incart_availability.product_price) * item.incart_quantity),
                            'product_unit': item.incart_availability.product_unit,
                            }],
                        }
                        order_total += float(item.incart_availability.product_price) * item.incart_quantity

                    try:
                        item_history = ProductPurchase.objects.filter(customer=user)\
                                       .get(bought_product=item.incart_availability.product)
                        item_history.purchase_dates.append(datetime.now())
                        item_history.nb_of_purchases += 1
                        item_history.save()
                    except ProductPurchase.DoesNotExist:
                        ProductPurchase.objects.create(customer=user,
                                                       bought_product=item.incart_availability.product,
                                                       purchase_store=store,
                                                       purchase_dates=[datetime.now()])
                    item.delete()

            order = Order.objects.create(data=order_data)
            order.data['order_nb'] = int(10000 + order.pk)
            order.data['order_total'] = "%.2f" % order_total
            order.save()
            messages.info(self.request, "Congratulations for your virtual purchase!", fail_silently=True)
            return redirect('grocerystore:index')

        messages.error(self.request, "Please make sure you enter valid credit cart information.", fail_silently=True)
        return redirect('grocerystore:checkout', zipcode=zipcode, store_id=store_id)


class OrdersHistory(LoginRequiredMixin, View):
    """List all the previous orders that the (authenticated) user has placed in
    this store, and allow them to replace an entire order."""
    template_name = 'grocerystore/orders.html'
    login_url = 'grocerystore:login'
    redirect_field_name = 'redirect_to'

    def get(self, request, zipcode, store_id):
        # if the user types an invalid zipcode directly in the browser
        if len(zipcode) > 5 or len(zipcode) < 4 or not zipcode.isnumeric():
            messages.error(self.request, "You are looking for an invalid zipcode.", fail_silently=True)
            return redirect('grocerystore:index')

        try: # check if the store_id does exist
            store = Store.objects.get(pk=store_id)
        except:
            messages.error(self.request, "Sorry, the requested store doesn't exist.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        try: # check if the chosen store delivers the chosen zipcode
            zipcode_obj = Zipcode.objects.get(zipcode=int(zipcode))
            if zipcode_obj not in store.delivery_area.all():
                messages.error(self.request, "The store you're looking for doesn't "\
                                             "deliver in the area you've chosen.", fail_silently=True)
                return redirect('grocerystore:start', zipcode=zipcode)
        except: # if there aren't any stores that deliver the chosen zipcode area
            messages.error(self.request, "There's no store available in the area "\
                                         "you've chosen.", fail_silently=True)
            return redirect('grocerystore:start', zipcode=zipcode)

        user = self.request.user
        context = {
            'user': user,
            'store_id': store_id,
            'store': Store.objects.get(pk=store_id),
            'zipcode': zipcode,
            'quantity_set': range(1, 21),
        }

        user_orders = Order.objects.filter(data__user__user_pk=user.pk)\
                      .filter(data__store__store_pk=store_id)

        if user_orders:
            for order in user_orders:
                for product in order.data['items']:
                    product['product_pic'] = Product.objects.get(pk=int(product['product_pk'])).product_pic
            context['user_orders'] = user_orders

        available_stores = Store.objects.filter(delivery_area__zipcode=zipcode)
        if available_stores:
            context['available_stores'] = available_stores

        return render(self.request, self.template_name, context=context)

    def post(self, request, zipcode, store_id):

        try: # in case the user uses the search tool in the navigation menu
            searched_item = self.request.POST.get('search')
            if searched_item.replace(" ", "").replace("-", "").isalpha():
                return redirect('grocerystore:search', zipcode=zipcode,
                                                       store_id=store_id,
                                                       searched_item=urllib.quote(searched_item.encode('utf8')))
            else:
                messages.error(self.request, "You must enter only alphabetical characters", fail_silently=True)
                return redirect('grocerystore:store', zipcode=zipcode, store_id=store_id)

        except: pass

        user = self.request.user
        user_orders = Order.objects.filter(data__user__user_pk=user.pk)\
                      .filter(data__store__store_pk=store_id)

        for order in user_orders:
            try:
                self.request.POST['everything '+str(order.pk)]
                items_added = False
                unavailable_items = []
                for elt in order.data['items']:
                    try:
                        availability = Availability.objects.get(pk=elt['availability_pk'])
                    except Availability.DoesNotExist:
                        unavailable_items.append(elt['product_name'])
                        continue
                    try:
                        item = ItemInCart.objects.filter(incart_user=user)\
                               .get(incart_availability=availability)
                        item.incart_quantity += int(elt['product_qty'])
                        item.save()
                        items_added = True
                    except:
                        ItemInCart.objects.create(incart_user=user,
                                                  incart_availability=availability,
                                                  incart_quantity=int(elt['product_qty']))
                        items_added = True

                if items_added and not unavailable_items:
                    messages.success(self.request, "All the items of your previous order have been put in your cart.", fail_silently=True)
                elif items_added and unavailable_items:
                    messages.success(self.request, "The available items of your previous order have been put in your cart.", fail_silently=True)
                    unavailable = ""
                    for elt in unavailable_items[:-1]:
                        unavailable += (str(elt) + ", ")
                    unavailable += str(unavailable_items[-1])
                    messages.error(self.request, "The following item(s) aren't available anymore at %s: %s"\
                                                 % (order.data['store']['store_name'], unavailable), fail_silently=True)
                else:
                    messages.error(self.request, "Sorry, the item(s) of your previous order aren't available anymore at %s" \
                                   % order.data['store']['store_name'], fail_silently=True)
                messages.info(self.request, "%s" % Store.objects.get(pk=store_id), fail_silently=True)
                return redirect('grocerystore:orders', zipcode=zipcode, store_id=store_id)

            except:
                for elt in order.data['items']:
                    try:
                        quantity_to_add = int(self.request.POST.get(str(elt['availability_pk'])))
                    except: continue

                    try:
                        availability = Availability.objects.get(pk=elt['availability_pk'])
                    except Availability.DoesNotExist:
                        messages.error(self.request, "Sorry, %s isn't available anymore at %s" \
                        % (elt['product_name'], order.data['store']['store_name']), fail_silently=True)
                        return redirect('grocerystore:orders', zipcode=zipcode, store_id=store_id)

                    try: # if the item is in stock in the store and if it's already in the user's cart
                        item = ItemInCart.objects.filter(incart_user=user)\
                               .get(incart_availability=availability)
                        item.incart_quantity += quantity_to_add
                        item.save()
                        messages.success(self.request, "'%s' quantity successfully updated" \
                        % item.incart_availability.product, fail_silently=True)
                        messages.info(self.request, "%s" % Store.objects.get(pk=store_id), fail_silently=True)

                    except:
                        item = ItemInCart.objects.create(incart_user=user,
                                                         incart_availability=availability,
                                                         incart_quantity=quantity_to_add)
                        messages.success(self.request, "'%s' successfully added in your cart" \
                                         % item.incart_availability.product, fail_silently=True)
                        messages.info(self.request, "%s" % Store.objects.get(pk=store_id), fail_silently=True)

                    return redirect('grocerystore:orders', zipcode=zipcode, store_id=store_id)
