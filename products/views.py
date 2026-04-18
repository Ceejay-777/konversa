from django.db import transaction

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import extend_schema

from .models import ProductPublishLog
from .serializers import ProductCreateSerializer, ProductPublishSerializer
from integrations.telegram.services import TelegramPublishingService

@extend_schema(tags=["Products"], summary="Create a new product")       
class ProductCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductCreateSerializer
    parser_classes = [MultiPartParser, FormParser]

@extend_schema(tags=["Products"], summary="Publish a product to a Telegram channel")
class ProductPublishView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductPublishSerializer
    
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product = serializer.validated_data['product']
        channel = serializer.validated_data['channel']
        
        service = TelegramPublishingService()
        success, error, message_id = service.publish_product(channel.channel_id, product)
        
        ProductPublishLog.objects.create(
            product=product,
            channel_connection=channel,
            post_id=message_id ,
            status="success" if success else "failed",
            error_message=error
        )
        
        return Response({"status": "success" if success else "error", "error": error, "detail": "Product published successfully"}, status=status.HTTP_200_OK)
        
        
