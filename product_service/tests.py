import json
from django.utils import timezone
from datetime import datetime, timedelta
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from unittest.mock import patch, MagicMock

from .models import Product, Variant
from .serializers import ProductSerializer, INDONESIA_TIMEZONE
from .views import ProductViewSet
from julo.celery import app as celery_app


class ProductViewSetCreateTest(TestCase):
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


class ProductViewSetListTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ProductViewSet.as_view({'get': 'list'})

        # Create test data
        self.product1 = Product.objects.create(
            name='Product 1', description='Description 1')
        self.product1.created_at = timezone.now() - timedelta(days=2)
        self.product1.save()
        self.variant1 = Variant.objects.create(
            product=self.product1, name='Variant 1', height=10.0, stock=100, price=10.0, weight=0.5, active_time=timezone.now())

        self.product2 = Product.objects.create(
            name='Product 2', description='Description 2')
        self.variant2 = Variant.objects.create(
            product=self.product2, name='Variant 2', height=12.0, stock=50, price=15.0, weight=0.7, active_time=timezone.now())

    def test_list_products(self):
        request = self.factory.get('/api/products/')
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        # Ensure all products are returned
        self.assertEqual(len(response.data['results']), 2)

    def test_list_products_with_created_at_gte(self):
        # Add 1 second to the created_at time of variant1
        created_at_gte = (self.variant1.created_at +
                          timedelta(seconds=1)).strftime('%d-%m-%Y')
        request = self.factory.get(
            '/api/products/', {'created_at_gte': created_at_gte})
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        # Only product1 should be returned
        self.assertEqual(len(response.data['results']), 1)

    def test_list_products_with_created_at_lte(self):
        # Add 1 second to the created_at time of variant1
        created_at_lte = datetime.now().strftime('%d-%m-%Y')
        request = self.factory.get(
            '/api/products/', {'created_at_lte': created_at_lte})
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        # Both products should be returned
        self.assertEqual(len(response.data['results']), 2)

    def test_list_products_with_pagination(self):
        # Create more products to trigger pagination
        for i in range(10):
            Product.objects.create(
                name=f'Test Product {i}', description='Description')

        request = self.factory.get('/api/products/')
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        # Paginated response should have 'results'
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 10)

    def test_list_products_with_invalid_created_at(self):
        request = self.factory.get(
            '/api/products/', {'created_at_gte': 'invalid_date'})
        response = self.view(request)
        # Invalid date format should result in a bad request
        self.assertEqual(response.data, {
            "next": None,
            "previous": None,
            "results": []
        })
        self.assertEqual(response.status_code, 200)

    def test_list_products_with_empty_queryset(self):
        # Delete all products to make queryset empty
        Product.objects.all().delete()

        request = self.factory.get('/api/products/')
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        # Empty queryset should return empty list
        self.assertEqual(len(response.data['results']), 0)

    def test_list_products_within_created_at_range(self):
        # Add 1 second to the created_at time of variant1
        created_at_gte = (datetime.now() - timedelta(days=2)
                          ).strftime('%d-%m-%Y')
        created_at_lte = (self.variant2.created_at +
                          timedelta(seconds=1)).strftime('%d-%m-%Y')
        request = self.factory.get(
            '/api/products/', {'created_at_gte': created_at_gte, 'created_at_lte': created_at_lte})
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        # Both products should be returned
        self.assertEqual(len(response.data['results']), 2)

    def test_list_products_with_invalid_date_range(self):
        request = self.factory.get(
            '/api/products/', {'created_at_gte': 'invalid_date', 'created_at_lte': 'invalid_date'})
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['next'], None)
        self.assertEqual(response.data['previous'], None)

    def test_list_products_with_max_two_variants(self):
        # Create a product with three variants
        product3 = Product.objects.create(
            name='Product 3', description='Description 3')
        Variant.objects.create(
            product=product3, name='Variant 3A', height=10.0, stock=100, price=10.0, weight=0.5, active_time=timezone.now())
        Variant.objects.create(
            product=product3, name='Variant 3B', height=12.0, stock=50, price=15.0, weight=0.7, active_time=timezone.now())
        Variant.objects.create(
            product=product3, name='Variant 3C', height=15.0, stock=25, price=20.0, weight=1.0, active_time=timezone.now())

        request = self.factory.get('/api/products/')
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        # Ensure all three products are returned, but only two variants each
        self.assertEqual(len(response.data['results']), 3)

        for product in response.data['results']:
            self.assertEqual(len(product['variants']) <= 2, True)
