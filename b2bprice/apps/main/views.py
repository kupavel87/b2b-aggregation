from datetime import datetime, timedelta
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.defaulttags import register
from django.template.loader import render_to_string
from django.urls import reverse


from .models import ProviderAPI, Catalog, Product, Price, Property, Property_Value, Vendor, ImportantProperty, Catalog_mapping
import logging
from functools import lru_cache
from decimal import Decimal, ROUND_HALF_UP
from .decorators import duration_time
from providers.providers import get_provider_catalog, get_provider_price, get_provider_product_detail
from main.utils import get_cbr
from main.update_product import prepare_update

logger = logging.getLogger(__name__)


@login_required
def index(request):
    """Главная станица"""
    # product_type_list = ProductType.objects.all()
    categories = Catalog.objects.filter(export=True)
    return render(request, 'main/index.html', {'categories': categories})


@register.filter
def get_item(dictionary, args):
    return dictionary.get(args, 0)


@login_required
def catalog(request):
    catalog = Catalog.objects.all()
    providers = ProviderAPI.objects.all()
    mapping = Catalog_mapping.objects.all().select_related('provider_id', 'catalog_id')
    provider_ids = {}
    for item in mapping:
        if item.catalog_id.id not in provider_ids:
            provider_ids[item.catalog_id.id] = {}
        if item.provider_id.id not in provider_ids[item.catalog_id.id]:
            provider_ids[item.catalog_id.id][item.provider_id.id] = item.value
        else:
            provider_ids[item.catalog_id.id][item.provider_id.id] += ', ' + item.value
    return render(request, 'main/catalog.html', {'catalog': catalog, 'providers': providers, 'provider_ids': provider_ids, 'page_name': 'Каталог'})


def create_catalog_list(root):
    result = [root]
    for children in root.children.all():
        result.extend(create_catalog_list(children))
    return result


def prepare_view(prices, products):
    cbr = {'RUB': Decimal(1), 'RUR': Decimal(1)}
    result = {'provider': {}, 'products': {}}
    for price in prices:
        p = price.product_id
        if p.id not in result['products']:
            result['products'][p.id] = {'partnumber': p.partnumber, 'name': p.name, 'catalog': p.catalog_id.name,
                                        'catalog_id': p.catalog_id.id, 'vendor': p.vendor_id.name,
                                        'vendor_id': p.vendor_id.id, 'price': {}}
        if price.provider_id.id not in result['products'][p.id]['price']:
            if price.currency not in cbr:
                cbr[price.currency] = get_cbr(price.currency)
            try:
                total = (price.value * cbr[price.currency]).quantize(Decimal('0.01'), ROUND_HALF_UP)
                total = str(total).replace('.', ',')
                pos = total.index(',') - 3
                while pos > 0:
                    total = '\xa0'.join([total[:pos], total[pos:]])
                    pos -= 3
            except TypeError:
                total = 'error'
            result['products'][p.id]['price'][price.provider_id.id] = [price.balance,
                                                                       total, price.currency, price.date.strftime('%d.%m.%Y')]
            if price.provider_id.id not in result['provider']:
                if datetime.utcnow().strftime('%d.%m.%Y') == price.date.strftime('%d.%m.%Y', ):
                    danger = 'bg-success'
                else:
                    danger = 'bg-danger'
                result['provider'][price.provider_id.id] = {
                    'name': price.provider_id.name, 'date': price.date.strftime('%d.%m.%Y'), 'danger': danger}
    return result


@login_required
def viewcatalog(request):
    start = datetime.now()
    try:
        catalog_id = request.POST['catalog_id']
    except KeyError:
        messages.info(request, 'Не указана группа')
        return HttpResponseRedirect(reverse('main:index'))

    catalog = Catalog.objects.get(id=catalog_id)
    catalog_list = create_catalog_list(catalog)
    products = Product.objects.filter(catalog_id__in=catalog_list)
    result = ''
    if products:
        last_week = datetime.now() - timedelta(days=7)
        prices = Price.objects.filter(product_id__in=products, date__gte=last_week).order_by('-date').select_related(
            "product_id", 'product_id__catalog_id', 'product_id__vendor_id', 'provider_id'
        )
        result = prepare_view(prices, products)
    end = datetime.now()
    text = f"Количество товаров: {len(result['products'])}\tВремя запроса: {end - start}"
    return render(request, 'main/viewcatalog3.html', {'result': result, 'text': text, 'page_name': 'Товары'})


