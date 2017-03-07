#-*- coding: UTF-8 -*-
import os
import sys
import json
import requests
import urllib

"""
This module contains the class whose instances are used as intermediates by the
application program interface (API) created with Django framework to
communicate with the Flask HTTP server.

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
