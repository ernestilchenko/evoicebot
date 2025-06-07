import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Start Celery Beat scheduler'

    def handle(self, *args, **options):
        os.system('celery -A evoicebot beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler')
