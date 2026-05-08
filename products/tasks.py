from celery import shared_task

from integrations.telegram.services import TelegramPublishingService
from integrations.telegram.exceptions import TelegramAPIError
from .models import ProductPublishLog, Product

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
    log = ProductPublishLog.objects.get(id=log_id)

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