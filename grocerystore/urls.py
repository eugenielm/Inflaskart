#-*- coding: UTF-8 -*-
from django.conf.urls import url
from . import views

app_name = 'grocerystore'
urlpatterns = [
    # grocerystore/
    url(r'^$', views.IndexView.as_view(), name='index'),
    # grocerystore/register/
    url(r'^register/$', views.UserRegisterView.as_view(), name='register'),
    # grocerystore/login/
    url(r'^login/$', views.UserLoginForm.as_view(), name='login'),
    # grocerystore/cart/
    url(r'^cart/$', views.CartView.as_view(), name='cart'),
    # grocerystore/logout/
    url(r'^logout/$', views.log_out, name='log_out'),
    # grocerystore/search/anyitemurlencoded/
    url(r'^search/(?P<searched_item>[0-9a-zA-Z%]+)/$', views.SearchView.as_view(), name='search'),
    # grocerystore/checkout/
    url(r'^checkout/$', views.CheckoutView.as_view(), name='checkout'),
    url(r'^congrats/$', views.congrats, name='congrats'),
]
