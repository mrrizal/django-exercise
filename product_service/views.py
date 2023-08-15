from rest_framework import viewsets
from rest_framework.response import Response
from .models import Product, Variant
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)


# class VariantViewSet(viewsets.ViewSet):
#     def create(self, request, product_pk=None):
#         try:
#             product = Product.objects.get(pk=product_pk)
#         except Product.DoesNotExist:
#             return Response({'error': 'Product not found'}, status=404)

#         serializer = ProductSerializer(data=request.data)
#         if serializer.is_valid():
#             variant_data = serializer.validated_data.pop('variants')[0]
#             Variant.objects.create(product=product, **variant_data)
#             return Response(serializer.data, status=201)
#         return Response(serializer.errors, status=400)

#     def list(self, request, product_pk=None):
#         try:
#             product = Product.objects.get(pk=product_pk)
#         except Product.DoesNotExist:
#             return Response({'error': 'Product not found'}, status=404)

#         variants = product.variants.all()
#         serializer = VariantSerializer(variants, many=True)
#         return Response(serializer.data)
