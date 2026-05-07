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
from .schemas import ProductViewsetSchema
from .services import publish_product

from konversa.mixins import BaseViewSet

from integrations.telegram.services import TelegramPublishingService

@extend_schema_view(**ProductViewsetSchema)
@extend_schema(tags=["Products"])
class ProductViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductCreateSerializer
    queryset = Product.objects.all().select_related("store")
    
    parser_classes = [MultiPartParser, FormParser]
    
    http_method_names = ["post", "get", "delete"]
    lookup_field = "sqid"
    
    filterset_class = ProductFilter
    search_fields = ["title", "description"]
    
    def get_base_queryset(self):
        return super().get_base_queryset().filter(store__owner=self.request.user).order_by("-created_at")
    
    def list(self, request, *args, **kwargs):
        if not request.query_params.get("store"):
            raise ValidationError({"detail": "This query parameter is required."})
        
        return super().list(request, *args, **kwargs)
    
@extend_schema(tags=["Products"], summary="Publish a product to a connection")
class ProductPublishView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductPublishSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        connection = serializer.validated_data['connection']
        product = serializer.validated_data['product']
        
        success, error = publish_product(connection, product)
        
        if not success:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail": "Product published successfully"}, status=status.HTTP_200_OK)
    
        
