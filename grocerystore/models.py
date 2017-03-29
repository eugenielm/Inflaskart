#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from django.db import models
import json


"""
This module contains 10 model classes:
- State (used by the Address model's state field, by the Store model's
store_state field)
- Address (used by the Inflauser model's inflauser_address field)
THERE'S A TYPO IN street_adress1 AND street_adress2 (should be street_address with 2 'd')
- Inflauser (also requires the User model)
- Zipcode (used by the Store model's delivery_area field)
- Store (used by the Product model's product_store field, and by the
Availability model's store field)
- ProductCategory (used by the ProductSubCategory model's parent field)
- ProductSubCategory (used by the Product model's product_category field)
- Dietary (used by the Product model's product_dietary field)
- Product (used by the Availability model's product field)
- Availability
"""


@python_2_unicode_compatible
class State(models.Model):
    state_name = models.CharField(max_length=50)
    state_postal_code = models.CharField(max_length=2)

    def __str__(self):
        return self.state_name + ", " + self.state_postal_code

    class Meta:
        ordering = ['state_name', 'state_postal_code']


@python_2_unicode_compatible
class Address(models.Model):
    """Used by the inflauser_address field of the Inflauser class."""
    street_adress1 = models.CharField(max_length=100, verbose_name="Address")
    street_adress2 = models.CharField(max_length=100, blank=True, verbose_name="Address (line 2)")
    apt_nb = models.CharField(max_length=20, blank=True, verbose_name="Apt/Unit") # can be an integer or a character
    other = models.CharField(max_length=50, blank=True, verbose_name="Floor, building, etc.")
    city = models.CharField(max_length=30)
    zip_code = models.PositiveIntegerField(error_messages={'invalid': "Please enter a valid ZIP code."})
    state = models.ForeignKey(State, on_delete=models.CASCADE, error_messages={'invalid': "Please enter a valid ZIP code."})

    def __str__(self):
        return self.street_adress1 + ", " + str(self.zip_code)

    class Meta:
        ordering = ['state', 'city', 'street_adress1']
        verbose_name_plural = "addresses"


@python_2_unicode_compatible
class Inflauser(models.Model):
    infla_user = models.OneToOneField(User)
    inflauser_address = models.ForeignKey(Address, on_delete=models.CASCADE)

    def __str__(self):
        return self.infla_user.username

    class Meta:
        ordering = ['infla_user__username']


@python_2_unicode_compatible
class Zipcode(models.Model):
    """Used by the delivery_area field of the Store class."""
    zipcode = models.PositiveIntegerField(error_messages={'invalid': "Please enter a valid ZIP code."})

    def __str__(self):
        return str(self.zipcode)


@python_2_unicode_compatible
class Store(models.Model):
    store_name = models.CharField(max_length=30, verbose_name="store")
    store_location = models.CharField(max_length=30, default=None, verbose_name="location name")
    store_city = models.CharField(max_length=30, verbose_name="city")
    store_zipcode = models.PositiveIntegerField(error_messages={'invalid': "Please enter a valid ZIP code."})
    store_state = models.ForeignKey(State, on_delete=models.CASCADE, verbose_name="state")
    store_pic = models.ImageField(blank=True, verbose_name="logo/picture")
    delivery_area = models.ManyToManyField(Zipcode)

    def __str__(self):
        return self.store_name + " (" + self.store_location + ")"

    class Meta:
        ordering = ['store_name', 'store_state', 'store_city', 'store_location']


@python_2_unicode_compatible
class ProductCategory(models.Model):
    top_category = models.CharField(max_length=30, verbose_name="top product category")
    def __str__(self):
        return self.top_category
    class Meta:
        ordering = ['top_category',]
        verbose_name_plural = "product categories"


@python_2_unicode_compatible
class ProductSubCategory(models.Model):
    parent = models.ForeignKey(ProductCategory, blank=True, default=None, verbose_name="top product category")
    sub_category_name = models.CharField(max_length=30, blank=True, default=None, verbose_name="product sub-category")
    def __str__(self):
        return self.parent.top_category + " / " + self.sub_category_name
    class Meta:
        ordering = ['parent', 'sub_category_name']
        verbose_name = "product sub-category"
        verbose_name_plural = "product sub-categories"


@python_2_unicode_compatible
class Dietary(models.Model):
    name = models.CharField(max_length=30, verbose_name="dietary")
    def __str__(self):
        return self.name
    class Meta:
        ordering = ['name']
        verbose_name_plural = "dietaries"


@python_2_unicode_compatible
class Product(models.Model):
    product_name = models.CharField(max_length=60, verbose_name="product")
    product_category = models.ForeignKey(ProductSubCategory, default=None)
    product_dietary = models.ManyToManyField(Dietary, blank=True)
    product_brand_or_variety = models.CharField(max_length=50, blank=True, verbose_name="product brand/variety")
    product_description = models.TextField(blank=True)
    product_pic = models.ImageField(blank=True, verbose_name="product picture")
    user_id_required = models.BooleanField(default=False, verbose_name="ID required")
    product_store = models.ManyToManyField(Store, through='Availability', verbose_name="availability(ies) in store(s)")

    def __str__(self):
        if len(self.product_dietary.all()) == 0:
            if not self.product_brand_or_variety:
                return "'" + self.product_name + "'"
            else:
                return "'" + self.product_name + " - " + self.product_brand_or_variety + "'"
        else:
            dietaries = ""
            for dietary in self.product_dietary.all():
                dietaries += (dietary.name + " ")
            if not self.product_brand_or_variety:
                return "'" + str(self.product_name) + " - " + dietaries + "'"
            else:
                return "'" + str(self.product_name) + " - " + self.product_brand_or_variety \
                       + " - " + dietaries + "'"

    class Meta:
        ordering = ['product_name']


@python_2_unicode_compatible
class Availability(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    product_unit = models.CharField(max_length=20, verbose_name="unit")
    product_price = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="price")

    def __str__(self):
        price = "$" + str(self.product_price) + " / " + self.product_unit

        if len(self.product.product_dietary.all()) == 0:
            if not self.product.product_brand_or_variety:
                return self.product.product_name + " - " + price
            else:
                return self.product.product_name + " (" + self.product.product_brand_or_variety +\
                       " - " + price + ")"
        else:
            dietaries = ""
            for dietary in self.product.product_dietary.all():
                dietaries += (dietary.name + " ")
            if not self.product.product_brand_or_variety:
                return self.product.product_name + " ( " + dietaries + " - " + price + " )"
            else:
                return self.product.product_name + " ( " + self.product.product_brand_or_variety +\
                       ", " + dietaries + " - " + price + ")"

    class Meta:
        ordering = ['product__product_name']
        verbose_name_plural = "availabilities"
