import pytz
from datetime import datetime
from rest_framework import serializers
from .utils import to_indonesia_timezone
from .models import Product, Variant
from django.conf import settings


STATUS_FAILED = "failed"
STATUS_SUCCESS = "success"
INDONESIA_TIMEZONE = pytz.timezone('Asia/Jakarta')


class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = ('name', 'height', 'stock', 'price',
                  'weight', 'created_at', 'is_active', 'active_time')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('active_time')
        representation['created_at'] = to_indonesia_timezone(
            representation['created_at'])

        for field in ['height', 'price', 'weight']:
            representation[field] = float(representation[field])
        return representation


class CustromErrorSerializer(serializers.BaseSerializer):
    def is_valid(self, raise_exception=False):
        assert not hasattr(self, 'restore_object'), (
            'Serializer `%s.%s` has old-style version 2 `.restore_object()` '
            'that is no longer compatible with REST framework 3. '
            'Use the new-style `.create()` and `.update()` methods instead.' %
            (self.__class__.__module__, self.__class__.__name__)
        )

        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )

        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except serializers.ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.detail
            else:
                self._errors = {}

        if self._errors and raise_exception:
            raise serializers.ValidationError(
                {"status": STATUS_FAILED, "message": self.errors})

        return not bool(self._errors)

    def fail(self, key, **kwargs):
        try:
            msg = self.error_messages[key]
        except KeyError:
            class_name = self.__class__.__name__
            msg = serializers.MISSING_ERROR_MESSAGE.format(
                class_name=class_name, key=key)
            raise AssertionError(msg)
        message_string = msg.format(**kwargs)
        raise serializers.ValidationError(
            {"status": STATUS_FAILED, "message": message_string}, code=key)


class ProductSerializer(serializers.ModelSerializer, CustromErrorSerializer):
    variants = VariantSerializer(many=True)

    class Meta:
        model = Product
        fields = ('name', 'description', 'variants', 'is_active', 'created_at')

    def validate_variants_name(self, variants_data):
        names = {}
        for data in variants_data:
            if data['name'] in names:
                err_message = {
                    "status": STATUS_FAILED,
                    "message": f"A variant with '{data['name']}' name already exists for the product."
                }
                raise serializers.ValidationError(err_message)
            names[data['name']] = True

    def create(self, validated_data):
        variants_data = validated_data.pop('variants')
        self.validate_variants_name(variants_data)

        product = Product.objects.create(**validated_data)
        variants = []
        for variant_data in variants_data:
            variant_data['active_time'] = variant_data['active_time'].replace(
                tzinfo=INDONESIA_TIMEZONE)
            if variant_data['active_time'].strftime('%s') <= datetime.now(INDONESIA_TIMEZONE).strftime('%s'):
                variant_data['is_active'] = True
            variants.append(Variant(product=product, **variant_data))

        if len(variants) > 0:
            Variant.objects.bulk_create(variants)

        return product

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('created_at')
        return representation


class ProductLimitVariantsSerializer(ProductSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['variants'] = representation['variants'][:
                                                                settings.VARIANT_LIMIT_PER_PRODUCT]
        return representation
