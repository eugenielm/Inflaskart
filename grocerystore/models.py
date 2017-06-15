#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models
import json


"""
This module contains 13 model classes:
- State (used by the Address model's state field, by the Store model's
store_state field)
- Address (used by the Inflauser model's inflauser_address field)
- Inflauser (also requires the User model)
- Zipcode (used by the Store model's delivery_area field)
- Store (used by the Product model's product_store field, and by the
Availability model's store field)
- ProductCategory (used by the ProductSubCategory model's parent field)
- ProductSubCategory (used by the Product model's product_category field)
- Dietary (used by the Product model's product_dietary field)
- Product (used by the Availability model's product field)
- Availability (used by the ItemInCart model's incart_availability field)
- ItemInCart
- Order
- ProductHistory
"""


@python_2_unicode_compatible
class State(models.Model):
    """This model is used for federal countries."""
    state_name = models.CharField(max_length=50)
    state_postal_code = models.CharField(max_length=2)

    def __str__(self):
        return str(self.state_name) + ", " + str(self.state_postal_code)

    class Meta:
        ordering = ['state_name', 'state_postal_code']


@python_2_unicode_compatible
class Address(models.Model):
    """Used by the inflauser_address field of the Inflauser model."""
    street_address1 = models.CharField(max_length=100, verbose_name="Address")
    street_address2 = models.CharField(max_length=100, blank=True, verbose_name="Address (line 2)")
    apt_nb = models.CharField(max_length=20, blank=True, verbose_name="Apt/Unit") # can be an integer or a character
    other = models.CharField(max_length=50, blank=True, verbose_name="Floor, building, etc.")
    city = models.CharField(max_length=50)
    zip_code = models.PositiveIntegerField(error_messages={'invalid': "Please enter a valid ZIP code."})
    state = models.ForeignKey(State, on_delete=models.CASCADE, error_messages={'invalid': "Please enter a valid ZIP code."})

    def __str__(self):
        return str(self.street_address1) + ", " + str(self.zip_code)

    class Meta:
        ordering = ['state', 'city', 'street_address1']
        verbose_name_plural = "addresses"


@python_2_unicode_compatible
class Inflauser(models.Model):
    """Extension of the User model to allow users to store their address."""
    # https://docs.djangoproject.com/en/dev/topics/auth/customizing/#extending-user
    infla_user = models.OneToOneField(User)
    inflauser_address = models.ForeignKey(Address, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.infla_user.username)

    class Meta:
        ordering = ['infla_user__username']


@python_2_unicode_compatible
class Zipcode(models.Model):
    """Used by the delivery_area field of the Store class."""
    zipcode = models.PositiveIntegerField(error_messages={'invalid': "Please enter a valid ZIP code."})
    zip_city = models.CharField(max_length=50)
    zip_state = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.zip_city) + ", " + str(self.zip_state.state_postal_code) + " " + str(self.zipcode)

    class Meta:
        ordering = ['zip_city', 'zipcode']


@python_2_unicode_compatible
class Store(models.Model):
    """Model used for each store. Several store objects may have the same brand,
    ie. the same store_name."""
    store_name = models.CharField(max_length=30, verbose_name="store")
    store_location = models.CharField(max_length=30, verbose_name="location name")
    store_address = models.CharField(max_length=200, verbose_name="Address")
    store_city = models.CharField(max_length=30, verbose_name="city")
    store_zipcode = models.PositiveIntegerField(error_messages={'invalid': "Please enter a valid ZIP code."})
    store_state = models.ForeignKey(State, on_delete=models.CASCADE, verbose_name="state")
    store_pic = models.ImageField(upload_to='stores/', blank=True, verbose_name="logo/picture")
    delivery_area = models.ManyToManyField(Zipcode)

    def __str__(self):
        return str(self.store_name) + " (" + str(self.store_location) + ")"

    class Meta:
        ordering = ['store_name', 'store_state', 'store_city', 'store_location']


@python_2_unicode_compatible
class ProductCategory(models.Model):
    """Model used for product categories. Each category has several sub-categories."""
    top_category = models.CharField(max_length=30, verbose_name="top product category")

    def __str__(self):
        return str(self.top_category)

    class Meta:
        ordering = ['top_category',]
        verbose_name_plural = "product categories"


@python_2_unicode_compatible
class ProductSubCategory(models.Model):
    """Model used for product sub-categories. Each sub-category has only one
    parent category."""
    parent = models.ForeignKey(ProductCategory, verbose_name="top product category")
    sub_category_name = models.CharField(max_length=30, verbose_name="product sub-category")

    def __str__(self):
        return str(self.parent.top_category) + " / " + str(self.sub_category_name)

    class Meta:
        ordering = ['parent__top_category', 'sub_category_name']
        verbose_name = "product sub-category"
        verbose_name_plural = "product sub-categories"


