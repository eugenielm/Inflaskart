from django.conf.urls import url
from . import views

app_name = 'grocerystore'
urlpatterns = [
    # grocerystore/
    url(r'^$', views.index, name='index'),
    #grocerystore/register/
    url(r'^register/$', views.UserRegisterView.as_view(), name='register'),
    # grocerystore/accounts/login/
    url(r'^login/$', views.UserLoginForm.as_view(), name='login'),
    # grocerystore/eglelek/
    url(r'^(?P<username>[0-9a-zA-Z]+)/$', views.UserShopView.as_view(), name='user_shop'),
    # grocerystore/eglelek/cart/
    url(r'^(?P<username>[0-9a-zA-Z]+)/cart/$', views.ShowCartView.as_view(), name='cart'),
    # grocerystore/eglelek/logout/
    url(r'^(?P<username>[0-9a-zA-Z]+)/logout/$', views.log_out, name='log_out'),
    # # grocerystore/eglelek/checkout/
    # url(r'^(?P<username>[0-9a-zA-Z]+)/checkout/$', views.Checkout.as_view(), name='checkout'),
    # grocerystore/eglelek/search/searcheditem/
    url(r'^(?P<username>[0-9a-zA-Z]+)/search/(?P<searched_item>[0-9a-zA-Z%]+)/$', views.SearchView.as_view(), name='search'),
]
