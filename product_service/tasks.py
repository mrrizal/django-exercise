import logging
from celery import shared_task

from .models import Variant


@shared_task
def activate_variant(variant_id):
    variant = Variant.objects.get(pk=variant_id)
    variant.is_active = True
    variant.save()
    logging.info(f"variant '{variant.name}' with id {variant_id} activated")
