# Generated by Django 2.1.13 on 2019-10-31 19:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_auto_20191031_2152'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapping',
            name='group',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='main.ProductType'),
            preserve_default=False,
        ),
    ]
