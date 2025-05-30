from django.db import models
from accounts.models import Account
from store.models import Product, Variation


class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cart_id


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE, blank=True, null=True)
    variations = models.ManyToManyField(Variation, blank=True)
    
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cart Item"

    def sub_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return self.product.product_name
