import requests
from django.conf import settings

from .exceptions import (
    TelegramRequestError,
    TelegramResponseError,
)


class TelegramClient:
    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self):
        self.base_url = f"{self.BASE_URL}{settings.TELEGRAM_BOT_TOKEN}"

    def _request(self, method: str, http_method="GET", **kwargs):
        url = f"{self.base_url}/{method}"
        
        print("Requesting:", url)

        try:
            if http_method == "GET":
                response = requests.get(url, timeout=10, **kwargs)
            else:
                response = requests.post(url, timeout=10, **kwargs)

        except requests.RequestException as e:
            print(f"Error occurred while making request: {e}")
            raise TelegramRequestError("Failed to connect to Telegram API")

        # HTTP-level failure
        if response.status_code != 200:
            print(response.text)
            raise TelegramRequestError(
                f"Telegram API returned status {response.status_code}", response.status_code
            )

        data = response.json()

        # Telegram-level failure
        if not data.get("ok"):
            raise TelegramResponseError(
                data.get("description", "Telegram API error")
            )

        return data["result"]

    def get_chat(self, chat_id: str):
        return self._request(
            "getChat",
            params={"chat_id": chat_id}
        )

    def get_chat_member(self, chat_id: str, user_id: int):
        return self._request(
            "getChatMember",
            params={
                "chat_id": chat_id,
                "user_id": user_id
            }
        )

    def get_me(self):
        return self._request("getMe")

    def send_photo(self, chat_id: str, photo_url: str, caption: str):
        return self._request(
            "sendPhoto",
            http_method="POST",
            data={
                "chat_id": chat_id,
                "photo": photo_url,
                "caption": caption,
                "parse_mode": None
            }
        )