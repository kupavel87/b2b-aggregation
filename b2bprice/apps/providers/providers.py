import ast
from decimal import Decimal
from html import unescape
from lxml import etree
import requests

from main.models import ProviderAPI
from main.decorators import duration_time


def str2float(float_str):
    if not float_str:
        return float_str
    try:
        return float(float_str)
    except ValueError:
        return float_str


@duration_time
def get_provider_catalog(id):
    try:
        api = ProviderAPI.objects.get(id=id)
    except KeyError:
        return {'text': 'Ошибка: Провайдер не найден'}
    try:
        answer = requests.post(api.url, data=api.catalog.encode('utf-8'),
                               headers=ast.literal_eval(api.headers))
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return {'text': 'Ошибка: Провайдер не отвечает'}
    result = []
    if answer.status_code == 200:
        xml = unescape(answer.content.decode('utf-8'))
        root = etree.XML(xml.encode())
        if api.id == 1:
            all_categories = root.findall('.//{http://tempuri.org/}Category')
            for category in all_categories:
                if (len(category.getchildren()) > 3 and category.getchildren()[3].text == '2'):
                    result.append({'id': category.getchildren()[0].text,
                                   'name': category.getchildren()[1].text, 'level': 0})
                    for subcategory in all_categories:
                        if (len(category.getchildren()) > 3 and
                                subcategory.getchildren()[2].text == category.getchildren()[0].text):
                            result.append({'id': subcategory.getchildren()[0].text,
                                           'name': subcategory.getchildren()[1].text, 'level': 1})
                            for subsubcategory in all_categories:
                                if (len(category.getchildren()) > 3 and
                                        subsubcategory.getchildren()[2].text == subcategory.getchildren()[0].text):
                                    result.append({'id': subsubcategory.getchildren()[0].text,
                                                   'name': subsubcategory.getchildren()[1].text, 'level': 2})
            text = f'Количество групп: {len(result)}'
        elif api.id == 2:
            all_categories = root.findall('.//category')
            for category in all_categories:
                if category.get('parent') == '04030AB1-678B-457D-8976-AC7297C65CE6':
                    result.append({'id': category.get('id'),
                                   'name': category.get('name'), 'level': 0})
                    for subcategory in all_categories:
                        if subcategory.get('parent') == category.get('id'):
                            result.append({'id': subcategory.get('id'),
                                           'name': subcategory.get('name'), 'level': 1})
                            for subsubcategory in all_categories:
                                if subsubcategory.get('parent') == subcategory.get('id'):
                                    result.append({'id': subsubcategory.get('id'),
                                                   'name': subsubcategory.get('name'), 'level': 2})
            text = f'Количество групп: {len(result)}'
        else:
            text = f"Ошибка. Неизвестный поставщик id={api.id}"
    else:
        text = f"Ошибка у провайдера - {answer.status_code}"
    return {'provider': api, 'provider_catalog': result, 'text': text}


@duration_time
def get_provider_price(id, category, api=None):
    if not api:
        try:
            api = ProviderAPI.objects.get(id=id)
        except KeyError:
            return {'text': 'Ошибка: Провайдер не найден'}
    data = api.data.format(category)
    try:
        answer = requests.post(api.url, data=data.encode('utf-8'), headers=ast.literal_eval(api.headers))
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return {'text': 'Ошибка: Провайдер не отвечает'}
    price = {}
    if answer.status_code == 200:
        xml = unescape(answer.content.decode('utf-8'))
        try:
            root = etree.XML(xml.encode())
        except etree.XMLSyntaxError:
            root = etree.XML(answer.content)

        if api.id == 1:
            all_products = root.findall('.//{http://tempuri.org/}Product')
            for product in all_products:
                attr = product.getchildren()
                text = ''
                storage = attr[-1].getchildren()[0].getchildren()
                if storage[-1].text == '1':
                    balance = '∞'
                else:
                    balance = storage[1].text
                price[attr[1].text] = {
                    'id': attr[0].text, 'partnumber': attr[1].text,
                    'vendor': attr[2].text, 'name': attr[3].text,
                    'price': Decimal(attr[7].text[:-10]), 'currency': attr[8].text,
                    'balance': balance
                }
                category = attr[26].text
            text = f'Количество товаров: {len(price)}'
        elif api.id == 2:
            all_products = root.findall('.//position')
            for product in all_products:
                price[product.get('articul')] = {
                    'id': product.get('id'), 'partnumber': product.get('articul'),
                    'vendor': product.get('vendor'), 'name': product.get('name'),
                    'price': Decimal(product.get('price')), 'currency': product.get('currency'),
                    'balance': product.get('freenom')
                }
                category = product.getparent().get('name')
            text = f'Количество товаров: {len(price)}'
        else:
            text = f"Ошибка. Неизвестный поставщик id={api.id}"
    else:
        text = f"Ошибка у провайдера - {answer.status_code}"
    return {'price': price, 'category': category, 'provider': api, 'text': text}


@duration_time
def get_provider_product_detail(id, partnumber, api=None):
    """Получение подробной информации от поставщика"""
    if not api:
        try:
            api = ProviderAPI.objects.get(id=id)
        except KeyError:
            return {'text': 'Ошибка: Провайдер не найден'}
    data = api.detail_info.format(partnumber)
    try:
        answer = requests.post(api.detail_url, data=data.encode(
            'utf-8'), headers=ast.literal_eval(api.headers))
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return {'text': 'Ошибка: Провайдер не отвечает'}
    result = {}
    text = ''
    if answer.status_code == 200:
        root = etree.XML(answer.content)
        if api.id == 1:
            return {'text': "Ошибка: Поставщик не предоставляет информацию"}
        elif api.id == 2:
            product = root.find('.//Product')
            if product is not None:
                result['name'] = product.get('ShortDesc')
                result['basic'] = {}
                result['basic']['Короткое имя'] = ' '.join(result['name'].split()[:3])
                result['basic']['Артикул'] = product.get('Articul')
                result['basic']['Вес'] = str(str2float(product.get('WeightBrutto', '')))
                result['basic']['Длинна'] = str(str2float(product.get('Length', '')))
                result['basic']['Ширина'] = str(str2float(product.get('Width', '')))
                result['basic']['Высота'] = str(str2float(product.get('Height', '')))

                allpropertes = root.findall('.//Property')
                result['personal'] = {}
                for property in allpropertes:
                    result['personal'][property.get('ID')] = {
                        'name': property.get('Name'), 'value': property.get('Value')}

                allpictures = root.findall('.//row')
                result['Изображение'] = []
                for picture in allpictures:
                    result['Изображение'].append(picture.get('Link'))
                text = f"Всего {len(result['basic']) + len(result['personal'])} свойств и {len(result['Изображение'])} изображений."
        else:
            text = f"Ошибка. Неизвестный поставщик id={api.id}"
    else:
        text = f"Ошибка у провайдера - {answer.status_code}"
    return {'property': result, 'provider': api, 'text': text}
