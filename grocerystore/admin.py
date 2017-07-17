from django.contrib import admin
from .models import Product, Store, Availability, Inflauser, Address, Dietary,\
                    ProductCategory, ProductSubCategory, State, Zipcode, Order,\
                    ProductPurchaseHistory


class InflauserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'user_full_name', 'user_address')

    def user_id(self, obj):
        return obj.infla_user.username

    def user_full_name(self, obj):
        return obj.infla_user.last_name + ", " + obj.infla_user.first_name

    def user_address(self, obj):
        return str(obj.inflauser_address)


class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_full_name', 'street_address1', 'street_address2', \
                    'apt_nb', 'other', 'city', 'zip_code', 'state')

    def user(self, obj):
        return Inflauser.objects.get(inflauser_address=obj).infla_user.username

    def user_full_name(self, obj):
        return Inflauser.objects.get(inflauser_address=obj).infla_user.last_name + ", " \
               + Inflauser.objects.get(inflauser_address=obj).infla_user.first_name


class ZipcodeAdmin(admin.ModelAdmin):
    list_display = ('zipcode', 'zip_city', 'zip_state')


class StateAdmin(admin.ModelAdmin):
    list_display = ('state_name','state_postal_code', 'all_cities', 'all_zipcodes')

    def all_cities(self, obj):
        cities = []
        for z in Zipcode.objects.filter(zip_state=obj):
            if z.zip_city not in cities:
                cities.append(z.zip_city)
        return ", ".join(cities)

    def all_zipcodes(self, obj):
        return ", ".join([str(z.zipcode) for z in Zipcode.objects.filter(zip_state=obj)])


class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name','product_diet', 'product_brand_or_variety', 'product_category')

    def product_diet(self, obj):
        return " // ".join([d.name for d in obj.product_dietary.all()])


class StoreAdmin(admin.ModelAdmin):
    list_display = ('store_name','store_location', 'store_city', 'store_zipcode', 'store_state', 'store_delivery_area')

    def store_delivery_area(self, obj):
        return ", ".join([str(zipcode.zipcode) for zipcode in obj.delivery_area.all()])


class CategoriesAdmin(admin.ModelAdmin):
    list_display = ('parent','sub_category_name', 'all_products')

    def all_products(self, obj):
        return " // ".join([str(p) for p in Product.objects.filter(product_category=obj)])


class TopCategoriesAdmin(admin.ModelAdmin):
    list_display = ('top_category','all_sub_categories')

    def all_sub_categories(self, obj):
        return " // ".join([str(cat.sub_category_name) for cat in ProductSubCategory.objects.filter(parent=obj)])


class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('product_category', 'product', 'store', 'product_unit', 'product_price')

    def product_category(self, obj):
        return obj.product.product_category


class ProductPurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ('purchaser', 'purchase_store', 'purchase_date', 'bought_product', 'bought_product_category', 'total_amount')

    def total_amount(self, obj):
        return "$%.2f" % obj.purchase_amount


class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'order_number', 'purchase_date', 'store', 'order_total')

    def user(self, obj):
        return obj.data['user']['username']

    def order_number(self, obj):
        return obj.data['order_nb']

    def purchase_date(self, obj):
        if obj.data['purchase_date'][3] < 12: tod = 'am'
        else: tod = 'pm'

        return str(obj.data['purchase_date'][1]) + "/" + str(obj.data['purchase_date'][2]) + "/" \
               + str(obj.data['purchase_date'][0]) + ", " + str(obj.data['purchase_date'][3]) \
               + "." + str(obj.data['purchase_date'][4]) + tod

    def store(self, obj):
        return obj.data['store']['store_name'] + " (" + obj.data['store']['store_address']['store_location'] + ")"

    def order_total(self, obj):
        return "$" + obj.data['order_total']



admin.site.register(Dietary)

admin.site.register(Inflauser, InflauserAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Zipcode, ZipcodeAdmin)
admin.site.register(State, StateAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Store, StoreAdmin)
admin.site.register(ProductSubCategory, CategoriesAdmin)
admin.site.register(ProductCategory, TopCategoriesAdmin)
admin.site.register(Availability, AvailabilityAdmin)
admin.site.register(ProductPurchaseHistory, ProductPurchaseHistoryAdmin)
admin.site.register(Order, OrderAdmin)
