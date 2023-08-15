from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from collections import OrderedDict


class CustomPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at'
