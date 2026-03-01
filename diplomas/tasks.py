from celery import shared_task
from .models import Upload
from .generator import generate_diplomas


@shared_task
def process_upload(upload_id):

    upload = Upload.objects.get(id=upload_id)
    upload.status = "processing"
    upload.save()

    generate_diplomas(upload)

    upload.status = "done"
    upload.save()