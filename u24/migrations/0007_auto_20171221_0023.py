# Generated by Django 2.0 on 2017-12-20 21:23

from django.db import migrations
import u24.models


class Migration(migrations.Migration):

    dependencies = [
        ('u24', '0006_auto_20171213_1209'),
    ]

    operations = [
        migrations.AlterField(
            model_name='phone',
            name='num',
            field=u24.models.NonStrippingCharField(max_length=50, verbose_name='номер'),
        ),
    ]
