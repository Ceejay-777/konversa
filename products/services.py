from integrations.telegram.services import TelegramPublishingService
from .models import ProductPublishLog

PUBLISHING_SERVICE = {
    "telegram": TelegramPublishingService
}

def publish_product(connection, product) -> bool:
    platform = connection.platform
    service = PUBLISHING_SERVICE.get(platform)
    success, error, post_id = service.publish(connection, product)
    
    ProductPublishLog.objects.create(
        product=product,
        connection=connection,
        post_id=post_id ,
        status="success" if success else "failed",
        error_message=error
    )
    
    return success, error