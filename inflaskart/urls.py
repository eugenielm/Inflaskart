"""inflaskart URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url, handler404, handler500
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings


handler404 = 'grocerystore.views.PageNotFound'
handler500 = 'grocerystore.views.ServerError'


urlpatterns = [
    url(r'^', include('grocerystore.urls')),
    # if there were more than the grocerystore app in the inflaskart project, I could use the following:
    # url(r'^grocerystore/', include('grocerystore.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^', include('favicon.urls')),
]
