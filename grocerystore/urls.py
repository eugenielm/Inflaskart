#-*- coding: UTF-8 -*-
from django.conf.urls import url
from . import views

app_name = 'grocerystore'
urlpatterns = [
    # to prevent errors for people who got the old link
    url(r'^grocerystore/$', views.IndexView.as_view(), name='index'),
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^register/$', views.UserRegisterView.as_view(), name='register'),
    url(r'^login/$', views.UserLoginView.as_view(), name='login'),
    url(r'^logout/$', views.log_out, name='logout'),
    url(r'^profile/$', views.ProfileView.as_view(), name='profile'),
    url(r'^profile/update/$', views.ProfileUpdateView.as_view(), name='profile_update'),
    url(r'^(?P<zipcode>[0-9]{4,5})/$', views.StartView.as_view(), name='start'),
    url(r'^(?P<zipcode>[0-9]{4,5})/store/(?P<store_id>[0-9a-zA-Z%]+)/$', \
            views.StoreView.as_view(), name='store'),
    url(r'^(?P<zipcode>[0-9]{4,5})/cart/$', views.CartView.as_view(), name='cart'),
    url(r'^(?P<zipcode>[0-9]{4,5})/store/(?P<store_id>[0-9a-zA-Z%]+)/detail/(?P<product_id>[0-9a-zA-Z%]+)/$', \
            views.ProductDetailView.as_view(), name='detail'),
    url(r'^(?P<zipcode>[0-9]{4,5})/store/(?P<store_id>[0-9a-zA-Z%]+)/search/(?P<searched_item>[0-9a-zA-Z%]+)/$',
            views.SearchView.as_view(), name='search'),
    url(r'^(?P<zipcode>[0-9]{4,5})/store/(?P<store_id>[0-9a-zA-Z%]+)/category/(?P<category_id>[0-9a-zA-Z%]+)/subcategory/(?P<subcategory_id>[0-9a-zA-Z%]+)/$',
            views.Instock.as_view(), name='instock'),
    url(r'^(?P<zipcode>[0-9]{4,5})/store/(?P<store_id>[0-9a-zA-Z%]+)/buyagain/$', \
            views.BuyAgainView.as_view(),name='buyagain'),
    url(r'^(?P<zipcode>[0-9]{4,5})/store/(?P<store_id>[0-9a-zA-Z%]+)/orders/$', \
            views.OrdersHistory.as_view(),name='orders'),
    url(r'^(?P<zipcode>[0-9]{4,5})/store/(?P<store_id>[0-9a-zA-Z%]+)/checkout/$', \
            views.CheckoutView.as_view(),name='checkout'),
]
