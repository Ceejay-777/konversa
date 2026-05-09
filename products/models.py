from django.db import models

from stores.models import Store, Connection
from konversa.models import BaseModel, Status
from konversa.utils import upload_product_image_to

class Product(BaseModel):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="products"
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    image = models.ImageField(upload_to=upload_product_image_to, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class AiCaption(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name="ai_captions")
    
    ai_generated_text = models.TextField(blank=True, null=True)
    final_text = models.TextField(blank=True, null=True)
    
    was_edited = models.BooleanField(default=False)
    status = models.CharField(max_length=50, default=Status.PENDING, choices=Status.choices)
    ai_model = models.CharField(max_length=255, blank=True, null=True)
    
class Publication(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="publications")
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE, related_name="publications")
    
    ai_caption = models.ForeignKey(AiCaption, on_delete=models.DO_NOTHING, related_name="publications", null=True, default=None)
    caption = models.TextField(blank=True, null=True)
    
    post_id = models.CharField(max_length=255, null=True, default=None)
    status = models.CharField(max_length=50, default=Status.PENDING, choices=Status.choices) 
    error_message = models.TextField(blank=True, null=True, default=None)
    
