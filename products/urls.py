from django.urls import path
from .views import ProductCreateView, ProductPublishView

urlpatterns = [
    path("/", ProductCreateView.as_view(), name="create-product"),
    path("/publish", ProductPublishView.as_view(), name="publish-product"),
]