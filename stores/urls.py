from django.urls import path
from .views import CreateStoreView, ConnectTelegramView

urlpatterns = [
    path("", CreateStoreView.as_view()),
    path("connect-telegram/", ConnectTelegramView.as_view(), name="connect-telegram"),
]