from django.urls import path
from .views import ProductPublishView, ProductViewSet, RetrieveProductPublishLogView, GenerateAiCaptionView
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register(r"products", ProductViewSet, basename="products")

urlpatterns = [
    path("products/publish", ProductPublishView.as_view(), name="publish-product"),
    path("products/logs/<slug:sqid>", RetrieveProductPublishLogView.as_view(), name="retrieve-product-publish-log"),
    path("products/auto-caption", GenerateAiCaptionView.as_view(), name="generate-ai-caption"),
] + router.urls