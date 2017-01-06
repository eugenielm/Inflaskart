#-*- coding: UTF-8 -*-
from django.conf.urls import url
from . import views

app_name = 'grocerystore'
urlpatterns = [
    # grocerystore/
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^register/$', views.UserRegisterView.as_view(), name='register'),
    url(r'^login/$', views.UserLoginForm.as_view(), name='login'),
    # url(r'^(?P<username>[0-9a-zA-Z]+)/cart/$', views.ShowCartView.as_view(), name='cart'), -> remplacé par:
    url(r'^cart/$', views.CartView.as_view(), name='cart'),
    # url(r'^(?P<username>[0-9a-zA-Z]+)/logout/$', views.log_out, name='log_out'), -> remplacé par:
    url(r'^logout/$', views.log_out, name='log_out'),
    # url(r'^(?P<username>[0-9a-zA-Z]+)/search/(?P<searched_item>[0-9a-zA-Z%]+)/$', views.SearchView.as_view(), name='search') -> remplacé par:,
    url(r'^search/(?P<searched_item>[0-9a-zA-Z%]+)/$', views.SearchView.as_view(), name='search'),
        # # grocerystore/eglelek/checkout/
        # url(r'^(?P<username>[0-9a-zA-Z]+)/checkout/$', views.Checkout.as_view(), name='checkout'),

]
