from django.urls import path, include
from . import views
from django.views.generic import TemplateView


app_name = 'main'
urlpatterns = [
    path('', views.index, name='index'),
    # path('getprice', views.getprice, name='getprice'),
    # path('getcatalog', views.getcatalog, name='getcatalog'),
    # path('addproduct', views.addproduct, name='addproduct'),
    # path('updateprice', views.updateprice, name='updateprice'),
    # path('finditem', views.finditem, name='finditem'),
    # path('detailinfo', views.detailinfo, name='detailinfo'),
    # path('detailgroup', views.detailgroup, name='detailgroup'),
    # path('settings', views.settings, name='settings'),

    # path('providers', views.providers, name='providers'),
    # path('provider_catalog', views.provider_catalog, name='provider_catalog'),
    # path('provider_price', views.provider_price, name='provider_price'),
    # path('provider_product_detail', views.provider_product_detail, name='provider_product_detail'),

    path('catalog', views.catalog, name='catalog'),
    path('viewcatalog', views.viewcatalog, name='viewcatalog'),
    path('historyupdate', views.historyupdate, name='historyupdate'),
    path('deleteupdate', views.deleteupdate, name='deleteupdate'),
    path('prepareproperty', views.prepareproperty, name='prepareproperty'),
    path('viewproperty', views.viewproperty, name='viewproperty'),
    path('search', views.search, name='search'),
    path('export_1c', views.export_1c, name='export_1c'),
    path('export_settings', views.export_settings, name='export_settings'),
    path('export_settings_save', views.export_settings_save, name='export_settings_save'),
    path('offer', views.offer, name='offer'),

    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type='text/plain')),
]
