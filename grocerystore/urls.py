#-*- coding: UTF-8 -*-
from django.conf.urls import url
from . import views

app_name = 'grocerystore'
urlpatterns = [
    # grocerystore/
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^register/$', views.UserRegisterView.as_view(), name='register'),
    url(r'^login/$', views.UserLoginForm.as_view(), name='login'),
    url(r'^logout/$', views.log_out, name='log_out'),
    url(r'^storessearch/(?P<searched_store>[0-9a-zA-Z%]+)/$', views.StoresSetList.as_view(), name='stores_set'),
    url(r'^store/(?P<store_id>[0-9]+)/$', views.StoreView.as_view(), name='store'),
    url(r'^store/(?P<store_id>[0-9a-zA-Z%]+)/cart/$', views.CartView.as_view(), name='cart'),
    url(r'^store/(?P<store_id>[0-9a-zA-Z%]+)/search/(?P<searched_item>[0-9a-zA-Z%]+)/$', views.SearchView.as_view(), name='search_in_store'),
    url(r'^store/(?P<store_id>[0-9a-zA-Z%]+)/checkout/$', views.CheckoutView.as_view(), name='checkout'),
    url(r'^congrats/$', views.congrats, name='congrats'),
    url(r'^store/(?P<store_id>[0-9a-zA-Z%]+)/category/(?P<category_id>[0-9a-zA-Z%]+)/$', views.SubcategoriesList.as_view(), name='subcategories'),
    url(r'^store/(?P<store_id>[0-9a-zA-Z%]+)/category/(?P<category_id>[0-9a-zA-Z%]+)/subcategory/(?P<subcategory_id>[0-9a-zA-Z%]+)/$', views.InstockList.as_view(), name='instock'),
]
