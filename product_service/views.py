import re

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        n_variant = len(serializer.data['variants'])
        message = f"success create 1 product with {n_variant} variants"
        if n_variant <= 1:
            message = f"success create 1 product with {n_variant} variant"

        return Response({"status": STATUS_SUCCESS, "message": message}, status=201)

    def is_valid_date(self, date: str) -> str:
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date))

    def filter_queryset_by_date_range(self, queryset, start_date, end_date):
        datetime_format = "%d-%m-%YT%H:%M:%S"

        if start_date and self.is_valid_date(start_date):
            start_date = to_indonesia_timezone(
                f'{start_date}T00:00:00', datetime_format)
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date and self.is_valid_date(end_date):
            end_date = to_indonesia_timezone(
                f'{end_date}T23:59:59', datetime_format)
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset

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

        if created_at_gte and self.is_valid_date(created_at_gte):
            try:
                created_at_gte = to_indonesia_timezone(
                    f'{created_at_gte}T00:00:00', datetime_format)
                queryset = queryset.filter(created_at__gte=created_at_gte)
            except ValueError:
                return Response(empty_result)

        if created_at_lte and self.is_valid_date(created_at_lte):
            try:
                created_at_lte = to_indonesia_timezone(
                    f'{created_at_lte}T23:59:59', datetime_format)
                queryset = queryset.filter(created_at__lte=created_at_lte)
            except ValueError:
                return Response(empty_result)

        queryset = self.filter_queryset_by_date_range(
            queryset,
            created_at_gte,
            created_at_lte
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
