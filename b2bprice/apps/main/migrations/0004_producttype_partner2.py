# Generated by Django 2.2.5 on 2019-10-28 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20191028_0235'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttype',
            name='partner2',
            field=models.CharField(default='', max_length=40, verbose_name='Название у партнера (Treolan)'),
            preserve_default=False,
        ),
    ]
