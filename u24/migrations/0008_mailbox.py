# Generated by Django 2.0 on 2018-07-04 02:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('u24', '0007_auto_20171221_0023'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mailbox',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('server', models.CharField(max_length=128, verbose_name='IMAP сервер')),
                ('login', models.CharField(max_length=128, verbose_name='логин')),
                ('password', models.CharField(max_length=128, verbose_name='пароль')),
                ('active', models.BooleanField(default=True, verbose_name='включен')),
            ],
            options={
                'verbose_name': 'почтовый ящик',
                'verbose_name_plural': 'почтовые ящики',
            },
        ),
    ]
