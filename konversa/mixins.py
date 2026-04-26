from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny

class PublicGenericAPIView(generics.GenericAPIView):
    authentication_classes = []  
    permission_classes = [AllowAny]
class BaseViewSet(viewsets.ModelViewSet):
    def get_base_queryset(self):
        return self.queryset

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        qs = self.get_base_queryset()
        return self.filter_queryset(qs)
    
    def perform_destroy(self, instance):
        instance.soft_delete()