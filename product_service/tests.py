import json
from datetime import datetime, timedelta
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from unittest.mock import patch, MagicMock

from .models import Product, Variant
from .serializers import ProductSerializer, INDONESIA_TIMEZONE
from .views import ProductViewSet
from julo.celery import app as celery_app


class ProductViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ProductViewSet.as_view({'post': 'create', 'get': 'list'})

    def test_create_product_with_variants(self):
        with patch("product_service.serializers.activate_variant.apply_async") as mock_activate_variant:
            mock_activate_variant.return_value = True

            data = {
                "name": "Sample Product",
                "description": "This is a sample product.",
                "variants": [
                    {
                        "name": "Variant 1",
                        "height": 10.0,
                        "stock": 100,
                        "price": 10.0,
                        "weight": 0.5,
                        "active_time": "2023-08-16T12:00:00Z"
                    },
                    {
                        "name": "Variant 2",
                        "height": 12.0,
                        "stock": 50,
                        "price": 15.0,
                        "weight": 0.7,
                        "active_time": "2023-08-16T14:00:00Z"
                    }
                ]
            }
            request = self.factory.post(
                '/api/products/', json.dumps(data), content_type='application/json')
            response = self.view(request)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['status'], 'success')
            self.assertEqual(response.data['message'],
                             'success create 1 product with 2 variants')
            mock_activate_variant.assert_not_called()

    def test_create_product_with_single_variant(self):
        with patch("product_service.serializers.activate_variant.apply_async") as mock_activate_variant:
            mock_activate_variant.return_value = True
            data = {
                "name": "Single Variant Product",
                "description": "This product has only one variant.",
                "variants": [
                    {
                        "name": "Single Variant",
                        "height": 8.0,
                        "stock": 75,
                        "price": 20.0,
                        "weight": 0.4,
                        "active_time": "2023-08-16T10:00:00Z"
                    }
                ]
            }
            request = self.factory.post(
                '/api/products/', json.dumps(data), content_type='application/json')
            response = self.view(request)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['status'], 'success')
            self.assertEqual(response.data['message'],
                             'success create 1 product with 1 variant')
            mock_activate_variant.assert_not_called()

    def test_create_product_with_duplicate_name(self):
        # Create a product with a variant using your actual model and serializer
        product_data = {
            "name": "Duplicate Product",
            "description": "This is a duplicate product.",
            "variants": [
                {
                    "name": "Variant 1",
                    "height": 10.0,
                    "stock": 100,
                    "price": 10.0,
                    "weight": 0.5,
                    "active_time": "2023-08-16T12:00:00Z"
                }
            ]
        }
        product_serializer = ProductSerializer(data=product_data)
        product_serializer.is_valid(raise_exception=True)
        product_serializer.save()

        # Try to create another product with the same name
        duplicate_data = {
            "name": "Duplicate Product",
            "description": "This is another duplicate product.",
            "variants": [
                {
                    "name": "Variant 2",
                    "height": 12.0,
                    "stock": 50,
                    "price": 15.0,
                    "weight": 0.7,
                    "active_time": "2023-08-16T14:00:00Z"
                }
            ]
        }
        request = self.factory.post(
            '/api/products/', json.dumps(duplicate_data), content_type='application/json')
        response = self.view(request)
        # Duplicate product name should lead to a validation error
        self.assertEqual(response.status_code, 400)

    def test_create_product_with_duplicate_variant_name(self):
        data = {
            "name": "Product with Duplicate Variants",
            "description": "This product has variants with duplicate names.",
            "variants": [
                {
                    "name": "Variant 1",
                    "height": 10.0,
                    "stock": 100,
                    "price": 10.0,
                    "weight": 0.5,
                    "active_time": "2023-08-16T12:00:00Z"
                },
                {
                    "name": "Variant 1",  # This is a duplicate name within the same product
                    "height": 12.0,
                    "stock": 50,
                    "price": 15.0,
                    "weight": 0.7,
                    "active_time": "2023-08-16T14:00:00Z"
                }
            ]
        }
        request = self.factory.post(
            '/api/products/', json.dumps(data), content_type='application/json')
        response = self.view(request)
        # Duplicate variant name within the same product should lead to a validation error
        self.assertEqual(response.status_code, 400)

    def test_create_product_with_variant_active_time_ahead(self):
        with patch("product_service.serializers.activate_variant.apply_async") as mock_activate_variant:
            mock_activate_variant.return_value = True
            five_minutes_ahead = datetime.now(
                INDONESIA_TIMEZONE) + timedelta(minutes=10)

            data = {
                "name": "Future Active Variant Product",
                "description": "This product has a variant with active time ahead.",
                "variants": [
                    {
                        "name": "Future Variant",
                        "height": 8.0,
                        "stock": 75,
                        "price": 20.0,
                        "weight": 0.4,
                        "active_time": five_minutes_ahead.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "is_active": False
                    }
                ]
            }
            request = self.factory.post(
                '/api/products/', json.dumps(data), content_type='application/json')
            response = self.view(request)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['status'], 'success')
            self.assertEqual(response.data['message'],
                             'success create 1 product with 1 variant')

            # Variant with active time ahead should trigger the Celery task
            mock_activate_variant.assert_called_once()
