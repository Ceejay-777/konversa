from django.db import transaction

from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema, extend_schema_view
from celery import chord

from .models import Product, AiCaption, AiCaptionJob, PublicationJob, Publication
from .filters import ProductFilter
from .serializers import ProductCreateSerializer, PublishProductsSerializer, GenerateAiCaptionSerializer, AiCaptionJobSerializer
from .schemas import ProductViewsetSchema
from .tasks import publish_product_task, generate_ai_caption_task, generate_ai_captions_completed

from konversa.mixins import BaseViewSet
from konversa.models import Status
from konversa.utils import get_job_channel


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
    serializer_class = PublishProductsSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        connection = serializer.validated_data['connection']
        publication_items = serializer.validated_data['publication_items']
        
        publictions = []
        tasks = []
        
        with transaction.atomic():
            job = PublicationJob.objects.create(store=products[0].store, status=Status.PENDING)
            
            for publication_item in publication_items:
                product = publication_item.product
                
                publication = Publication.objects.create(job=job, product=product, connection=publication_item.connection, ai_caption=publication_item.ai_caption, caption=publication_item.caption, status=Status.PENDING)
                
                tasks.append(publish_product_task.s(connection.id, publication.id, job.id))
                publictions.append({"product_id": product.sqid, "publication_id": publication.sqid})
            
        callback = publish_products_completed.s(job.id)
        transaction.on_commit(lambda: chord(tasks)(callback))
        
        return Response({"detail": "Publishing products", "publications": publications, "job_id": job.sqid, "channel": get_job_channel("publication", job.sqid)}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Products"], summary="Generate AI captions for a list of products")    
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
        
        return Response({ "detail": "Generating AI captions", "ai_captions": ai_captions, "job_id": job.sqid, "channel": get_job_channel("ai-caption", job.sqid)}, status=status.HTTP_200_OK)
  
class RetrieveAiCaptionJob(generics.RetrieveAPIView):
    serializer_class = AiCaptionJobSerializer
    queryset = AiCaptionJob.objects.all()
    lookup_field = "sqid"