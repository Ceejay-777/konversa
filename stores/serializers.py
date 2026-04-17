from rest_framework import serializers

from stores.models import Store, TelegramChannelConnection

class StoreSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Store
        fields = ['sqid', 'name', 'created_at']
        read_only_fields = ['sqid', 'created_at']
        
class TelegramConnectSerializer(serializers.ModelSerializer):
    store = serializers.SlugRelatedField(slug_field='sqid', queryset=Store.objects.all())
    channel_username = serializers.CharField(help_text="The username of the channel")
    
    class Meta: 
        model = TelegramChannelConnection
        fields = ['sqid', 'store', 'channel_id', "channel_username", "channel_name", 'created_at']
        read_only_fields = ['sqid', 'created_at', 'channel_id', 'channel_name']
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        store = validated_data.get("store")
        
        if store.owner != self.context['request'].user:
            raise serializers.ValidationError({"store": "You do not have permission to connect this store."})
        
        return validated_data
