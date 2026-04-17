from rest_framework import serializers
from .models import Product

from stores.models import Store, TelegramChannelConnection

class ProductCreateSerializer(serializers.ModelSerializer):
    store = serializers.SlugRelatedField(slug_field='sqid', queryset=Store.objects.all())
    
    class Meta:
        model = Product
        fields = ["sqid", "store", "title", "description", "price", "image_url", "stock", "created_at"]
        read_only_fields = ["sqid", "created_at"]
        
class ProductPublishSerializer(serializers.Serializer):
    channel = serializers.SlugRelatedField(slug_field='sqid', queryset=TelegramChannelConnection.objects.all(), required=True)
    product = serializers.SlugRelatedField(slug_field='sqid', queryset=Product.objects.all(), required=True)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        product = validated_data.get("product")
        channel = validated_data.get("channel")
        
        store = channel.store
        
        if store.owner != self.context['request'].user:
            raise serializers.ValidationError({"store": "You do not have permission to publish this product."})
        
        if product.store.owner != self.context['request'].user:
            raise serializers.ValidationError({"product": "You do not have permission to publish this product."})
        
        if channel.store != store:
            raise serializers.ValidationError({"channel": "The selected channel does not belong to this user."})
        
        if not channel.is_active:
            raise serializers.ValidationError({"channel": "The selected channel is not active."})
        
        return validated_data