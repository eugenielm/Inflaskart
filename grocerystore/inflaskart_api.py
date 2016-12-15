#-*- coding: UTF-8 -*-
import os
import sys
import json
import requests
import urllib

class InflaskartClient:
    """Class whose instances are used by the infla-client.py script to send HTTP
    requests to inflaskart.py"""

    def __init__(self, url, user):
        self.url = url
        self.user = user

    # def __repr__(self):
    #     cart = self.list()
    #     pretty = ["Here is %s's cart: " % self.user]
    #     for i, elt in enumerate(cart["items"]):
    #         line = "item %d: " % (i+1) + "%s, " % elt["name"]\
    #                + "quantity: %s" % elt["qty"]
    #         pretty.append(line)
    #     lines = '\n'.join(pretty)
    #     return lines

    def __repr__(self):
        cart = self.list()
        in_cart = []
        for elt in cart["items"]:
            item = "%s: " % elt["name"] + "%s" % elt["qty"]
            in_cart.append(item)
        return in_cart

    def __repr__(self):
        cart = self.list()

    def list(self):
        r = requests.get(self.url)
        cart = r.json()
        return cart

    def add(self, item, qty):
        url = os.path.join(self.url,'product', item)
        payload = {'qty': qty}
        r = requests.put(url, json=payload)
        cart = r.json()
        return cart

    def delete(self, item):
        url = os.path.join(self.url,'product', item)
        r = requests.delete(url)
        cart = r.json()
        return cart
