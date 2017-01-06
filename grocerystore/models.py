from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models


@python_2_unicode_compatible
class Product(models.Model):
    product_name = models.CharField(max_length=60)
    product_unit = models.CharField(max_length=20)
    product_price = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    # product_brand = models.CharField(max_length=20, required=False)
    # product_category = models.CharField(max_length=30)

    # def __str__(self):
    #     return self.product_name + " (" + self.product_unit + ")"

    def __str__(self):
        return self.product_name + " ($" + str(self.product_price) + " / " + self.product_unit + ")"

# class Store(models.Model):
#     store_name = models.CharField(max_length=50)
    # store_city = models.Charfield(max_length=20)
    # store_state = models.ChoiceField(queryset=STATES)
