from drf_spectacular.utils import extend_schema

ProductViewsetSchema = {
    "list":extend_schema(
        summary="List products",
        description="Retrieve products for a specific store using the store query parameter",
    ),
    "create":extend_schema(
        summary="Create a new product",
        description="Create a new product under the authenticated user's store",
    ),
    "destroy":extend_schema(
        summary="Delete a product",
        description="Delete a product by sqid",
    ),
    "retrieve":extend_schema(
        summary="Retrieve a product",
        description="Retrieve a product by sqid",
    ),
}