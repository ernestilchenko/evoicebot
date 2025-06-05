from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Setup Celery periodic tasks'

    def handle(self, *args, **options):
        daily_schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )

        hourly_schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )

        PeriodicTask.objects.get_or_create(
            name='Daily cleanup of old files',
            defaults={
                'interval': daily_schedule,
                'task': 'evoicebot_app.tasks.cleanup_old_files',
                'enabled': True,
            }
        )

        PeriodicTask.objects.get_or_create(
            name='Hourly document expiry notifications',
            defaults={
                'interval': hourly_schedule,
                'task': 'evoicebot_app.tasks.send_document_expiry_notifications',
                'enabled': True,
            }
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully set up Celery periodic tasks')
        )