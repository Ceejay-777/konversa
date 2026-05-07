from rest_framework import serializers

from stores.models import Store, Connection

class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = ['sqid', 'store', 'account_id', 'created_at']
        read_only_fields = ['sqid', 'created_at', 'account_id']

class CreateTelegramConnectionSerializer(serializers.Serializer):
    store = serializers.SlugRelatedField(slug_field='sqid', queryset=Store.objects.all(), required=True)
    channel_username = serializers.CharField(help_text="The username of the channel", required=True)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        store = validated_data.get("store")
        channel_username = validated_data.get("channel_username")
        
        if store.owner != self.context['request'].user:
            raise serializers.ValidationError({"detail": "You do not have permission to connect this store."})
        
        if not channel_username.startswith("@"):
            channel_username = "@" + channel_username
            validated_data['channel_username'] = channel_username
        
        return validated_data

class StoreSerializer(serializers.ModelSerializer):
    telegram_channels = ConnectionSerializer(many=True, read_only=True, source='telegram_channel_connections')
    
    class Meta:
        model = Store
        fields = ['sqid', 'name', 'created_at', 'telegram_channels']
        read_only_fields = ['sqid', 'created_at', 'telegram_channels']
        
class DeactivateConnectionSerializer(serializers.Serializer):
    store = serializers.SlugRelatedField(slug_field='sqid', queryset=Store.objects.all(), required=True)
    connection = serializers.SlugRelatedField(slug_field='sqid', queryset=Connection.objects.all(), required=True)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        store = validated_data.get("store")
        connection = validated_data.get("connection")
        
        if store.owner != self.context['request'].user:
            raise serializers.ValidationError({"detail": "You do not have permission to disconnect this connection."})
        
        if connection.store != store:
            raise serializers.ValidationError({"detail": "This connection does not belong to this store."})
        
        return validated_data

