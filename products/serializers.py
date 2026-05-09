from rest_framework import serializers
from .models import Product, Publication, AiCaption, AiCaptionJob, PublicationJob

from stores.models import Store, Connection

class ProductCreateSerializer(serializers.ModelSerializer):
    store = serializers.SlugRelatedField(slug_field='sqid', queryset=Store.objects.all())
    image = serializers.ImageField(required=False, allow_null=True, write_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Product
        fields = ["sqid", "store", "title", "description", "price", "image_url", "image", "stock", "created_at"]
        read_only_fields = ["sqid", "created_at", "image_url"]
        
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
    
class AiCaptionInJobSerializer(serializers.ModelSerializer):
    product = serializers.CharField(read_only=True, source='product.sqid')
    class Meta:
        model = AiCaption
        fields = ["sqid", "product", "status"]
    
class AiCaptionJobSerializer(serializers.ModelSerializer):
    ai_captions = AiCaptionInJobSerializer(many=True, read_only=True)
    class Meta:
        model = AiCaptionJob
        fields = ["sqid", "status", "ai_captions"]
    
class PublishAiCaptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiCaption
        fields = ["was_edited", "final_text"]
        
class GenerateAiCaptionSerializer(serializers.Serializer):
    products = serializers.SlugRelatedField(slug_field='sqid', queryset=Product.objects.all(), required=True, many=True)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        products = validated_data.get("products")
        
        for product in products:
            if product.store.owner != self.context['request'].user:
                raise serializers.ValidationError({"detail": f"You do not have permission to publish this product: {product.title}"})
        
        return validated_data
        
class PublicationInJobSerializer(serializers.ModelSerializer):
    product = serializers.CharField(read_only=True, source='product.sqid')

    class Meta:
        model = Publication
        fields = ["sqid", "status", "product"]
        
class PublicationJobSerializer(serializers.ModelSerializer):
    publications = PublicationInJobSerializer(many=True, read_only=True)
    class Meta:
        model = PublicationJob
        fields = ["sqid", "status", "publications"]
        
class PublicationItemSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(slug_field='sqid', queryset=Product.objects.all(), required=True)
    ai_caption = PublishAiCaptionSerializer(required=False)
    caption = serializers.CharField(required=False)
    
    class Meta:
        model = Publication
        fields = ["product", "caption", "ai_caption"]
        read_only_fields = ["created_at"]
    
class PublishProductsSerializer(serializers.Serializer):
    connection = serializers.SlugRelatedField(slug_field='sqid', queryset=Connection.objects.all(), required=True)
    publication_items = PublicationItemSerializer(many=True, required=True)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        publication_items = validated_data.get("publication_items")
        connection = validated_data.get("connection")
        
        store = connection.store
        user = self.context['request'].user
        
        if store.owner != user:
            raise serializers.ValidationError({"detail": "You do not have permission to publish this product."})
        
        if connection.store != store:
            raise serializers.ValidationError({"detail": "The selected channel does not belong to this store."})
        
        if not connection.is_active:
            raise serializers.ValidationError({"detail": "The selected channel has been disconnected."})
        
        for publication_item in publication_items:
            product = publication_item.product
            
            if product.store != store:
                raise serializers.ValidationError({"detail": f"This product does not belong to this store: {product.title}"})
        
        return validated_data