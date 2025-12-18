from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from core.models import TimeStampedModel, SoftDeleteModel
from products.models import Product, ProductImage

# Create your models here.

User = get_user_model()

class Cart(TimeStampedModel, SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_by = models.CharField(null=True, blank=True)
    updated_by = models.CharField(null=True, blank=True)

    class Meta:
        db_table = 'cart'

    def __str__(self):
        if self.user:
            return f"Cart of {self.user}"
        return f"Cart {self.id} (Guest)"


class CartItem(TimeStampedModel, SoftDeleteModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.FloatField(default=0.0)
    created_by = models.CharField(null=True, blank=True)
    updated_by = models.CharField(null=True, blank=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

    @property
    def subtotal(self):
        return self.price * self.quantity

class Coupon(TimeStampedModel, SoftDeleteModel):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=[('fixed', 'Fixed'), ('percent', 'Percentage')])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'coupons'

    def __str__(self):
        return self.code


class BillingAddress(TimeStampedModel):
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)

    class Meta:
        db_table = 'billing_addresses'

    def __str__(self):
        return f"{self.address}, {self.city}"


class ShippingAddress(TimeStampedModel):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)

    class Meta:
        db_table = 'shipping_addresses'

    def __str__(self):
        return f"{self.address}, {self.city}"


class Order(TimeStampedModel, SoftDeleteModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    order_number = models.CharField(max_length=100, blank=True, null=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    billing_address = models.OneToOneField(BillingAddress, on_delete=models.SET_NULL, blank=True, null=True, related_name='order_billing')
    shipping_address = models.OneToOneField(ShippingAddress, on_delete=models.SET_NULL, blank=True, null=True, related_name='order_shipping')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    order_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    shipping_charge = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    discount = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    coupon_discount = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    vat_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    tax_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    paid_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    due_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2)
    grand_total = models.DecimalField(default=0, max_digits=20, decimal_places=2)

    class Meta:
        db_table = 'orders'

    def __str__(self):
        return f"{self.order_number} ({self.customer} - {self.created_at})"

    def save(self, *args, **kwargs):
        import datetime
        if not self.order_number:
            today = datetime.date.today()
            count = Order.objects.filter(order_number__startswith=f"{today:%Y%m}").count()
            self.order_number = f"{today:%Y%m}{count + 1:04d}{today:%d}{self.customer.id}"
        super().save(*args, **kwargs)


class OrderDetail(TimeStampedModel, SoftDeleteModel):
    order = models.ForeignKey(Order, related_name='order_details', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    unit_price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    is_discount = models.BooleanField(default=False)
    discount_price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(default=0, max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_details'

    def __str__(self):
        return f"{self.order.order_number} ({self.product} - {self.quantity})"
