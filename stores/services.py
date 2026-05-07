from integrations.telegram.services import TelegramConnectionService

from .serializers import CreateTelegramConnectionSerializer

PLATFORM_SERVICES = {
    "telegram": TelegramConnectionService(),
    # "whatsapp": WhatsAppConnectionService(),
}

CONNECTION_SERIALIZERS = {
    "telegram": CreateTelegramConnectionSerializer
}

def connect_platform(platform, validated_data):
    service = PLATFORM_SERVICES.get(platform)
    return service.connect(validated_data)