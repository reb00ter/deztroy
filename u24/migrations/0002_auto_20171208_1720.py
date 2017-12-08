# Generated by Django 2.0 on 2017-12-08 14:20

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('u24', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='advert',
            name='last_post',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='последнее размещение'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='u24id',
            field=models.PositiveSmallIntegerField(default=1, help_text='Код раздела на Ухта24', verbose_name='код раздела'),
            preserve_default=False,
        ),
    ]
