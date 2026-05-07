from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes


StoreViewsetSchema = {
    "list":extend_schema(
        summary="List stores",
        description="Retrieve stores for a specific store using the store query parameter",
    ),
    "create":extend_schema(
        summary="Create a new store",
        description="Create a new store for the authenticated user",
    ),
    "destroy":extend_schema(
        summary="Delete a store",
        description="Delete a store by sqid",
    ),
    "retrieve":extend_schema(
        summary="Retrieve a store",
        description="Retrieve a store by sqid",
    ),
}
    
StoreParam = OpenApiParameter(
        name="store",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=True,
        description="Store sqid"
    )

PlatformParam = OpenApiParameter(
        name="platform",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=True,
        description="Platform type"
    )