@python_2_unicode_compatible
class Dietary(models.Model):
    """Model used for product dietaries: it can be organic, gluten-free, etc."""
    name = models.CharField(max_length=30, verbose_name="dietary")

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "dietaries"


@python_2_unicode_compatible
class Product(models.Model):
    product_name = models.CharField(max_length=60, verbose_name="product")
    product_category = models.ForeignKey(ProductSubCategory, on_delete=models.CASCADE)
    product_dietary = models.ManyToManyField(Dietary, blank=True)
    product_brand_or_variety = models.CharField(max_length=50, blank=True, verbose_name="product brand/variety")
    product_description = models.TextField(blank=True)
    product_pic = models.ImageField(upload_to='products/', blank=True, verbose_name="product picture")
    user_id_required = models.BooleanField(default=False, verbose_name="ID required")
    product_store = models.ManyToManyField(Store, through='Availability', verbose_name="availability(ies) in store(s)")
    # sales tax is applicable in California except for groceries and prescription drugs
    taxability = models.BooleanField(default=True)

    def __str__(self):
        if len(self.product_dietary.all()) == 0:
            if not self.product_brand_or_variety:
                return str(self.product_name)
            else:
                return str(self.product_name) + " - " + str(self.product_brand_or_variety)
        else:
            dietaries = ""
            for dietary in self.product_dietary.all():
                dietaries += (str(dietary.name) + " ")
            if not self.product_brand_or_variety:
                return str(self.product_name) + " - " + dietaries
            else:
                return str(self.product_name) + " - " + str(self.product_brand_or_variety) \
                       + " - " + dietaries

    class Meta:
        ordering = ['product_name']


@python_2_unicode_compatible
class Availability(models.Model):
    """This model is used as an intermediate between Product and Store instances."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    product_unit = models.CharField(max_length=20, verbose_name="unit")
    product_price = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="price")

    def __str__(self):
        price = "$" + str(self.product_price) + " / " + str(self.product_unit)
        dietaries_nb = len(self.product.product_dietary.all())
        if dietaries_nb == 0:
            if not self.product.product_brand_or_variety:
                return str(self.store) + ", " + str(self.product.product_category) \
                       + " - " + str(self.product.product_name) + " - " + price
            else:
                return str(self.store) + ", " + str(self.product.product_category) \
                       + " - " + str(self.product.product_name) + " (" \
                       + str(self.product.product_brand_or_variety) + ") " + price
        else:
            dietaries = ""
            for dietary in self.product.product_dietary.all()[:dietaries_nb-1]:
                dietaries += (str(dietary.name) + " - ")
            dietaries += str(self.product.product_dietary.all()[dietaries_nb-1].name)
            if not self.product.product_brand_or_variety:
                return str(self.store) + ", " + str(self.product.product_category) \
                       + " - " + str(self.product.product_name) + " (" + dietaries + ") " + price
            else:
                return str(self.store) + ", " + str(self.product.product_category) \
                       + " - " + str(self.product.product_name) + " (" \
                       + str(self.product.product_brand_or_variety) + ", " + dietaries + ") " + price

    class Meta:
        ordering = ['store__store_name', 'store__store_location',
                    'product__product_category__parent__top_category',
                    'product__product_category__sub_category_name',
                    'product__product_name']
        verbose_name_plural = "availabilities"


@python_2_unicode_compatible
class ItemInCart(models.Model):
    """An instance of this model is created when a user puts an item in their cart."""
    incart_user = models.ForeignKey(User, on_delete=models.CASCADE)
    incart_availability = models.ForeignKey(Availability, on_delete=models.CASCADE)
    incart_quantity = models.FloatField()

    def __str__(self):
        return str(self.incart_quantity) + " " + str(self.incart_availability.product.product_name)

    class Meta:
        ordering = ['incart_availability__product__product_name']


class Order(models.Model):
    """An instance of this model is created each time an order is placed.
    The order number will be set to the pk + some specific start value (e.g.: 1000)"""
    data = JSONField() # all the important details about the order

    class Meta:
        ordering = ['-pk']


class ProductPurchase(models.Model):
    """All bought items are stored as ProductPurchase instances - for data
    analysis purposes."""
    bought_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    purchase_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True)
    # https://docs.djangoproject.com/en/1.11/ref/models/fields/#datefield
    purchase_dates = ArrayField(models.DateTimeField())
    nb_of_purchases = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['customer__username','bought_product__product_name']
