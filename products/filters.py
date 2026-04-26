from django_filters import rest_framework as filters
from .models import Product

class ProductFilter(filters.FilterSet):
    store = filters.CharFilter(field_name="store__sqid")

    class Meta:
        model = Product
        fields = ["store"]