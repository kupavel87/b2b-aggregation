"""b2bprice URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from .settings import SILK

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('providers/', include('providers.urls')),
]

urlpatterns += [
    path('accounts/', include('django.contrib.auth.urls')),
]

if SILK:
    urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]
