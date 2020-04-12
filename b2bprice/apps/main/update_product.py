import logging
from logging.handlers import TimedRotatingFileHandler

from main.models import Catalog, Catalog_mapping, Price, Product, Vendor, Property, Property_mapping, Property_Value, ProviderAPI
from providers.providers import get_provider_price, get_provider_product_detail

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO,
                    handlers=[TimedRotatingFileHandler('log/tasks.log', when="d", interval=1, backupCount=7)])


def prepare_update(id=None, name=None, date=None):
    print("Подготовка обновления")
    if id:
        category = Catalog.objects.get(id=id)
    elif name:
        category = Catalog.objects.get(name=name)
    else:
        return 'error'
    result = {'providers': set(), 'category': {}, 'new': {}}
    return update_category(category, date, result, ProviderAPI.objects.all())


def update_category(category, date, result, providers):
    print(f"Обновление {category.name}")
    for provider in providers:
        provider_categories = Catalog_mapping.objects.filter(catalog_id=category, provider_id=provider)
        new_price = {}
        new_protucts_property = []
        for provider_category in provider_categories:
            provider_price = get_provider_price(0, provider_category.value, provider)
            check = provider_price.get('price', '')
            if check:
                new_price.update(check)
        if not new_price:
            continue
        result['providers'].add(provider.name)
        if category.name not in result['category']:
            result['category'][category.name] = {}
        result['category'][category.name][provider.name] = len(new_price)
        create_price = []
        for product in category.products.all():
            new_product = new_price.pop(product.partnumber, '')
            if new_product:
                create_price.append(Price(provider_id=provider, product_id=product, balance=new_product['balance'],
                                          value=new_product['price'], currency=new_product['currency'], date=date))
        if create_price:
            Price.objects.bulk_create(create_price)
        products_by_vendor = {}
        for _, new_product in new_price.items():
            vendor = new_product['vendor']
            if vendor in products_by_vendor:
                products_by_vendor[vendor].append(new_product)
            else:
                products_by_vendor[vendor] = [new_product]
        vendors = Vendor.objects.filter(name__in=products_by_vendor)
        new_vendors = products_by_vendor.copy()
        for vendor in vendors:
            new_vendors.pop(vendor.name)
        create_vendor = []
        for name in new_vendors:
            create_vendor.append(Vendor(name=name))
        if create_vendor:
            Vendor.objects.bulk_create(create_vendor)
        vendors = Vendor.objects.filter(name__in=products_by_vendor)
        for vendor in vendors:
            for new_product in products_by_vendor.pop(vendor.name):
                product = Product.objects.create(name=new_product['name'], catalog_id=category,
                                                 partnumber=new_product['partnumber'], vendor_id=vendor)
                Price.objects.create(provider_id=provider, product_id=product, balance=new_product['balance'],
                                     value=new_product['price'], currency=new_product['currency'], date=date)
                new_protucts_property.append(product)
                logging.info(f"Добавлен продукт {new_product['partnumber']} в категорию {category.name}")
                if category.name not in result['new']:
                    result['new'][category.name] = []
                result['new'][category.name].append(new_product['partnumber'])
        if new_protucts_property:
            add_product_property(new_protucts_property)

    for child in category.get_children():
        result = update_category(child, date, result, providers)

    return result


def add_product_property(products, provider_id=2):
    print(f"добавление свойств для {len(products)} товаров")
    product_properties = {}
    basic_filter = {}
    personal_filter = {}
    provider = ''
    i = 0
    for product in products:
        if provider:
            provider_detail = get_provider_product_detail(provider_id, product.partnumber, provider)
        else:
            provider_detail = get_provider_product_detail(provider_id, product.partnumber)
        check = provider_detail.get('property')
        if check:
            product_properties[product.id] = check
            provider = provider_detail['provider']
            basic_filter.update({key: 0 for key in check['basic']})
            personal_filter.update({key: value['name'] for key, value in check['personal'].items()})
        i += 1
        if i % 10 == 0:
            print(i)
    if not product_properties:
        return

    basic_property = Property.objects.filter(type='1')
    for property_ in basic_property:
        basic_filter.pop(property_.name, None)
    create_name = []
    for name in basic_filter:
        create_name.append(Property(name=name, type='1'))
    if create_name:
        Property.objects.bulk_create(create_name)
    basic_property = Property.objects.filter(type='1')
    create_property_value = []
    for product in products:
        for property_ in basic_property:
            check = product_properties.get(product.id, None)
            if check:
                value = check['basic'].pop(property_.name, None)
                if value is not None:
                    create_property_value.append(Property_Value(product_id=product, property_id=property_, value=value))
    if create_property_value:
        Property_Value.objects.bulk_create(create_property_value)
    personal_property = Property_mapping.objects.filter(provider_id=provider, value__in=personal_filter)
    personal_filter_copy = personal_filter.copy()
    for property_ in personal_property:
        personal_filter.pop(property_.value, None)
    personal_filter = {value: key for key, value in personal_filter.items()}
    personal_property = Property.objects.filter(type='2', name__in=personal_filter)
    create_property_mapping = []
    for property_ in personal_property:
        ids = personal_filter.pop(property_.name, None)
        create_property_mapping.append(Property_mapping(property_id=property_, provider_id=provider, value=ids))
    if create_property_mapping:
        Property_mapping.objects.bulk_create(create_property_mapping)
    for name, ids in personal_filter.items():
        property_ = Property.objects.create(name=name, type=2)
        Property_mapping.objects.create(property_id=property_, provider_id=provider, value=ids)
    personal_property = Property_mapping.objects.filter(provider_id=provider, value__in=personal_filter_copy)
    create_property_value = []
    for product in products:
        for property_ in personal_property:
            check = product_properties.get(product.id, None)
            if check:
                value = check['personal'].pop(property_.value, None)
                if value is not None:
                    create_property_value.append(Property_Value(
                        product_id=product, property_id=property_.property_id, value=value['value']))
    if create_property_value:
        Property_Value.objects.bulk_create(create_property_value)

    property_ = Property.objects.filter(type='3').first()
    if not property_:
        property_ = Property.objects.create(name='Изображение', type='3')
    create_property_value = []
    for product in products:
        check = product_properties.get(product.id, None)
        if check:
            for picture in check['Изображение']:
                create_property_value.append(Property_Value(product_id=product, property_id=property_, value=picture))
    if create_property_value:
        Property_Value.objects.bulk_create(create_property_value)
