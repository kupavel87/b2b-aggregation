from decimal import Decimal
from lxml import etree
import requests


def get_cbr(currency):
    url = 'http://www.cbr.ru/scripts/XML_daily.asp'
    headers = {'Content-type': 'application/json', 'charset': 'utf-8'}
    answer = requests.get(url, headers=headers)
    if answer.status_code == 200:
        root = etree.XML(answer.content)
        result = ''
        for value in root.getchildren():
            if value[1].text == currency:
                return Decimal(value[4].text.replace(',', '.'))
        else:
            print(f'Валюта {currency} не найдена')
    else:
        print('Error connect')
