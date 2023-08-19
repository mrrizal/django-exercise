from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    # default null
    is_active = models.NullBooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Variant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=255)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    stock = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    active_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    # kalau  gada di req, set nullable / default null
    is_active = models.NullBooleanField()

    # 1 to 1 relation, gunakan untuk column yang temporary

    class Meta:
        unique_together = ['product', 'name']

    def __str__(self):
        return self.name
