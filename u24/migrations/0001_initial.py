# Generated by Django 2.0 on 2017-12-02 22:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Advert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='чтобы не запутаться', max_length=255, verbose_name='название')),
                ('text', models.TextField(verbose_name='текст')),
                ('photo1', models.ImageField(blank=True, null=True, upload_to='', verbose_name='Фото1')),
                ('photo2', models.ImageField(blank=True, null=True, upload_to='', verbose_name='Фото2')),
                ('photo3', models.ImageField(blank=True, null=True, upload_to='', verbose_name='Фото3')),
                ('photo4', models.ImageField(blank=True, null=True, upload_to='', verbose_name='Фото4')),
                ('interval', models.PositiveSmallIntegerField(help_text='в минутах', verbose_name='интервал')),
                ('status', models.CharField(choices=[('WT', 'Ожидает'), ('ST', 'Отправлено'), ('PU', 'Опубликовано'), ('RM', 'Удалено'), ('ER', 'Ошибка'), ('EA', 'Ошибка подтверждения публикации')], default='WT', max_length=2, verbose_name='статус')),
                ('status_changed', models.DateTimeField(auto_now=True)),
                ('remove_link', models.URLField(blank=True, null=True, verbose_name='URL для удаления')),
            ],
            options={
                'verbose_name': 'объявление',
                'verbose_name_plural': 'объявления',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='название')),
            ],
            options={
                'verbose_name': 'категория',
                'verbose_name_plural': 'категории',
            },
        ),
        migrations.CreateModel(
            name='Phone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num', models.CharField(help_text='обязтельно без 8', max_length=10, verbose_name='номер')),
            ],
            options={
                'verbose_name': 'телефон',
                'verbose_name_plural': 'телефоны',
            },
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='название')),
                ('u24id', models.PositiveSmallIntegerField(help_text='Код подраздела на Ухта24', verbose_name='код подраздела')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='u24.Category', verbose_name='категория')),
            ],
            options={
                'verbose_name': 'подкатегория',
                'verbose_name_plural': 'подкатегории',
            },
        ),
        migrations.AddField(
            model_name='advert',
            name='phones',
            field=models.ManyToManyField(to='u24.Phone', verbose_name='выбранные телефоны'),
        ),
        migrations.AddField(
            model_name='advert',
            name='subcategory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='u24.SubCategory', verbose_name='подкатегория'),
        ),
    ]
