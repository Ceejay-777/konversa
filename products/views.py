from django.db import transaction

from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Product, ProductPublishLog
from .filters import ProductFilter
from .serializers import ProductCreateSerializer, ProductPublishSerializer

from konversa.mixins import BaseViewSet

from integrations.telegram.services import TelegramPublishingService

@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Retrieve products for a specific store using the store query parameter",
    ),
    create=extend_schema(
        summary="Create a new product",
        description="Create a new product under the authenticated user's store",
    ),
    destroy=extend_schema(
        summary="Delete a product",
        description="Delete a product by sqid",
    ),
    retrieve=extend_schema(
        summary="Retrieve a product",
        description="Retrieve a product by sqid",
    ),
)
@extend_schema(tags=["Products"])
class ProductViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductCreateSerializer
    queryset = Product.objects.all().select_related("store")
    
    parser_classes = [MultiPartParser, FormParser]
    
    http_method_names = ["post", "get", "delete"]
    lookup_field = "sqid"
    
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    
    def get_base_queryset(self):
        return super().get_base_queryset().filter(store__owner=self.request.user).order_by("-created_at")
    
    def list(self, request, *args, **kwargs):
        if not request.query_params.get("store"):
            raise ValidationError({"store": "This query parameter is required."})
        
        return super().list(request, *args, **kwargs)
    
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
    
        
