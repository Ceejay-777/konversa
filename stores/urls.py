from django.urls import path
from .views import CreateConnectionView, StoreViewset, DeactivateConnectionView
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register(r"stores", StoreViewset, basename="stores")

urlpatterns = [
    path("stores/connect", CreateConnectionView.as_view(), name="create-connection"),
    path("stores/disconnect", DeactivateConnectionView.as_view(), name="deactivate-connection"),
] + router.urls