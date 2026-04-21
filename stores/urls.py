from django.urls import path
from .views import CreateStoreView, ConnectTelegramView, ListStoresView

urlpatterns = [
    path("/", CreateStoreView.as_view()),
    path("/connect-telegram", ConnectTelegramView.as_view(), name="connect-telegram"),
    path("/list", ListStoresView.as_view(), name="list-stores"),
]