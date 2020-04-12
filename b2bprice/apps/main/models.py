from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class ProviderAPI(models.Model):
    name = models.CharField('Название поставщика', max_length=20)
    url = models.CharField('Url адрес API', max_length=100)
    headers = models.CharField('Заголовок запроса', max_length=100, blank=True)
    catalog = models.TextField('Запрос каталога', blank=True)
    data = models.TextField('Запрос цены', blank=True)
    detail_url = models.CharField('Url подробной информации', max_length=100, blank=True)
    detail_info = models.TextField('Запрос подробной информации', blank=True)

    def __str__(self):
        return f'<{self.name}>'

    class Meta:
        verbose_name = 'Настройки API'
        verbose_name_plural = 'Настройки API'
        # app_label = 'b2bprice.apps'


class Catalog(MPTTModel):
    name = models.CharField(max_length=50)
    parent = TreeForeignKey('self', on_delete=models.CASCADE,
                            null=True, blank=True, related_name='children')
    export = models.BooleanField('Можно экспортировать', default=False)

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return f'<{self.name}>'

    class Meta:
        verbose_name = 'Каталог'
        verbose_name_plural = 'Каталоги'


class Catalog_mapping(models.Model):
    catalog_id = models.ForeignKey(Catalog, on_delete=models.CASCADE, related_name="provider_ids")
    provider_id = models.ForeignKey(ProviderAPI, on_delete=models.CASCADE)
    value = models.CharField('Код поставщика', max_length=50, blank=True)

    class Meta:
        verbose_name = 'ИД производителя'
        verbose_name_plural = 'Таблица соответсвия каталогов'

    def __str__(self):
        return f'<{self.catalog_id.name} - {self.provider_id.name}>'


class Vendor(models.Model):
    name = models.CharField('Название', max_length=50, unique=True)

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'

    def __str__(self):
        return f'<{self.name}>'


class Product(models.Model):
    name = models.TextField('Описание')
    catalog_id = models.ForeignKey(Catalog, on_delete=models.CASCADE, related_name="products")
    partnumber = models.CharField('Артикул производителя', max_length=50)
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f'<{self.partnumber}>'

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def important_property(self):
        propety_list = ImportantProperty.objects.filter(catalog_id=self.catalog_id).values_list('property_id')
        return Property_Value.objects.filter(product_id=self).filter(property_id__in=propety_list)


class Product_mapping(models.Model):
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="provider_ids")
    provider_id = models.ForeignKey(ProviderAPI, on_delete=models.CASCADE)
    value = models.CharField('Код поставщика', max_length=50, blank=True)

    class Meta:
        verbose_name = 'ИД производителя'
        verbose_name_plural = 'Таблица соответсвия товаров'

    def __str__(self):
        return f'<{self.product_id.id} - {self.provider_id.name}>'


class Price(models.Model):
    provider_id = models.ForeignKey(ProviderAPI, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE,
                                   related_name="prices", related_query_name="price")
    balance = models.CharField('Остаток', max_length=10)
    value = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    currency = models.CharField('Валюта', max_length=10)
    date = models.DateTimeField('Дата')

    class Meta:
        verbose_name = 'Цена и остатки'
        verbose_name_plural = 'Цены и остатки'

    def __str__(self):
        return f'<{self.product_id.partnumber}>-<{self.date.strftime("%d.%m.%Y %H:%M")}>'


class Property(models.Model):
    name = models.CharField('Название', max_length=50)
    unit = models.CharField('Еденицы измерения', max_length=50, blank=True)
    type = models.CharField('Тип свойства', max_length=1,
                            choices=(('1', 'basic'), ('2', 'personal'), ('3', 'Изображение')))

    class Meta:
        verbose_name = 'Свойство'
        verbose_name_plural = 'Свойства'

    def __str__(self):
        return f'<{self.name}>'


class Property_mapping(models.Model):
    property_id = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="property_ids")
    provider_id = models.ForeignKey(ProviderAPI, on_delete=models.CASCADE)
    value = models.CharField('Код поставщика', max_length=50, blank=True)

    class Meta:
        verbose_name = 'ИД производителя'
        verbose_name_plural = 'Таблица соответсвия свойств'

    def __str__(self):
        return f'<{self.property_id.id} - {self.provider_id.name}>'


class Property_Value(models.Model):
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE,
                                   related_name="properties")
    property_id = models.ForeignKey(Property, on_delete=models.CASCADE)
    value = models.TextField('Значение')
    local_value = models.TextField('Внутренне значение', blank=True)

    class Meta:
        verbose_name = 'Значение свойства'
        verbose_name_plural = 'Значения свойст'

    def __str__(self):
        return f'<{self.product_id.partnumber}>-<{self.property_id.name}>'


class ImportantProperty(models.Model):
    catalog_id = models.ForeignKey(Catalog, on_delete=models.CASCADE)
    property_id = models.ForeignKey(Property, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Свойство'
        verbose_name_plural = 'Свойства для экспорта'

    def __str__(self):
        return f'<{self.catalog_id.name}>-<{self.property_id.name}>'
