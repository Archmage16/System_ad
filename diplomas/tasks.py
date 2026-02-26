from celery import shared_task
from .generator import generate_diplomas
from .models import Upload


@shared_task
def process_upload(upload_id):
    upload = Upload.objects.get(id=upload_id)
    generate_diplomas(upload)