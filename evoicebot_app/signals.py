from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Document
from .utils.notification_utils import schedule_deadline_alerts, cancel_deadline_alerts


@receiver(post_save, sender=Document)
def document_saved(sender, instance, created, **kwargs):
    if instance.deadline:
        schedule_deadline_alerts(instance)


@receiver(post_delete, sender=Document)
def document_deleted(sender, instance, **kwargs):
    cancel_deadline_alerts(instance)
