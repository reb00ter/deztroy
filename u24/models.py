import datetime
import os
import random

from time import sleep

import requests
from django.conf import settings
from django.db import models

# Create your models here.
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
    WAITING = 'WT'    # ожидает отправки
    SENT = 'ST'       # отправлено
    PUBLISHED = 'PU'  # опубликовано
    REMOVED = 'RM'    # удалено
    ERROR = 'ER'      # ошибка при отправке
    ERROR_APROOVE = 'EA'  # ошибка при подтверждении
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
    text = models.TextField(verbose_name="текст", max_length=350)
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

    def send(self, cron_id=""):
        s = requests.session()
        s.headers.update(settings.HEADERS)
        s.cookies.set("_ym_uid", "1503518737371134762")
        s.cookies.set("_ym_isad", "2")
        was_error = False
        self.remove()
        mboxes = Mailbox.objects.filter(active=True).order_by('?')
        available_phones = self.phones
        if available_phones.count() == 0:
            available_phones = Phone.objects.all()
        assert available_phones.count() > 0
        phone = available_phones.order_by('?').first()
        post_data = {
            'chpodrazdel': self.subcategory.category.u24id,
            'obtext': self.text,
            'obtelefon': phone.get_phone(),
            'obemail': mboxes[0].from_email,
            'chpunkt': self.subcategory.u24id,
            'cena': 0,
        }
        post_files = []

        def add_thumb_if_not_none(files, field):
            from imagekit.cachefiles import ImageCacheFile
            if field:
                image_generator = U24Thumbnail(source=field.file)
                file = ImageCacheFile(image_generator)
                file.generate()
                files.append(os.path.join(settings.MEDIA_ROOT, file.name))

        add_thumb_if_not_none(post_files, self.photo1)
        add_thumb_if_not_none(post_files, self.photo2)
        add_thumb_if_not_none(post_files, self.photo3)
        add_thumb_if_not_none(post_files, self.photo4)

        # отправка данных через селениум
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.select import Select
        # инициализация драйвера
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")  # running as root support
        driver = webdriver.Chrome(chrome_options=chrome_options)
        try:
            driver.get("https://uhta24.ru/obyavlenia/dobavit/")
            sleep(1)
            chp1 = Select(driver.find_element_by_id("chp1"))
            chp1.select_by_value(str(post_data['chpodrazdel']))
            # после выбора категории первого уровня ждём несколько секунд для загрузки категорий второго уровня
            sleep(3)
            chp2 = Select(driver.find_element_by_id("chp2"))
            chp2.select_by_value(str(post_data['chpunkt']))
            obt1 = driver.find_element_by_id("obt1")
            obt1.send_keys(post_data['obtext'])
            obtelefon = driver.find_element_by_name("obtelefon")
            obtelefon.send_keys(post_data['obtelefon'])
            obemail = driver.find_element_by_name("obemail")
            obemail.send_keys(post_data['obemail'])
            # заполняем файлинпуты
            userfiles = driver.find_elements_by_name('userfile[]')
            file_index = 0
            for userfile in userfiles:
                if file_index < len(post_files):
                    if os.path.exists(post_files[file_index]):
                        userfile.send_keys(post_files[file_index])
                    file_index += 1

            driver.find_element_by_css_selector('form[name="obformdob1"] input[type="submit"]').click()
            self.status = self.SENT
            settings.LOGGER.info("Cron %s. ID %s sent." %(cron_id, self.id))
        except Exception as e:
            self.response_text = str(e)
            self.status = self.ERROR
            was_error = True
        self.status_changed = datetime.datetime.now()
        self.save()
        return was_error

    class Meta:
        verbose_name = "объявление"
        verbose_name_plural = "объявления"

    def remove(self, cron_id=""):
        if self.remove_link and self.remove_link != "":
            r = requests.get(self.remove_link, headers=settings.HEADERS)
            settings.LOGGER.info("ID %s Removed from u24. Response: %s" %
                                 (self.id, r.status_code))
            result = r.status_code == 200
        else:
            settings.LOGGER.info("Cron %s. Deleting request for id %s. Don`t needed - not posted " % (cron_id, self.id))
            result = True
        self.remove_link = ""
        self.status = self.WAITING
        self.save()
        return result

    def aproove(self, links):
        s = requests.session()
        s.headers.update(settings.HEADERS)
        s.cookies.set("_ym_uid", "1503518737371134762")
        s.cookies.set("_ym_isad", "2")
        r = s.get(links[0])
        self.remove_link = links[1]
        if r.status_code == requests.codes.ok:
            self.status = self.PUBLISHED
            self.last_post = datetime.datetime.now()
        else:
            self.status = self.ERROR_APROOVE
        self.response_text = r.status_code
        settings.LOGGER.info("Id %s Approoved. URL was: %s" %
                             (self.id, links[0]))
        self.last_post = datetime.datetime.now()
        self.status_changed = datetime.datetime.now()
        self.save()

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
            aproove_link = msg_text[aproove_start:aproove_end].strip()
            s = requests.session()
            s.headers.update(settings.HEADERS)
            s.cookies.set("_ym_uid", "1503518737371134762")
            s.cookies.set("_ym_isad", "2")
            r = s.get(aproove_link)
            if r.status_code == requests.codes.ok:
                ad.status = cls.PUBLISHED
                ad.last_post = datetime.datetime.now()
            else:
                ad.status = cls.ERROR_APROOVE
            ad.response_text = r.status_code
            ad.last_post = datetime.datetime.now()
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


class Mailbox(models.Model):
    from_email = models.CharField(verbose_name="адрес", max_length=128)
    server = models.CharField(verbose_name="IMAP сервер", max_length=128)
    login = models.CharField(verbose_name="логин", max_length=128)
    password = models.CharField(verbose_name="пароль", max_length=128)
    active = models.BooleanField(verbose_name="включен", default=True)

    def __str__(self):
        return "%s" % self.from_email

    class Meta:
        verbose_name = "почтовый ящик"
        verbose_name_plural = "почтовые ящики"

