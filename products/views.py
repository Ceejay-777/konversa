from django.db import transaction

from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Product, Publication, AICaption
from .filters import ProductFilter
from .serializers import ProductCreateSerializer, ProductPublishSerializer, PublicationSerializer, GenerateAiCaptionSerializer
from .schemas import ProductViewsetSchema
from .tasks import publish_product_task

from konversa.mixins import BaseViewSet

from integrations.ai.captioning.services import generate_caption

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
    
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        connection = serializer.validated_data['connection']
        product = serializer.validated_data['product']
        
        log = Publication.objects.create(
            product=product,
            connection=connection,
            status="pending",
        )
        
        publish_product_task.delay_on_commit(connection.id, product.id, log.id)
        
        return Response({"detail": "Publishing product...", "log_id": log.sqid}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Products"], summary="Get product publish log. Use for polling")
class RetrieveProductPublishLogView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicationSerializer
    queryset = Publication.objects.all()
    lookup_field = "sqid"
    
        
class GenerateAiCaptionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GenerateAiCaptionSerializer
    
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        products = serializer.validated_data['products']
        ai_captions = []
        
        for product in products:
            ai_caption = AICaption.objects.create(
                product=product,
                status="processing"
            )
            
            generate_ai_caption_task.delay_on_commit(product.id, ai_caption.id)
            
            ai_captions.append(ai_caption.sqid)
        
        return Response({ "detail": "Generating AI captions...", "captions": captions}, status=status.HTTP_200_OK)