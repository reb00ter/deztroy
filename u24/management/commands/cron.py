from django.core.management.base import BaseCommand
from u24.views import cron
__author__ = 'reb00ter'


class Command(BaseCommand):
    help = "Выполняет синхронизацию с Ухта24"

    def handle(self, *args, **options):
        cron(None)
