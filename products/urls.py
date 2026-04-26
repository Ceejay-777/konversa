from django.urls import path
from .views import ProductPublishView, ProductViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register(r"products", ProductViewSet, basename="products")

urlpatterns = [
    path("products/publish", ProductPublishView.as_view(), name="publish-product"),
] + router.urls