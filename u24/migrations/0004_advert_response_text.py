# Generated by Django 2.0 on 2017-12-10 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('u24', '0003_auto_20171210_2320'),
    ]

    operations = [
        migrations.AddField(
            model_name='advert',
            name='response_text',
            field=models.CharField(default='', max_length=255, verbose_name='ответ сервера'),
            preserve_default=False,
        ),
    ]
