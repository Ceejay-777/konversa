from celery import shared_task

from integrations.telegram.services import TelegramPublishingService
from integrations.telegram.exceptions import TelegramAPIError

from integrations.ai.captioning.services import generate_caption

from .models import Publication, Product, AICaption

from stores.models import Connection

PUBLISHING_SERVICE = {
    "telegram": TelegramPublishingService
}

@shared_task(
    autoretry_for=(TelegramAPIError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3}
)
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

            log.save(update_fields=[
                "status",
                "error_message"
            ])

            raise Exception(error)

        log.status = "success"
        log.post_id = post_id
        log.error_message = None

        log.save(update_fields=[
            "status",
            "post_id",
            "error_message"
        ])

    except Exception as e:
        log.status = "failed"
        log.error_message = str(e)

        log.save(update_fields=[
            "status",
            "error_message"
        ])

        raise    

@shared_task()
def generate_ai_caption_task(ai_caption_id):
    ai_caption = AICaption.objects.get(id=ai_caption_id).select_related("product")
    product = ai_caption.product
    
    try:
        success, caption, ai_model = generate_caption(product) # TODO: Add seller profile data
        
        ai_caption.ai_generated_text = caption
        ai_caption.ai_model = ai_model
        ai_caption.status = "success" if success else "failed"
        
        ai_caption.save(update_fields=["ai_generated_text", "ai_model", "status"])
        
    except Exception as e:
        # TODO: Log and error and re-raise
        ai_caption.status = "failed"
        
        ai_caption.save(update_fields=["status"])
        
        raise