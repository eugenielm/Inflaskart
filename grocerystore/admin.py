from django.contrib import admin
from .models import Product, Store, Availability, Inflauser, Address, Dietary,\
                    ProductCategory, ProductSubCategory, ProductSubSubCategory

# class StoreAdmin(admin.ModelAdmin):
#     fieldsets = [
#         ('Available products in store', {'fields': ['products']}),
#         ('Store location', {'fields': ['store_name', 'store_location', 'store_city',]+\
#         ['store_state', 'store_country', 'store_pic']}),
    # ]

# admin.site.register(Store, StoreAdmin)

admin.site.register(Product)
admin.site.register(Store)
admin.site.register(Availability)
admin.site.register(Inflauser)
admin.site.register(Address)
admin.site.register(Dietary)
admin.site.register(ProductCategory)
admin.site.register(ProductSubCategory)
admin.site.register(ProductSubSubCategory)
