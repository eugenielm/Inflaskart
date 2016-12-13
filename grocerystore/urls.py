from django.conf.urls import url
from . import views

app_name = 'grocerystore'
urlpatterns = [
    # grocerystore/
    url(r'^$', views.index, name='index'),
    #grocerystore/register/
    url(r'^register/$', views.UserRegisterView.as_view(), name='register'),
    # grocerystore/accounts/login/
    url(r'^accounts/login/$', views.UserLoginForm.as_view(), name='login'),
    # grocerystore/eglelek/   (only if user.is_authenticated())
    url(r'^(?P<username>[0-9a-zA-Z]+)/$', views.UserHomeView.as_view(), name='user_home'),
    # # grocerystore/logout/
    # url(r'^logout/$', views.log_out, name='log_out'),
    # grocerystore/eg2275/cart/
    url(r'^(?P<username>[0-9a-zA-Z]+)/cart/$', views.ShowCartView.as_view(), name='cart'),
]
