from django.contrib import admin
from .models import Product, Store, Availability, Inflauser, Address, Dietary,\
                    ProductCategory, ProductSubCategory

admin.site.register(Product)
admin.site.register(Store)
admin.site.register(Availability)
admin.site.register(Inflauser)
admin.site.register(Address)
admin.site.register(Dietary)
admin.site.register(ProductCategory)
admin.site.register(ProductSubCategory)
