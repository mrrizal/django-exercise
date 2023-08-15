from rest_framework import serializers
from .models import Product, Variant
from pprint import pprint


class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = ('name', 'height', 'stock', 'price',
                  'weight', 'created_at', 'is_active', 'active_time')


class ProductSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True)

    class Meta:
        model = Product
        fields = ('name', 'description', 'variants', 'is_active', 'created_at')

    def validate_variants_name(self, variants_data):
        names = {}
        for data in variants_data:
            if data['name'] in names:
                raise serializers.ValidationError(
                    f"A variant with '{data['name']}' name already exists for the product.")
            names[data['name']] = True
        return variants_data

    def create(self, validated_data):
        variants_data = validated_data.pop('variants')
        variants_data = self.validate_variants_name(variants_data)

        product = Product.objects.create(**validated_data)
        variants = []
        for variant_data in variants_data:
            variants.append(Variant(product=product, **variant_data))

        if len(variants) > 0:
            Variant.objects.bulk_create(variants)

        return product
