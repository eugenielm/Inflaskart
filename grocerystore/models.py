from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from django.db import models
import json


@python_2_unicode_compatible
class Inflauser(models.Model):
    infla_user = models.OneToOneField(User)
    inflauser_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.infla_user.username

    class Meta:
        ordering = ['infla_user__username']


@python_2_unicode_compatible
class Address(models.Model):
    inflauser = models.ForeignKey(Inflauser, on_delete=models.CASCADE, default=None)
    address_name = models.CharField(max_length=20)
    street_adress = models.CharField(max_length=100)
    apt_nb = models.IntegerField(null=True, blank=True)
    other = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=30)
    zip_code = models.IntegerField()
    state = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=30)

    def __str__(self):
        return self.inflauser.infla_user.username + " - " + self.address_name

    class Meta:
        ordering = ['inflauser__infla_user__username', 'address_name']
        verbose_name_plural = "addresses"


@python_2_unicode_compatible
class Store(models.Model):
    ALABAMA = "AL"
    ALASKA = "AK"
    ARIZONA = "AZ"
    ARKANSAS = "AR"
    CALIFORNIA = "CA"
    COLORADO = "CO"
    CONNECTICUT = "CT"
    DELAWARE = "DE"
    FLORIDA = "FL"
    GEORGIA = "GA"
    HAWAII = "HI"
    IDAHO = "ID"
    ILLINOIS = "IL"
    INDIANA = "IN"
    IOWA = "IA"
    KANSAS = "KS"
    KENTUCKY = "KY"
    LOUISIANA = "LA"
    MAINE = "ME"
    MARYLAND = "MD"
    MASSACHUSETTS = "MA"
    MICHIGAN = "MI"
    MINNESOTA = "MN"
    MISSISSIPPI = "MS"
    MISSOURI = "MO"
    MONTANA = "MT"
    NEBRASKA = "NE"
    NEVADA = "NV"
    NEW_HAMPSHIRE = "NH"
    NEW_JERSEY = "NJ"
    NEW_MEXICO = "NM"
    NEW_YORK = "NY"
    NORTH_CAROLINA = "NC"
    NORTH_DAKOTA = "ND"
    OHIO = "OH"
    OKLAHOMA = "OK"
    OREGON = "OR"
    PENNSYLVANIA = "PA"
    RHODE_ISLAND = "RI"
    SOUTH_CAROLINA = "SC"
    SOUTH_DAKOTA = "SD"
    TENNESSEE = "TN"
    TEXAS = "TX"
    UTAH = "UT"
    VERMONT = "VE"
    VIRGINIA = "VA"
    WASHINGTON = "WA"
    WEST_VIRGINIA = "WV"
    WISCONSIN = "WI"
    WYOMING = "WY"
    DISTRICT_OF_COLUMBIA = "DC"

    US_STATES = (
        (ALABAMA, 'Alabama'),
        (ALASKA, 'Alaska'),
        (ARIZONA, 'Arizona'),
        (ARKANSAS, 'Arkansas'),
        (CALIFORNIA, 'California'),
        (COLORADO, 'Colorado'),
        (CONNECTICUT, 'Connecticut'),
        (DELAWARE, 'Delaware'),
        (FLORIDA, 'Florida'),
        (GEORGIA, 'Georgia'),
        (HAWAII, 'Hawaii'),
        (IDAHO, 'Idaho'),
        (ILLINOIS, 'Illinois'),
        (INDIANA, 'Indiana'),
        (IOWA, 'Iowa'),
        (KANSAS, 'Kansas'),
        (KENTUCKY, 'Kentucky'),
        (LOUISIANA, 'Louisiana'),
        (MAINE, 'Maine'),
        (MARYLAND, 'Maryland'),
        (MASSACHUSETTS, 'Massachusetts'),
        (MICHIGAN, 'Michigan'),
        (MINNESOTA, 'Minnesota'),
        (MISSISSIPPI, 'Mississippi'),
        (MISSOURI, 'Missouri'),
        (MONTANA, 'Montana'),
        (NEBRASKA, 'Nebraska'),
        (NEVADA, 'Nevada'),
        (NEW_HAMPSHIRE, 'New Hampshire'),
        (NEW_JERSEY, 'New Jersey'),
        (NEW_MEXICO, 'New Mexico'),
        (NEW_YORK, 'New York'),
        (NORTH_CAROLINA, 'North Carolina'),
        (NORTH_DAKOTA, 'North Dakota'),
        (OHIO, 'Ohio'),
        (OKLAHOMA, 'Oklahoma'),
        (OREGON, 'Oregon'),
        (PENNSYLVANIA, 'Pennsylvania'),
        (RHODE_ISLAND, 'Rhode Island'),
        (SOUTH_CAROLINA, 'South Carolina'),
        (SOUTH_DAKOTA, 'South Dakota'),
        (TENNESSEE, 'Tennessee'),
        (TEXAS, 'Texas'),
        (UTAH, 'Utah'),
        (VERMONT, 'Vermont'),
        (VIRGINIA, 'Virginia'),
        (WASHINGTON, 'Washington'),
        (WEST_VIRGINIA, 'West Virginia'),
        (WISCONSIN, 'Wisconsin'),
        (WYOMING, 'Wyoming'),
        (DISTRICT_OF_COLUMBIA, 'District of Columbia'),
    )

    store_name = models.CharField(max_length=30)
    store_location = models.CharField(max_length=30, default=None)
    store_city = models.CharField(max_length=30)
    store_state = models.CharField(max_length=30, choices=US_STATES)
    store_country = models.CharField(max_length=30, default="USA")
    store_pic = models.ImageField(blank=True)

    def __str__(self):
        return self.store_name + " (" + self.store_location + ")"


@python_2_unicode_compatible
class ProductCategory(models.Model):
    top_category = models.CharField(max_length=30)
    def __str__(self):
        return self.top_category
    class Meta:
        ordering = ['top_category',]
        verbose_name_plural = "product categories"


@python_2_unicode_compatible
class ProductSubCategory(models.Model):
    top_category = models.ForeignKey(ProductCategory, blank=True, default=None)
    sub_category_1 = models.CharField(max_length=30, blank=True, default=None)
    def __str__(self):
        return self.top_category.top_category + " / " + self.sub_category_1
    class Meta:
        ordering = ['top_category', 'sub_category_1']
        verbose_name = "product sub-category"
        verbose_name_plural = "product sub-categories"


@python_2_unicode_compatible
class Dietary(models.Model):
    name = models.CharField(max_length=30)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ['name']
        verbose_name_plural = "dietaries"


@python_2_unicode_compatible
class Product(models.Model):
    product_name = models.CharField(max_length=60)
    product_category = models.ForeignKey(ProductSubCategory, default=None)
    product_dietary = models.ManyToManyField(Dietary, blank=True)
    product_brand_or_variety = models.CharField(max_length=50, blank=True)
    product_description = models.TextField(blank=True)
    product_pic = models.ImageField(blank=True)
    user_id_required = models.BooleanField(default=False)
    product_store = models.ManyToManyField(Store, through='Availability')

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
    product_unit = models.CharField(max_length=20)
    product_price = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        price = "$" + str(self.product_price) + " / " + self.product_unit

        if len(self.product.product_dietary.all()) == 0:
            if not self.product.product_brand_or_variety:
                return self.product.product_name + " - " + price + ")"
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
