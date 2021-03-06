# Generated by Django 2.0 on 2017-12-10 20:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('u24', '0002_auto_20171208_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advert',
            name='interval',
            field=models.PositiveSmallIntegerField(default=0, help_text='в минутах, 0 - приостановить автоматическое обновление', verbose_name='интервал'),
        ),
        migrations.AlterField(
            model_name='advert',
            name='last_post',
            field=models.DateTimeField(blank=True, null=True, verbose_name='последнее размещение'),
        ),
    ]
