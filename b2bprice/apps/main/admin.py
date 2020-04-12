from django.contrib import admin
from .models import ProviderAPI, Catalog, Product, Price, Property, Property_Value, Vendor, ImportantProperty, Catalog_mapping, Property_mapping

admin.site.register(ProviderAPI)
admin.site.register(Catalog)
admin.site.register(Product)
admin.site.register(Price)
admin.site.register(Property)
admin.site.register(Property_Value)
admin.site.register(Vendor)
admin.site.register(ImportantProperty)
admin.site.register(Catalog_mapping)
admin.site.register(Property_mapping)
