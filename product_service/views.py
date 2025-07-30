from rest_framework import viewsets
from rest_framework.response import Response

from .utils import to_indonesia_timezone
from .models import Product
from .serializers import (
    ProductSerializer,
    STATUS_SUCCESS,
    ProductLimitVariantsSerializer)
from .paginations import CustomPagination


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('variants').all()
    serializer_class = ProductSerializer
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        self.serializer_class = ProductLimitVariantsSerializer

        datetime_format = "%d-%m-%YT%H:%M:%S"
        created_at_gte = request.GET.get('created_at_gte', None)
        created_at_lte = request.GET.get('created_at_lte', None)

        empty_result = {
            "next": None,
            "previous": None,
            "results": []
        }
        if created_at_gte:
            try:
                created_at_gte = to_indonesia_timezone(
                    f'{created_at_gte}T00:00:00', datetime_format)
                queryset = queryset.filter(created_at__gte=created_at_gte)
            except ValueError:
                return Response(empty_result)

        if created_at_lte:
            try:
                created_at_lte = to_indonesia_timezone(
                    f'{created_at_lte}T23:59:59', datetime_format)
                queryset = queryset.filter(created_at__lte=created_at_lte)
            except ValueError:
                return Response(empty_result)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
