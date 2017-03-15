#-*- coding: UTF-8 -*-
import os
import sys
import json
import requests
import urllib
from .models import Availability, Store

"""
This module contains:

- InflaskartClient: the class whose instances are used as intermediates by the
application program interface (API) created with Django framework to
communicate with the cart server;

- search_item(): function used in SearchView and StoreView in views.py;

- get_flaskcart(): function used in UserRegisterView, UserLoginView, SearchView,
InstockList, ProductDetailView, CartView, CheckoutView, and StoreView in views.py;

- remove_old_items(): function used in UserRegisterView and UserLoginView 
in views.py;

"""


class InflaskartClient:
    """
    Its instances have 2 attributes: url and user.

    This class contains 4 methods:
    - list()
    - add()
    - delete()
    - empty_cart()

    NB : a cart JSON-decoded looks like: {'items': [{"name": "x", "qty": y}, ]}

    """

    def __init__(self, url, user):
        self.url = url
        self.user = user

    def __str__(self):
        cart = self.list()['items']
        return cart

    def __repr__(self):
        cart = self.list()['items']
        return cart

    def list(self):
        """Return the cart JSON-decoded."""
        r = requests.get(self.url) # r (for 'response') is a JSON object
        cart = r.json() # json() is a built-in JSON decoder that comes with the requests module
        return cart

    def add(self, item, qty):
        """Add an item in the cart and return the cart JSON-decoded."""
        url = os.path.join(self.url,'product', item)
        payload = {'qty': qty}
        r = requests.put(url, json=payload) # or: r = requests.put(url, data=json.dumps(payload))
        cart = r.json()
        return cart

    def delete(self, item):
        """Delete an item from the cart and return the cart JSON-decoded."""
        url = os.path.join(self.url,'product', item)
        r = requests.delete(url)
        cart = r.json()
        return cart

    def empty_cart(self):
        """Empty the cart and return the cart JSON-decoded."""
        items_in_cart = self.list()['items']
        for item in items_in_cart:
            url = os.path.join(self.url,'product', item["name"])
            r = requests.delete(url)
        cart = r.json()
        return cart


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


def get_flaskcart(username, cart_host):
    """Returns an instance of the InflaskartClient class whose username is the
    one passed in as a parameter"""
    username_encoded = urllib.quote(urllib.quote(username))
    flask_cart_url = os.path.join(cart_host, username_encoded)
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
