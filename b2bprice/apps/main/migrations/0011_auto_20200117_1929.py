# Generated by Django 2.1.13 on 2020-01-17 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_auto_20191220_1426'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='id_treolan',
            field=models.CharField(blank=True, max_length=50, verbose_name='id в Treolan'),
        ),
    ]
