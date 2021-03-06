from time import sleep

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.fields.files import ImageFieldFile
from django.http import HttpResponse, HttpResponseRedirect

# Create your views here.
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView

from deztroy.mixins import JSONResponseMixin
from mail_checker.mailer import get_links
from u24.models import Mailbox, Category, Advert, PreviewThumbnail

from exclusiveprocess import Lock, CannotAcquireLock


class Index(LoginRequiredMixin, TemplateView):
    template_name = "index.html"


class CategoriesJSON(JSONResponseMixin, LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        categories = Category.objects.all()
        categories_list = list()
        for category in categories:
            category_item = dict(id=category.id, title=category.title)
            category_item['items'] = list(category.subcategory_set.values('id', 'title'))
            category_item['opened'] = False
            categories_list.append(category_item)
        self.extra_context = dict(categories=categories_list)
        return super().get_context_data(**kwargs)

    def get_data(self, context):
        return context['categories']

    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, safe=False)


class AdsJSON(JSONResponseMixin, LoginRequiredMixin, TemplateView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.q = Q()

    def get(self, request, *args, **kwargs):
        if 'cat' in request.GET:
            self.q = Q(subcategory__category_id=request.GET.get('cat', 0))
        if 'sub' in request.GET:
            self.q = Q(subcategory_id=request.GET.get('sub', 0))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        def get_thumb_url(field: ImageFieldFile):
            from imagekit.cachefiles import ImageCacheFile
            if field:
                image_generator = PreviewThumbnail(source=field.file)
                file = ImageCacheFile(image_generator)
                file.generate()
                return file.url
            return None

        ads = Advert.objects.filter(self.q).values('id', 'text', 'title', 'status', 'interval')
        ads = list(ads)
        for ad in ads:
            advert = Advert.objects.get(id=ad['id'])
            ad['status'] = advert.get_status_display()
            ad['last_post'] = timezone.localtime(advert.last_post).strftime("%H:%M:%S %d.%m.%Y") if advert.last_post else ""
            ad['status_changed'] = timezone.localtime(advert.status_changed).strftime("%H:%M:%S %d.%m.%Y") if advert.status_changed else ""
            ad['photos'] = list()
            if advert.photo1:
                ad['photos'].append(get_thumb_url(advert.photo1))
            if advert.photo2:
                ad['photos'].append(get_thumb_url(advert.photo2))
            if advert.photo3:
                ad['photos'].append(get_thumb_url(advert.photo3))
            if advert.photo4:
                ad['photos'].append(get_thumb_url(advert.photo4))

        self.extra_context = dict(ads=ads)
        return super().get_context_data(**kwargs)

    def get_data(self, context):
        return context['ads']

    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, safe=False)


class AdvertCreate(LoginRequiredMixin, CreateView):
    model = Advert
    fields = ['subcategory', 'title', 'text', 'interval', 'phones', 'photo1', 'photo2', 'photo3', 'photo4']
    success_url = reverse_lazy('index')


class AdvertUpdate(LoginRequiredMixin, UpdateView):
    model = Advert
    fields = ['subcategory', 'title', 'text', 'interval', 'phones', 'photo1', 'photo2', 'photo3', 'photo4']
    success_url = reverse_lazy('index')


class AdvertDelete(LoginRequiredMixin, DeleteView):
    model = Advert
    success_url = reverse_lazy('index')


def notify_fail(advert: Advert):
    from django.core.mail import send_mail
    text = "При отправке объявления %s (рубрика %s) возникла проблема\n\r" \
           "Не было получено письмо от Ухта24 со ссылкой для подтверждения публикации\r\n" \
           "Текст объявления:\r\n" \
           "%s" % (advert.title, advert.subcategory.title, advert.text)
    send_mail(
        'Проблема при отправке объявления',
        text,
        settings.EMAIL_HOST_USER,
        [settings.NOTIFY_EMAIL],
        fail_silently=False,
    )


def send():
    from uuid import uuid4
    id = uuid4()
    settings.LOGGER.info("Cron %s touched. Sending" % id)
    was_action = False
    try:
        with Lock(name="send_lock"):
            for ad in Advert.objects.filter(interval__gt=0):
                settings.LOGGER.info("Cron %s. Checking ad %s" % (id, ad.id))
                if was_action:
                    sleep(150)
                    was_action = False
                ad.refresh_from_db()
                if ad.status_changed is None:
                    ad.send(id)
                    was_action = True
                    continue
                if ad.status == ad.WAITING:
                    ad.send(id)
                    was_action = True
                    continue
                if ad.last_post is not None and (ad.status != ad.SENT):
                    dt = timezone.now()-ad.last_post
                    if dt > timezone.timedelta(minutes=ad.interval):
                        ad.send(id)
                        was_action = True
                        continue
    except CannotAcquireLock:
        settings.LOGGER.info("Cron %s. Another sending cron working. Exiting" % id)
    settings.LOGGER.info("Cron %s finished" % id)


def approove():
    from uuid import uuid4
    id = uuid4()
    settings.LOGGER.info("Cron %s touched. Approoving" % id)
    try:
        with Lock(name="approove_lock"):
            for ad in Advert.objects.filter(interval__gt=0).filter(status=Advert.SENT):
                find = False
                for box in Mailbox.objects.filter(active=True):
                    settings.LOGGER.info("Cron %s. Checking links for %s in box %s" % (id, ad.id, box.login))
                    links = get_links(box.server, box.login, box.password, ad.text)
                    if links is not None:
                        ad.aproove(links)
                        find = True
                settings.LOGGER.info("Cron %s. Checking links for %s complete" % (id, ad.id))
                if not find:
                    settings.LOGGER.warn("Cron %s. Did not find links for %s" % (id, ad.id))
                    dt = timezone.now() - ad.status_changed
                    if dt > timezone.timedelta(minutes=ad.interval):
                        notify_fail(ad)
                        ad.remove(id)
    except CannotAcquireLock:
        settings.LOGGER.info("Cron %s. Another approoving cron working. Exiting" % id)
    settings.LOGGER.info("Cron %s finished" % id)


def cron(request):
    send()
    approove()
    return HttpResponse('OK')


def stop_all(request):
    for ad in Advert.objects.all():
        ad.interval = 0
        ad.save()
    return HttpResponseRedirect("/")


def start_all(request):
    for ad in Advert.objects.all():
        ad.interval = 120
        ad.save()
    return HttpResponseRedirect("/")


def reset_all(request):
    for ad in Advert.objects.all():
        ad.remove()
    return HttpResponseRedirect("/")


def push_now(request):
    for ad in Advert.objects.filter(interval__gt=0):
        ad.remove()
        ad.send()
    return HttpResponseRedirect("/")
