from django_filters import rest_framework as filters
from .models import Store

class StoreFilter(filters.FilterSet):
    store = filters.CharFilter(field_name="sqid")

    class Meta:
        model = Store
        fields = ["store"]