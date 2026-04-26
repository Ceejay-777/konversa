from django.urls import path
from .views import ConnectTelegramView, StoreViewset, DisconnectTelegramView
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register(r"stores", StoreViewset, basename="stores")

urlpatterns = [
    path("stores/connect-telegram", ConnectTelegramView.as_view(), name="connect-telegram"),
    path("stores/disconnect-telegram", DisconnectTelegramView.as_view(), name="disconnect-telegram"),
] + router.urls