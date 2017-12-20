import datetime
import random

import os

import requests
from django.db import models

# Create your models here.
from django.dispatch import receiver
from django_mailbox.models import Mailbox
from django_mailbox.signals import message_received
from imagekit import ImageSpec
from pilkit.processors import Transpose, ResizeToFill
from urllib3.exceptions import IncompleteRead


class NonStrippingCharField(models.CharField):
    """CharField который не стрипит пробелы"""
    def formfield(self, **kwargs):
        kwargs['strip'] = False
        return super(NonStrippingCharField, self).formfield(**kwargs)


class Category(models.Model):
    title = models.CharField(verbose_name="название", max_length=255)
    u24id = models.PositiveSmallIntegerField(verbose_name="код раздела", help_text="Код раздела на Ухта24")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"


class SubCategory(models.Model):
    category = models.ForeignKey(Category, verbose_name="категория", on_delete=models.CASCADE)
    title = models.CharField(verbose_name="название", max_length=255)
    u24id = models.PositiveSmallIntegerField(verbose_name="код подраздела", help_text="Код подраздела на Ухта24")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "подкатегория"
        verbose_name_plural = "подкатегории"


class Phone(models.Model):
    num = NonStrippingCharField(max_length=50, verbose_name="номер")

    def __str__(self):
        return self.num

    def get_variant(self, variant: int):
        if variant == 0:
            return "+7%s" % self.num
        elif variant == 1:
            return "8%s" % self.num
        elif variant == 2:
            return "+7%s-%s-%s" % (self.num[0:5], self.num[5:7], self.num[7:10])
        elif variant == 3:
            return "8%s-%s-%s" % (self.num[0:5], self.num[5:7], self.num[7:10])
        elif variant == 4:
            return "+7(%s)%s-%s-%s" % (self.num[0:3], self.num[3:5], self.num[5:7], self.num[7:10])
        elif variant == 5:
            return "8(%s)%s-%s-%s" % (self.num[0:3], self.num[3:5], self.num[5:7], self.num[7:10])

    def get_random_variant(self):
        variant = random.randint(0, 5)
        return self.get_variant(variant)

    def get_default_variant(self):
        return self.num

    def get_phone(self):
        return self.get_default_variant()

    class Meta:
        verbose_name = "телефон"
        verbose_name_plural = "телефоны"


class U24Thumbnail(ImageSpec):
    processors = [Transpose(), ResizeToFill(800, 600)]
    format = 'JPEG'
    options = {'quality': 80}


class PreviewThumbnail(ImageSpec):
    processors = [Transpose(), ResizeToFill(100, 100)]
    format = 'JPEG'
    options = {'quality': 80}


