# Generated by Django 2.2.5 on 2019-10-21 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_name', models.CharField(max_length=20, verbose_name='Название типа')),
                ('partner1', models.CharField(max_length=10, verbose_name='Первый партнер')),
            ],
            options={
                'verbose_name': 'Тип номенклатуры',
                'verbose_name_plural': 'Типы номенклатуры',
            },
        ),
    ]
