from rest_framework import viewsets
from rest_framework.response import Response
from .models import Product, Variant
from .serializers import ProductSerializer, STATUS_SUCCESS


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        n_variant = len(serializer.data['variants'])
        message = f"success create 1 product with {n_variant} variants"
        if n_variant <= 1:
            message = f"success create 1 product with {n_variant} variant"

        return Response({"status": STATUS_SUCCESS, "message": message}, status=201)
