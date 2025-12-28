from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Incident
from .telegram import send_telegram_message

@receiver(post_save, sender=Incident)
def incident_created(sender, instance, created, **kwargs):
    if created:
        message = (
            "🚨 <b>Новый инцидент</b>\n\n",
            {instance}
        )
        send_telegram_message(message)
