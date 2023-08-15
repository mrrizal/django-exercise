from rest_framework.pagination import CursorPagination
from django.conf import settings


class CustomPagination(CursorPagination):
    page_size = settings.PRODUCT_LIMIT_PER_PAGE
    ordering = '-created_at'
