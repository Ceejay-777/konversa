from django.db import models
from stores.models import Store
from konversa.models import BaseModel


class Product(BaseModel):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="products"
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    image_url = models.URLField(blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class ProductPublishLog(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="publish_logs")
    channel_connection = models.ForeignKey("integrations.telegram.models.TelegramChannelConnection", on_delete=models.CASCADE, related_name="product_publish_logs"),
    post_id = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default="success")  # success, failed
    error_message = models.TextField(blank=True, null=True)