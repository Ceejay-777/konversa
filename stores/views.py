from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics

from drf_spectacular.utils import extend_schema

from integrations.telegram.services import TelegramConnectionService
from .models import TelegramChannelConnection
from .serializers import StoreSerializer, TelegramConnectSerializer

@extend_schema(tags=["Stores"], summary="Create a new store")
class CreateStoreView(generics.CreateAPIView):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(owner=user)

@extend_schema(tags=["Stores"], summary="Connect a Telegram channel to a store") 
class ConnectTelegramView(generics.CreateAPIView):
    serializer_class = TelegramConnectSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        channel_username = serializer.validated_data['channel_username']
        store = serializer.validated_data['store']
        
        service = TelegramConnectionService()
        success, error, metadata = service.validate_and_get_metadata(channel_username)
        
        if not success:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        connection, created = TelegramChannelConnection.objects.update_or_create(
            store=store,
            defaults={
                'channel_id': metadata['channel_id'],
                'channel_name': metadata['channel_name'],
                'channel_username': metadata['channel_username'],
                'is_active': True
            }
        )

        return Response({
            "status": "connected",
            "channel_name": connection.channel_name,
            "channel_id": connection.channel_id
        }, status=status.HTTP_201_CREATED)

@extend_schema(tags=["Stores"], summary="List all stores for the user")
class ListStoresView(generics.ListAPIView):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.stores.all()