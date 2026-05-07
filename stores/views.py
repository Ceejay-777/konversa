from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics

from drf_spectacular.utils import extend_schema, extend_schema_view

from konversa.mixins import BaseViewSet

from .models import Store, Connection
from .serializers import StoreSerializer, DeactivateConnectionSerializer, ConnectionSerializer
from .schema import StoreViewsetSchema, PlatformParam
from .services import connect_platform, CONNECTION_SERIALIZERS

@extend_schema_view(**StoreViewsetSchema)
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

@extend_schema(tags=["Stores"], summary="Connect a platform to a store", parameters=[PlatformParam]) 
class CreateConnectionView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        platform = self.request.query_params.get("platform")
        
        return CONNECTION_SERIALIZERS.get(platform)
    
    def create(self, request, *args, **kwargs):
        platform = request.query_params.get("platform")
        
        if platform not in dict(Connection.PlatformType.choices):
            return Response({"details": "Invalid platform type"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        success, error, connection = connect_platform(platform, serializer.validated_data)
        
        if not success:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail": "Platform connected successfully", "connection": ConnectionSerializer(connection).data}, status=status.HTTP_201_CREATED)

@extend_schema(tags=["Stores"], summary="Disconnect a connection from a store")
class DeactivateConnectionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeactivateConnectionSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        connection = serializer.validated_data['connection']
        
        connection.is_active = False
        connection.save()

        return Response({"detail": "Platform disconnected successfully"}, status=status.HTTP_200_OK)