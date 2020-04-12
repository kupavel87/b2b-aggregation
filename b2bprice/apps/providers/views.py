from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from providers.providers import get_provider_catalog, get_provider_price, get_provider_product_detail
from main.models import ProviderAPI, Catalog, Catalog_mapping


@login_required
def index(request):
    providers = ProviderAPI.objects.all()
    return render(request, 'providers/index.html', {'providers': providers})


@login_required
def catalog(request):
    try:
        provider_id = int(request.POST.get('provider_id'))
    except KeyError:
        messages.info(request, 'Ошибка: поставщик не найден')
        return HttpResponseRedirect(reverse('main:providers'))
    arg = get_provider_catalog(provider_id)
    catalog = Catalog.objects.all()
    catalog_mapping = Catalog_mapping.objects.filter(provider_id=provider_id).select_related('catalog_id')
    mapping = {}
    for item in catalog_mapping:
        mapping[item.value] = item.catalog_id.id
    provider = arg.get('provider')
    provider_name = '???'
    if provider:
        provider_name = provider.name
    arg.update({'page_name': f"Каталог поставщика: {provider_name}.", 'catalog': catalog, 'mapping': mapping})
    return render(request, 'providers/catalog.html', arg)


@login_required
def price(request):
    try:
        provider_id = int(request.POST.get('provider_id'))
        category = request.POST.get('category')
    except KeyError:
        messages.info(request, 'Ошибка: категориия не указана')
        return HttpResponseRedirect(reverse('main:providers'))
    if not category:
        messages.info(request, 'Ошибка: категориия не указана')
        return HttpResponseRedirect(reverse('main:providers'))
    arg = get_provider_price(provider_id, category)
    arg.update({'page_name': f"Категория: {arg.get('category')}. Поставщик: {arg.get('provider').name}."})
    return render(request, 'providers/price.html', arg)


@login_required
def product_detail(request):
    try:
        provider_id = int(request.POST.get('provider_id'))
        partname = request.POST.get('partnumber')
    except KeyError:
        messages.info(request, 'Ошибка: продукт не указан')
        return HttpResponseRedirect(reverse('main:providers'))
    if not partname:
        messages.info(request, 'Ошибка: продукт не указан')
        return HttpResponseRedirect(reverse('main:providers'))
    arg = get_provider_product_detail(provider_id, partname)
    return render(request, 'providers/product_detail.html', arg)


@login_required
def save_mapping(request):
    start = datetime.now()
    try:
        provider_id = request.POST.get('provider_id')
        catalog_list = request.POST.getlist('catalog')
        category_list = request.POST.getlist('category')
    except KeyError:
        messages.info(request, 'Ошибка параметров')
        return HttpResponseRedirect(reverse('providers:index'))
    new_mapping = {catalog_list[i]: int(category_list[i]) for i in range(len(category_list)) if category_list[i] != '0'}
    provider = ProviderAPI.objects.get(id=provider_id)
    mapping = Catalog_mapping.objects.filter(provider_id=provider)
    delete_list = [x.id for x in mapping if x.value not in new_mapping]
    Catalog_mapping.objects.filter(id__in=delete_list).delete()

    mapping = Catalog_mapping.objects.filter(provider_id=provider).select_related('catalog_id')
    edit_list = {}
    for item in mapping:
        i = new_mapping[item.value]
        if item.catalog_id.id != i:
            edit_list[i] = edit_list.get(i, [])
            edit_list[i].append(item)
    if edit_list:
        catalog_db = Catalog.objects.filter(id__in=edit_list)
        for catalog in catalog_db:
            for item in edit_list[catalog.id]:
                item.catalog_id = catalog
        Catalog_mapping.objects.bulk_update(mapping, ['catalog_id'])

    mapping_values = [x.value for x in mapping]
    new_list = {}
    for k, v in new_mapping.items():
        if k not in mapping_values:
            new_list[v] = new_list.get(v, [])
            new_list[v].append(k)
    if new_list:
        catalog_db = Catalog.objects.filter(id__in=new_list)
        items = (Catalog_mapping(catalog_id=catalog, provider_id=provider, value=v)
                 for catalog in catalog_db for v in new_list[catalog.id])
        Catalog_mapping.objects.bulk_create(items)

    end = datetime.now()
    text = f'Удалено: {len(delete_list)}\tИзменено: {len(edit_list)}\tДобавлено: {len(new_list)}\tВремя запроса: {end - start}'
    messages.info(request, text)
    return HttpResponseRedirect(reverse('providers:index'))