class Advert(models.Model):
    WAITING = 'WT'
    SENT = 'ST'
    PUBLISHED = 'PU'
    REMOVED = 'RM'
    ERROR = 'ER'
    ERROR_APROOVE = 'EA'
    STATUS_CHOICES = (
        (WAITING, 'Ожидает'),
        (SENT, 'Отправлено'),
        (PUBLISHED, 'Опубликовано'),
        (REMOVED, 'Удалено'),
        (ERROR, 'Ошибка'),
        (ERROR_APROOVE, 'Ошибка подтверждения публикации')
    )
    title = models.CharField(verbose_name="название", max_length=255, help_text="чтобы не запутаться")
    subcategory = models.ForeignKey(SubCategory, verbose_name="подкатегория", on_delete=models.CASCADE)
    text = models.TextField(verbose_name="текст")
    photo1 = models.ImageField(verbose_name="Фото1", null=True, blank=True)
    photo2 = models.ImageField(verbose_name="Фото2", null=True, blank=True)
    photo3 = models.ImageField(verbose_name="Фото3", null=True, blank=True)
    photo4 = models.ImageField(verbose_name="Фото4", null=True, blank=True)
    interval = models.PositiveSmallIntegerField(verbose_name="интервал", default=0,
                                                help_text="в минутах, 0 - приостановить автоматическое обновление")
    phones = models.ManyToManyField(Phone, verbose_name="выбранные телефоны")
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=WAITING, verbose_name="статус")
    status_changed = models.DateTimeField(auto_now=True)
    remove_link = models.URLField(verbose_name="URL для удаления", null=True, blank=True)
    last_post = models.DateTimeField(verbose_name="последнее размещение", null=True, blank=True)
    response_text = models.CharField(verbose_name="ответ сервера", max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title

    def category(self):
        return self.subcategory.category.title

    category.short_description = 'категория'

    def send(self):
        was_error = False
        self.remove()
        mboxes = Mailbox.objects.filter(active=True).order_by('?')
        available_phones = self.phones
        if available_phones.count() == 0:
            available_phones = Phone.objects.all()
        assert available_phones.count() > 0
        phone = available_phones.order_by('?').first()
        post_data = [
            ("chpodrazdel", self.subcategory.category.u24id),
            ("obtext", self.text.encode('windows-1251')),
            ("obtelefon", phone.get_phone().encode('windows-1251')),
            ("obemail", mboxes[0].from_email),
            ("chpunkt", self.subcategory.u24id),
            ("punkt3", self.subcategory.u24id)
        ]
        post_files = []

        def add_thumb_if_not_none(files, field):
            from imagekit.cachefiles import ImageCacheFile
            if field:
                image_generator = U24Thumbnail(source=field.file)
                file = ImageCacheFile(image_generator)
                file.generate()
                print(file.path)
                files.append(("userfile[]", open(file.path, 'rb')))

        add_thumb_if_not_none(post_files, self.photo1)
        add_thumb_if_not_none(post_files, self.photo2)
        add_thumb_if_not_none(post_files, self.photo3)
        add_thumb_if_not_none(post_files, self.photo4)
        url = "http://www.uhta24.ru/obyavlenia/dobavit/"
        try:
            r = requests.post(url, data=post_data, files=post_files)
            self.response_text = r.status_code
            if r.status_code == requests.codes.ok:
                self.status = self.SENT
            else:
                self.status = self.ERROR
                was_error = True
        except IncompleteRead:
            self.status = self.ERROR
            was_error = True
        self.status_changed = datetime.datetime.now()
        self.save()
        return was_error

    class Meta:
        verbose_name = "объявление"
        verbose_name_plural = "объявления"

    def remove(self):
        if self.remove_link and self.remove_link != "":
            r = requests.get(self.remove_link)
            self.remove_link = ""
            self.status = self.WAITING
            self.save()
            return r.status_code == 200
        return True

    @classmethod
    def fill_ad_by_message(cls, msg_text):
        adv_start = msg_text.find("\r\n\r\n") + 4
        adv_start = msg_text.find("\r\n\r\n", adv_start) + 4
        adv_end = msg_text.find("\r\n\r\n", adv_start)
        adv_text = msg_text[adv_start:adv_end]
        for ad in cls.objects.filter(status=cls.SENT):
            if ad.text != adv_text:
                continue
            remove_start = 0
            aproove_start = msg_text.find("http")
            aproove_end = msg_text.find("\r\n\r\n", aproove_start)
            aproove_link = msg_text[aproove_start:aproove_end]
            r = requests.get(aproove_link)
            if r.status_code == requests.codes.ok:
                ad.status = cls.PUBLISHED
                ad.last_post = datetime.datetime.now()
            else:
                ad.status = cls.ERROR_APROOVE
            ad.response_text = r.status_code
            ad.status_changed = datetime.datetime.now()
            ad.save()
            try:
                remove_start = msg_text.find("http", aproove_end)
                ad.remove_link = msg_text[remove_start:]
                ad.save()
                return True
            except:
                ad.response_text = "ошибка поиска ссылки для удаления remove_start=" + remove_start.__str__()
                ad.save()
                return False


@receiver(message_received)
def process_mail(sender, message, **args):
    try:
        from_header = message.from_header
    except:
        return
    if (from_header != 'noreply@uhta24.ru') and (from_header != 'Uhta24 <noreply@uhta24.ru>'):
        return
    if Advert.fill_ad_by_message(message.text):
        message.delete()
