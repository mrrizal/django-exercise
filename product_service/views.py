from rest_framework import viewsets
from rest_framework.response import Response
from django.db.models import Prefetch
from .models import Product, Variant
from .serializers import ProductSerializer, STATUS_SUCCESS, ProductLimitVariantsSerializer
from .paginations import CustomPagination


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('variants').all()
    serializer_class = ProductSerializer
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        n_variant = len(serializer.data['variants'])
        message = f"success create 1 product with {n_variant} variants"
        if n_variant <= 1:
            message = f"success create 1 product with {n_variant} variant"

        return Response({"status": STATUS_SUCCESS, "message": message}, status=201)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        self.serializer_class = ProductLimitVariantsSerializer

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
