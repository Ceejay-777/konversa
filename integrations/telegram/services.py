from django.conf import settings
from django.db import transaction

from typing import Tuple, Optional

from .clients import TelegramClient
from .exceptions import TelegramAPIError

from stores.models import Connection, TelegramConnectionDetails

class TelegramConnectionService:
    def __init__(self):
        self.client = TelegramClient()
        self.bot_id = settings.TELEGRAM_BOT_TOKEN

    def validate_and_get_metadata(self, channel_username: str):
        try:
            chat = self.client.get_chat(channel_username)

            if chat["type"] != "channel":
                return False, "Not a Telegram channel", None

            member = self.client.get_chat_member(chat["id"], self.bot_id)

            if member["status"] != "administrator":
                return False, "Bot must be an admin in the channel", None

            return True, None, {
                "channel_id": chat["id"],
                "channel_name": chat["title"],
                "channel_username": channel_username
            }

        except TelegramAPIError as e:
            return False, str(e), None
    
    def connect(self, validated_data):
        channel_username = validated_data['channel_username']
        store = validated_data['store']
        
        success, error, metadata = self.validate_and_get_metadata(channel_username)
        
        if not success:
            return False, error, None
        
        active_exists = Connection.objects.filter(store=store, account_id=metadata['channel_id'], platform=Connection.PlatformType.TELEGRAM).exists()
        if active_exists:
            return False, "This channel is already connected to this store. If it is not active, please reconnect it.", None
        
        with transaction.atomic():
            connection = Connection.objects.create(
                store=store,
                account_id=metadata['channel_id'],
                platform=Connection.PlatformType.TELEGRAM,
                is_active=True
            )
            
            TelegramConnectionDetails.objects.create(
                connection=connection,
                channel_id=metadata['channel_id'],
                channel_name=metadata['channel_name'],
                channel_username=channel_username
            )
        
            return True, None, connection

class TelegramPublishingService:
    def __init__(self):
        self.client = TelegramClient()
        
    def format_product_message(self, product):
        return (
            f"🛍 {product.title}\n\n"
            f"{product.description}\n\n"
            f"💰 Price: ₦{product.price}\n"
            f"📦 Stock: {'In Stock' if product.stock > 0 else 'Out of Stock'}\n\n"
            f"Send a DM to order!"
        )
        
    def publish(self, channel_id: str, product) -> Tuple[bool, Optional[str], Optional[int]]: # TODO: If image is optional, we should allow publishing without image (send message)
        """
        Sends the product image + caption to the specific channel.
        Returns: (success_bool, error_message, telegram_message_id)
        """
        caption = self.format_product_message(product)
        
        try:
            print("Image url: ", product.image.url if product.image else None)
            message = self.client.send_photo(
                chat_id=channel_id,
                photo_url=product.image.url if product.image else None,
                caption=caption
            )
            
            print("Telegram API response for send_photo:", message)
            
            return message.get("message_id")
        
        except TelegramAPIError as e:
            raise
        
    