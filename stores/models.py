from django.db import models

from konversa.models import BaseModel

class Store(BaseModel):
    owner = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="stores")
    
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class Connection(BaseModel):
    class PlatformType(models.TextChoices):
        TELEGRAM = "telegram"
        WHATSAPP = "whatsapp"
        INSTAGRAM = "instagram"
        TIKTOK = "tiktok"

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="connections")
    platform = models.CharField(max_length=20, choices=PlatformType.choices)

    account_id = models.CharField(max_length=255)  

    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.platform} Connection for Store {self.store.name}"
    
class TelegramConnectionDetails(models.Model):
    connection = models.OneToOneField(Connection, on_delete=models.CASCADE, related_name="telegram")

    channel_id = models.BigIntegerField()
    channel_name = models.CharField(max_length=255, blank=True, null=True)
    channel_username = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"Telegram Connection for Channel {self.channel_id} (Store: {self.connection.store.name})"
    
    

# class TelegramChannelConnection(BaseModel):
#     store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="telegram_channel_connections")
    
#     channel_id = models.BigIntegerField()
#     channel_name = models.CharField(max_length=255, blank=True, null=True)
#     channel_username = models.CharField(max_length=255, blank=True, null=True)
    
#     is_active = models.BooleanField(default=True)
    
#     def __str__(self):
#         return f"Telegram Connection for Channel {self.channel_id} (Store: {self.store.name})"