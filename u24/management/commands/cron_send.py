from django.core.management.base import BaseCommand
from u24.views import send
__author__ = 'reb00ter'


class Command(BaseCommand):
    help = "Выполняет синхронизацию с Ухта24"

    def handle(self, *args, **options):
        send()
