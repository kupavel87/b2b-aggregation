from django.urls import path, include
from . import views
from django.views.generic import TemplateView


app_name = 'providers'
urlpatterns = [
    path('', views.index, name='index'),
    path('catalog', views.catalog, name='catalog'),
    path('price', views.price, name='price'),
    path('product_detail', views.product_detail, name='product_detail'),
    path('save_mapping', views.save_mapping, name='save_mapping'),
]
