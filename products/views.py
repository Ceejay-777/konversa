from django.db import transaction

from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema, extend_schema_view
from celery import chord

from .models import Product, Publication, AiCaption, AiCaptionJob
from .filters import ProductFilter
from .serializers import ProductCreateSerializer, ProductPublishSerializer, PublicationSerializer, GenerateAiCaptionSerializer
from .schemas import ProductViewsetSchema
from .tasks import publish_product_task, generate_ai_caption_task, generate_ai_captions_completed

from konversa.mixins import BaseViewSet
from konversa.models import Status
from konversa.utils import get_job_channel

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
        
        publication = serializer.save(status="pending")
        
        publish_product_task.delay_on_commit(connection.id, product.id, publication.id)
        
        return Response({"detail": "Publishing product...", "publication_id": publication.sqid}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Products"], summary="Get product publish log. Use for polling")
class RetrieveProductPublishLogView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicationSerializer
    queryset = Publication.objects.all()
    lookup_field = "sqid"
        
class GenerateAiCaptionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GenerateAiCaptionSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        products = serializer.validated_data['products']
        ai_captions = []
        tasks = []
        
        with transaction.atomic():
            job = AiCaptionJob.objects.create(store=products[0].store, status=Status.PENDING)
            
            for product in products:
                ai_caption = AiCaption.objects.create(job=job, product=product, status=Status.PENDING)
                
                tasks.append(generate_ai_caption_task.s(ai_caption.id))
                ai_captions.append({"product_id": product.sqid, "ai_caption_id": ai_caption.sqid})
            
        callback = generate_ai_captions_completed.s(job.id)
        transaction.on_commit(lambda: chord(tasks)(callback))
        
        return Response({ "detail": "Generating AI captions", "ai_captions": ai_captions, "job_id": job.sqid, "channel": get_job_channel("ai_caption", job.sqid)}, status=status.HTTP_200_OK)