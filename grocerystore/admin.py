from django.contrib import admin
from .models import Product, Store, Availability, Inflauser, Address, Dietary,\
                    ProductCategory, ProductSubCategory, State, Zipcode, Order,\
                    ProductPurchase

# class StoreAdmin(admin.ModelAdmin):
#     fieldsets = [
#         ('Available products in store', {'fields': ['products']}),
#         ('Store location', {'fields': ['store_name', 'store_location', 'store_city',]+\
#         ['store_state', 'store_country', 'store_pic']}),
    # ]

# admin.site.register(Store, StoreAdmin)


admin.site.register(Inflauser)
admin.site.register(State)
admin.site.register(Address)
admin.site.register(Zipcode)
admin.site.register(Store)
admin.site.register(Product)
admin.site.register(Dietary)
admin.site.register(ProductCategory)
admin.site.register(ProductSubCategory)
admin.site.register(Availability)
admin.site.register(Order)
admin.site.register(ProductPurchase)
