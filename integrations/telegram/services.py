import telegram
from django.conf import settings
from typing import Tuple, Optional

from .clients import TelegramClient
from .exceptions import TelegramAPIError

class TelegramConnectionService:
    def __init__(self):
        self.client = TelegramClient()

    def validate_and_get_metadata(self, channel_username: str):
        try:
            chat = self.client.get_chat(channel_username)

            if chat["type"] != "channel":
                return False, "Not a Telegram channel", None

            bot = self.client.get_me()
            member = self.client.get_chat_member(chat["id"], bot["id"])

            if member["status"] != "administrator":
                return False, "Bot must be an admin in the channel", None

            return True, None, {
                "channel_id": chat["id"],
                "channel_name": chat["title"],
                "channel_username": channel_username
            }

        except TelegramAPIError as e:
            return False, str(e), None

class TelegramPublishingService:
    def __init__(self):
        self.client = TelegramClient()
        
    def format_product_message(self, product):
        return (
            f"🛍 {product.title}\n\n"
            f"{product.description}\n\n"
            f"💰 Price: ₦{product.price}\n"
            f"📦 *Stock:* {'In Stock' if product.stock > 0 else 'Out of Stock'}\n\n"
            f"Send a DM to order!"
        )
        
    def publish_product(self, channel_id: str, product) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Sends the product image + caption to the specific channel.
        Returns: (success_bool, error_message, telegram_message_id)
        """
        caption = self.format_product_message(product)
        
        try:
            message = self.client.send_photo(
                chat_id=channel_id,
                photo=product.image_url,
                caption=caption,
                parse_mode="Markdown"
            )
            
            return True, None, message.message_id
        
        except TelegramAPIError as e:
            return False, str(e), None