@login_required
def historyupdate(request):
    start = datetime.now()
    providers = ProviderAPI.objects.all()
    update_dict = {}
    for provider in providers:
        price_count = Price.objects.filter(provider_id=provider).values(
            'date').annotate(count=Count('id')).order_by('-date')
        for price in price_count:
            date = price['date']
            if date not in update_dict:
                update_dict[date] = {'date': date}
            update_dict[date].update({provider.name: price['count']})
    sorted_dates = sorted(update_dict.keys(), reverse=True)
    update_list = [update_dict[date] for date in sorted_dates]
    paginator = Paginator(update_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    end = datetime.now()
    text = f"Количество обновлений: {len(update_list)}\tВремя запроса: {end - start}"
    return render(request, 'main/historyupdate.html', {'updates': page_obj, 'providers': providers, 'text': text})


@login_required
def deleteupdate(request):
    start = datetime.now()
    try:
        date = datetime.strptime(request.POST['date'], '%d-%m-%Y %H:%M:%S.%f (%Z)')
    except KeyError:
        messages.info(request, 'Не указана дата')
    else:
        update_list = Price.objects.filter(date=date)
        count = len(update_list)
        update_list.delete()
        end = datetime.now()
        text = f'Удалено обновлений: {count} за {date.astimezone(None).strftime("%d-%m-%Y %H:%M")}\tВремя запроса: {end - start}'
        messages.info(request, text)
    return HttpResponseRedirect(reverse('main:historyupdate'))


@login_required
def prepareproperty(request):
    start = datetime.now()
    try:
        product_id = request.POST['product_id']
    except KeyError:
        return JsonResponse({'name': 'Ошибка', 'body': 'Не указана группа'})
    product = Product.objects.filter(id=product_id).select_related('vendor_id').first()
    two_weeks = datetime.now() - timedelta(days=14)
    prices = product.prices.filter(date__gte=two_weeks).select_related('provider_id')
    result = Property_Value.objects.filter(product_id=product).select_related('property_id')
    images = []
    for prop in result:
        if prop.property_id.name == "Изображение":
            if prop.local_value:
                images.append(prop.local_value)
            else:
                images.append(prop.value)
    chart = {'providers': set(), 'dates': set(), 'colors': {}}
    for price in prices:
        chart['providers'].add(price.provider_id.name)
        chart['dates'].add(price.date)
    chart['dates'] = sorted(chart['dates'])
    for provider in chart['providers']:
        chart[provider] = {x: 0 for x in chart['dates']}
    for price in prices:
        chart[price.provider_id.name][price.date] = float(price.value)
    colors = ['red', 'blue']
    for i, provider in enumerate(chart['providers']):
        chart[provider] = list(chart[provider].values())
        chart['colors'][provider] = colors[i]
    body = render_to_string('main/prepareproperty.html',
                            {'product': product, 'properties': result, 'chart': chart, 'prices': prices, 'images': images})
    end = datetime.now()
    text = f'Количество свойств: {len(result)}\tВремя запроса: {end - start}'
    return JsonResponse({'name': product.name, 'body': body, 'text': text})


@login_required
def viewproperty(request):
    try:
        product_id = request.POST['product_id']
    except KeyError:
        messages.info(request, 'Не указана группа')
        return HttpResponseRedirect(reverse('main:index'))
    return render(request, 'main/viewproperty.html', {'product_id': product_id})


@lru_cache(maxsize=100)
@login_required
def search(request):
    start = datetime.now()
    try:
        if request.method == 'POST':
            search_str = request.POST['search']
        else:
            search_str = request.GET['search'].replace('_', '#')
            print(search_str)

    except KeyError:
        messages.info(request, 'Не указана строка поиска')
        return HttpResponseRedirect(reverse('main:index'))

    if search_str:
        last_month = datetime.now() - timedelta(days=30)
        products = Product.objects.filter(Q(partnumber__icontains=search_str) | Q(name__icontains=search_str)
                                          ).select_related('catalog_id', 'vendor_id')
        prices = Price.objects.filter(product_id__in=products, date__gte=last_month).order_by('-date').select_related(
            "product_id", 'product_id__catalog_id', 'product_id__vendor_id', 'provider_id')
        result = prepare_view(prices, products)
        end = datetime.now()
        text = f"Найдено товаров: {len(result['products'])}\tВремя запроса: {end - start}"
        return render(request, 'main/viewcatalog2.html', {'result': result, 'text': text, 'page_name': 'Поиск', 'search': search_str})
    else:
        messages.info(request, 'Пустая строка поиска')
        return HttpResponseRedirect(reverse('main:index'))


@login_required
def export_1c(request):
    start = datetime.now()
    try:
        catalog_id = request.POST['groupid']
    except KeyError:
        messages.info(request, 'Не указана группа для экспорта')
        return HttpResponseRedirect(reverse('main:index'))
    catalog = Catalog.objects.get(id=catalog_id)
    products = Product.objects.filter(catalog_id=catalog).select_related('vendor_id')
    images = Property.objects.filter(name='Изображение').first()
    properties = ImportantProperty.objects.filter(catalog_id=catalog).select_related('property_id')
    result = {}
    for p in products:
        result[p.id] = {'name': p.name, 'vendor': p.vendor_id.name, 'properties': {}}
        for prop in properties:
            result[p.id]['properties'][prop.property_id.id] = ''
    if images.id in properties.values_list('property_id', flat=True):
        images_value = Property_Value.objects.filter(
            product_id__in=products, property_id=images).select_related('property_id', 'product_id')
        for value in images_value:
            if not result[value.product_id.id]['properties'].get(images.id):
                result[value.product_id.id]['properties'][images.id] = []
            if value.local_value:
                result[value.product_id.id]['properties'][images.id].append(
                    "C:\\{}".format(value.local_value.replace('/', '\\')))
            else:
                result[value.product_id.id]['properties'][images.id].append(value.value)
        property_values = Property_Value.objects.filter(
            product_id__in=products, property_id__in=properties.exclude(
                property_id=images).values_list('property_id')
        ).select_related('property_id', 'product_id')
    else:
        property_values = Property_Value.objects.filter(
            product_id__in=products, property_id__in=properties.values_list('property_id')
        ).select_related('property_id', 'product_id')
    for value in property_values:
        result[value.product_id.id]['properties'][value.property_id.id] = value.value
    end = datetime.now()
    text = f'Количество товаров: {len(result)}\tВремя запроса: {end - start}'
    return render(request, 'main/export1c.html', {'catalog': catalog, 'products': result, 'properties': properties, 'image': images.id, 'text': text})


@login_required
def export_settings(request):
    start = datetime.now()
    try:
        group_id = request.POST['groupid']
    except KeyError:
        messages.info(request, 'Не указана группа для экспорта')
        return HttpResponseRedirect(reverse('main:index'))
    group = Catalog.objects.get(id=group_id)
    products = Product.objects.filter(catalog_id=group)
    property_values = Property_Value.objects.filter(product_id__in=products).values('property_id')
    properties = Property.objects.filter(id__in=property_values)
    important_properties = ImportantProperty.objects.filter(catalog_id=group).values_list('property_id', flat=True)
    example = {}
    for prop in Property_Value.objects.filter(product_id=products.first()):
        if prop.local_value:
            example[prop.property_id.id] = prop.local_value
        else:
            example[prop.property_id.id] = prop.value
    result = []
    for prop in properties:
        check = prop.id in important_properties
        value = example.get(prop.id)
        result.append({'id': prop.id, 'name': prop.name, 'check': check, 'example': value})
    end = datetime.now()
    text = f'Количество товаров: {len(result)}\tВремя запроса: {end - start}'
    return render(request, 'main/exportsettings.html', {'group': group, 'properties': result, 'example': products[:1], 'text': text})


@login_required
def export_settings_save(request):
    start = datetime.now()
    try:
        new_check = request.POST.getlist('check')
        catalog_id = request.POST['btn']
    except KeyError:
        messages.info(request, 'Ошибка: свойства для экспорта не сохранены')
        return HttpResponseRedirect(reverse('main:index'))
    catalog = Catalog.objects.get(id=catalog_id)
    old_check = ImportantProperty.objects.filter(catalog_id=catalog).values_list('property_id', flat=True)
    result_delete = [x for x in old_check if str(x) not in new_check]
    if result_delete:
        ImportantProperty.objects.filter(property_id__in=result_delete).delete()
    result_add = [x for x in new_check if int(x) not in old_check]
    if result_add:
        new_important_properties = (ImportantProperty(catalog_id=catalog, property_id=prop)
                                    for prop in Property.objects.filter(id__in=result_add))
        ImportantProperty.objects.bulk_create(new_important_properties)
    end = datetime.now()
    messages.info(request, f'Настройки обновлены. Время работы: {end - start}')
    return HttpResponseRedirect(reverse('main:index'))


@lru_cache(maxsize=100)
@login_required
def offer(request):
    start = datetime.now()
    try:
        partnumber_arr = request.GET.getlist('pn')
    except KeyError:
        messages.info(request, 'Не указана строка поиска')

    if partnumber_arr:
        partnumber_list = [item.replace('_', '#') for item in partnumber_arr]
        products = Product.objects.filter(partnumber__in=partnumber_list).select_related('catalog_id', 'vendor_id')
        last_week = datetime.now() - timedelta(days=7)
        prices = Price.objects.filter(product_id__in=products, date__gte=last_week).order_by('-date').select_related(
            "product_id", 'product_id__catalog_id', 'product_id__vendor_id', 'provider_id')
        result = prepare_view(prices, products)
        end = datetime.now()
        text = f'Найдено товаров: {len(result)-1}\tВремя запроса: {end - start}'
        return render(request, 'main/offer.html', {'result': result, 'text': text, 'page_name': 'Коммерческое предложение'})
    else:
        messages.info(request, 'Пустая строка поиска')
    return HttpResponseRedirect(reverse('main:index'))
