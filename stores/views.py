from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics, viewsets
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes

from integrations.telegram.services import TelegramConnectionService
from konversa.mixins import BaseViewSet

from .filters import StoreFilter
from .models import TelegramChannelConnection, Store
from .serializers import StoreSerializer, TelegramConnectSerializer

@extend_schema_view(
    list=extend_schema(
        summary="List stores",
        description="Retrieve stores for a specific store using the store query parameter",
    ),
    create=extend_schema(
        summary="Create a new store",
        description="Create a new store for the authenticated user",
    ),
    destroy=extend_schema(
        summary="Delete a store",
        description="Delete a store by sqid",
    ),
    retrieve=extend_schema(
        summary="Retrieve a store",
        description="Retrieve a store by sqid",
    ),
)
@extend_schema(tags=["Stores"])
class StoreViewset(BaseViewSet):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]
    queryset = Store.objects.all().select_related("owner", "telegram_channel_connections")
    
    http_method_names = ["post", "get", "delete"]
    lookup_field = "sqid"

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(owner=user)
        
    def get_base_queryset(self):
        return self.request.user.stores.all()

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

@extend_schema(tags=["Stores"], summary="Disconnect a Telegram channel from a store", parameters=[
        OpenApiParameter(
            name="store",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Store sqid to disconnect the Telegram channel from"
        )
    ])
class DisconnectTelegramView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        store = request.query_params.get("store")
        if not store:
            raise ValidationError({"store": "This query parameter is required."})

        connection = TelegramChannelConnection.objects.filter(
            store__sqid=store,
            is_active=True
        ).select_related("store").first()

        if not connection:
            return Response({"telegram": "No active telegram connection found"}, status=404)

        connection.is_active = False
        connection.save()

        return Response({"status": "disconnected"}, status=status.HTTP_200_OK)