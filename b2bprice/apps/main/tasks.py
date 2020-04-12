from smtplib import SMTPException

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string

from background_task import background
from .models import Property_Value, Catalog
import requests
from datetime import datetime
from pathlib import Path
from .update_product import prepare_update


@background()
def task_test(text, arr=[]):
    print('Tasks works!')
    print(text)
    if arr:
        print(arr)


@background()
def sendmail_test(send_to=[]):
    print('Отправка тестового письма')
    msg = EmailMessage('A1 Cloud b2b', 'Проверка работы почты', to=send_to)
    msg.send()


@background
def task_update_catalog(name, send_to=[]):
    start = datetime.now()
    print('{} - Start update task'.format(start.strftime('%d-%m-%Y %H:%M:%S')))
    result = prepare_update(name=name, date=start)
    if send_to:
        body = render_to_string('email/update.html', {'result': result, "date": start})
        email = EmailMultiAlternatives('A1 Cloud обновление', "Обновление завершено", to=send_to)
        email.attach_alternative(body, "text/html")
        try:
            email.send()
        except SMTPException:
            with open(f"log/{start.strftime('%d-%m-%Y %H:%M:%S')}.html", 'w', encoding='utf-8') as f:
                f.write(body)
    end = datetime.now()
    print('{} - End update task. {}'.format(end.strftime('%d-%m-%Y %H:%M:%S'), end - start))


@background
def delete_catalog(name):
    start = datetime.now()
    print('{} - Start delete catalog task'.format(start.strftime('%d-%m-%Y %H:%M:%S')))
    Catalog.objects.get(name=name).delete()
    end = datetime.now()
    print('{} - End update task. {}'.format(end.strftime('%d-%m-%Y %H:%M:%S'), end - start))


@background
def download_images(folder):
    start = datetime.now()
    print('{} - Start download images task'.format(start.strftime('%d-%m-%Y %H:%M:%S')))
    images = Property_Value.objects.filter(property_id__type=3, local_value=''
                                           ).select_related('product_id', 'product_id__catalog_id')
    k = 1
    lastid = ''
    for image in images:
        if image.product_id.id == lastid:
            k += 1
        else:
            lastid = image.product_id.id
            k = 1
        file = requests.get(image.value)
        folder_name = f"{folder}/{image.product_id.catalog_id.name.replace(' ', '-')}"
        Path(folder_name).mkdir(parents=True, exist_ok=True)
        name = f"{folder_name}/{image.product_id.partnumber.replace('/', '_').replace('#','_')}-{k}.png"
        if open(name, 'wb').write(file.content):
            image.local_value = name
            image.save()
    end = datetime.now()
    print('{} - End download images task. {}'.format(end.strftime('%d-%m-%Y %H:%M:%S'), end - start))
