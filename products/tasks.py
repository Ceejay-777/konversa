from django.utils import timezone

from celery import shared_task
from django_eventstream import send_event

from integrations.telegram.services import TelegramPublishingService
from integrations.telegram.exceptions import TelegramAPIError
from integrations.ai.captioning.services import generate_caption
from integrations.ai.captioning.exceptions import CaptionBusinessError, CaptionInfrastructureError

from .models import Publication, AiCaption, AiCaptionJob, PublicationJob

from stores.models import Connection
from konversa.utils import get_job_channel
from konversa.models import Status

PUBLISHING_SERVICE = {
    "telegram": TelegramPublishingService
}

@shared_task(autoretry_for=(TelegramAPIError,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def publish_product_task(connection_id, publication_id, job_id):
    connection = Connection.objects.get(id=connection_id)
    publication = Publication.objects.get(id=publication_id)
    job = PublicationJob.objects.get(id=job_id)
    
    product = publication.product
    platform = connection.platform
    channel = get_job_channel("publication", job.sqid)

    job.status = Status.PROCESSING
    job.save(update_fields=["status"])
    
    publication.status = Status.PROCESSING
    publication.save(update_fields=["status"])

    service_class = PUBLISHING_SERVICE.get(platform)

    if not service_class:
        raise Exception(f"Platform {platform} is not supported")

    service = service_class()

    try:
        post_id = service.publish(connection.account_id, product)

        publication.status = Status.SUCCESS
        publication.post_id = post_id
        publication.save(update_fields=["status", "post_id"])
        
        send_event(channel=channel, event_type="publication.success", data={
                "type": "publication.success",
                "timestamp": timezone.now().isoformat(),
                "job_id": job.sqid,
                "data": {
                    "product_id": product.sqid,
                    "status": publication.status,
                }})
        
        return True

    except Exception as e:
        publication.status = Status.FAILED
        publication.save(update_fields=["status"])

        raise    

@shared_task(bind=True, max_retries=3)
def generate_ai_caption_task(self, ai_caption_id):
    ai_caption = AiCaption.objects.select_related("product", "job").get(id=ai_caption_id)
    product = ai_caption.product
    job = ai_caption.job
    channel = get_job_channel("ai-caption", job.sqid)
    
    try:
        caption, ai_model = generate_caption(product) # TODO: Add seller profile data
        
        ai_caption.ai_generated_text = caption
        ai_caption.ai_model = ai_model
        ai_caption.status = Status.SUCCESS
        ai_caption.save(update_fields=["ai_generated_text", "ai_model", "status"])
        
        send_event(channel=channel, event_type="caption.generated", data={
                "type": "caption.generated",
                "timestamp": timezone.now().isoformat(),
                "job_id": job.sqid,
                "data": {
                    "caption_id": ai_caption.sqid,
                    "product_id": product.sqid,
                    "status": ai_caption.status,
                    "generated_text": caption,
                }})
        
        return True
        
    except CaptionBusinessError as e:
        # TODO: Add logging
        ai_caption.status = Status.FAILED
        ai_caption.save(update_fields=["status"])
        
        send_event(channel=channel, event_type="caption.failed", data={
                "type": "caption.failed",
                "timestamp": timezone.now().isoformat(),
                "job_id": job.sqid,
                "data": {
                    "caption_id": ai_caption.sqid,
                    "product_id": product.sqid,
                    "status": "failed",
                }})
        
        return False
    
    except CaptionInfrastructureError as exc:
        try:
            raise self.retry(exc=exc, countdown=5)

        except self.MaxRetriesExceededError:
            ai_caption.status = Status.FAILED
            ai_caption.save(update_fields=["status"])

            send_event(channel=channel, event_type="caption.failed", data={
                "type": "caption.failed",
                "timestamp": timezone.now().isoformat(),
                "job_id": job.sqid,
                "data": {
                    "caption_id": ai_caption.sqid,
                    "product_id": product.sqid,
                    "status": "failed",
                }})

            return False
    
@shared_task()
def generate_ai_captions_completed(results, job_id):
    job = AiCaptionJob.objects.get(id=job_id)
    
    channel = get_job_channel("ai-caption", job.sqid)
    
    if all(results):
        job.status = Status.SUCCESS
    elif any(results):
        job.status = Status.PARTIAL_SUCCESS
    else:
        job.status = Status.FAILED
    
    job.save(update_fields=["status"])
    
    send_event(channel=channel, event_type="caption.job.completed", data={
                "type": "caption.job.completed",
                "timestamp": timezone.now().isoformat(),
                "job_id": job.sqid,
                "data": {}
                })