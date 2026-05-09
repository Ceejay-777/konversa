from django.utils import timezone

from celery import shared_task
from django_eventstream import send_event

from integrations.telegram.services import TelegramPublishingService
from integrations.telegram.exceptions import TelegramAPIError
from integrations.ai.captioning.services import generate_caption
from integrations.ai.captioning.exceptions import CaptionBusinessError, CaptionInfrastructureError, CaptionRateLimitError

from .models import Publication, Product, AiCaption, AiCaptionJob

from stores.models import Connection
from konversa.utils import get_job_channel
from konversa.models import JobStatus, Status

PUBLISHING_SERVICE = {
    "telegram": TelegramPublishingService
}

@shared_task(autoretry_for=(TelegramAPIError,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def publish_product_task(connection_id, product_id, log_id):
    connection = Connection.objects.get(id=connection_id)
    product = Product.objects.get(id=product_id)
    log = Publication.objects.get(id=log_id)

    log.status = "processing"
    log.save(update_fields=["status"])

    platform = connection.platform
    service_class = PUBLISHING_SERVICE.get(platform)

    if not service_class:
        raise Exception(f"Platform {platform} is not supported")

    service = service_class()

    try:
        success, error, post_id = service.publish(connection.account_id, product)

        if not success:
            log.status = "failed"
            log.error_message = error

            log.save(update_fields=["status", "error_message"])

            raise Exception(error)

        log.status = "success"
        log.post_id = post_id
        log.error_message = None

        log.save(update_fields=["status", "post_id", "error_message"])

    except Exception as e:
        log.status = "failed"
        log.error_message = str(e)

        log.save(update_fields=["status", "error_message"])

        raise    

@shared_task(bind=True, max_retries=3)
def generate_ai_caption_task(self, ai_caption_id):
    ai_caption = AiCaption.objects.select_related("product", "job").get(id=ai_caption_id)
    product = ai_caption.product
    job = ai_caption.job
    channel = get_job_channel("ai_caption", job.sqid)
    
    try:
        success, caption, ai_model = generate_caption(product) # TODO: Add seller profile data
        
        ai_caption.ai_generated_text = caption
        ai_caption.ai_model = ai_model
        ai_caption.status = Status.SUCCESS if success else Status.FAILED
        ai_caption.save(update_fields=["ai_generated_text", "ai_model", "status"])
        
        if success:
            send_event(channel=channel, event="caption.generated", data={
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
        
        else:
            send_event(channel=channel, event="caption.failed", data={
                "type": "caption.failed",
                "timestamp": timezone.now().isoformat(),
                "job_id": job.sqid,
                "data": {
                    "caption_id": ai_caption.sqid,
                    "product_id": product.sqid,
                    "status": "failed",
                }})
        
            return False
        
    except CaptionBusinessError as e:
        ai_caption.status = Status.FAILED
        ai_caption.save(update_fields=["status"])
        
        send_event(channel=channel, event="caption.failed", data={
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

            send_event(channel=channel, event="caption.failed", data={
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
    
    channel = get_job_channel("ai_caption", job.sqid)
    
    if all(results):
        job.status = JobStatus.SUCCESS
    elif any(results):
        job.status = JobStatus.PARTIAL_SUCCESS
    else:
        job.status = JobStatus.FAILED
    
    job.save(update_fields=["status"])
    
    send_event(channel=channel, event="caption.job.completed", data={
                "type": "caption.job.completed",
                "timestamp": timezone.now().isoformat(),
                "job_id": job.sqid,
                "data": {}
                })