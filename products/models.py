from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from .utils import get_client_ip 
from django.db.models import F
from django.db import models
from django.contrib.auth import get_user_model
from core.models import TimeStampedModel, SoftDeleteModel, AuditModel
import random
import string


User = get_user_model()

class Brand(TimeStampedModel, SoftDeleteModel, AuditModel):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='ecommerce/brand_images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'brands'
        verbose_name_plural = 'Brands'
        ordering = ['-is_active','name']

    def get_image_url(self):
        if self.image:
            image_path = str(self.image)
            if image_path.startswith("http://") or image_path.startswith("https://"):
                return image_path
            try:
                return self.image.url
            except ValueError:
                pass
        return '/static/defaults/default-image.jpg'


class ProductMainCategory(TimeStampedModel, SoftDeleteModel, AuditModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    image = models.ImageField(upload_to='ecommerce/category_images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    cat_ordering = models.IntegerField(default=0, blank=True, null=True)

    class Meta:
        db_table = 'product_category'
        verbose_name_plural = 'Product Categories'
        ordering = ['-is_active','cat_ordering']

    def __str__(self):
        return self.name

    def get_image_url(self):
        if self.image:
            image_path = str(self.image)
            if image_path.startswith("http://") or image_path.startswith("https://"):
                return image_path
            try:
                return self.image.url
            except ValueError:
                pass
        return '/static/defaults/default-image.jpg'

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            num = 1
            while ProductMainCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ProductSubCategory(TimeStampedModel, SoftDeleteModel, AuditModel):
    main_category = models.ForeignKey(ProductMainCategory, on_delete=models.CASCADE, related_name='sub_categories')
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    image = models.ImageField(upload_to='ecommerce/sub_category_images/', blank=True, null=True)
    sub_cat_ordering = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_sub_category'
        verbose_name_plural = 'Product Sub Categories'
        ordering = ['-is_active','sub_cat_ordering']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            num = 1
            while ProductSubCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)
    def get_image_url(self):
        if self.image:
            image_path = str(self.image)
            if image_path.startswith("http://") or image_path.startswith("https://"):
                return image_path
            try:
                return self.image.url
            except ValueError:
                pass
        return '/static/defaults/default-image.jpg'

class Product(TimeStampedModel, SoftDeleteModel, AuditModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    main_category = models.ForeignKey(ProductMainCategory, on_delete=models.CASCADE, related_name='products')
    sub_category = models.ForeignKey(ProductSubCategory, on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=50, blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    total_views = models.PositiveIntegerField(default=0)
    discount_percentage = models.PositiveIntegerField(default=0, blank=True, null=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'products'
        indexes = [models.Index(fields=['-total_views'])]
        verbose_name_plural = 'Products'
        ordering = ['-is_active']

    def generate_sku(self):
        cat = self.main_category.name[:3].upper() if self.main_category else "XXX"
        brand = self.brand.name[:4].upper() if self.brand else "GEN"
        return f"{cat}-{brand}-{self.id}"

    def get_primary_image(self):
        primary = self.product_images.filter(is_primary=True).first()
        if primary:
            return primary.get_image_url()
        return '/static/defaults/default-image.jpg'

    def add_view(self, request):
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        if not ProductView.objects.filter(product=self, session_key=session_key).exists():
            ProductView.objects.create(
                product=self,
                user=request.user if request.user.is_authenticated else None,
                session_key=session_key,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            )
            Product.objects.filter(pk=self.pk).update(total_views=F('total_views') + 1)
            return True  # ✅ indicates new view
        return False


    def in_stock(self):
        return self.quantity > 0

    def on_sale(self):
        return self.sale_price is not None

    @property
    def rating_int(self):
        return int(self.average_rating or 0)

    @property
    def has_half_star(self):
        return (self.average_rating or 0) % 1 >= 0.5

    def __str__(self):
        return self.name

    @property
    def is_new_arrival(self):
        if not self.created_at:
            return False
        return (timezone.now() - self.created_at) <= timedelta(days=30)

    @property
    def is_best_seller(self):
        return self.total_views >= 100 or self.is_featured

    @property
    def display_badge(self):
        if self.is_featured:
            return ("⭐ Featured", "bg-primary")
        elif self.is_best_seller:
            return ("🏆 Best Seller", "bg-warning text-dark")
        elif self.discount_percentage and self.discount_percentage > 0:
            return (f"{self.discount_percentage}% OFF", "bg-danger")
        elif self.is_new_arrival:
            return ("🆕 New Arrival", "bg-success")

        return (None, None)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            num = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ProductImage(TimeStampedModel, SoftDeleteModel, AuditModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to='ecommerce/product_images/', blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Unset other primary images for this product
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        elif not ProductImage.objects.filter(product=self.product, is_primary=True).exists():
            self.is_primary = True
        super().save(*args, **kwargs)

    def get_image_url(self):
        if self.image:
            image_path = str(self.image)
            if image_path.startswith("http://") or image_path.startswith("https://"):
                return image_path
            try:
                return self.image.url
            except ValueError:
                pass
        return '/static/defaults/default-image.jpg'

    class Meta:
        db_table = 'product_images'
        verbose_name_plural = 'Product Images'
        ordering = ['-is_active']

    def __str__(self):
        return self.product.name


class ProductVariant(TimeStampedModel, SoftDeleteModel, AuditModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    price_difference = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    class Meta:
        db_table = 'product_variants'
        unique_together = ('product', 'variant_name', 'value')

    def __str__(self):
        return f"{self.product} - {self.variant_name}: {self.value}"


class InventoryLog(TimeStampedModel, AuditModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_logs')
    change_type = models.CharField(max_length=20, choices=[('in', 'Stock In'), ('out', 'Stock Out')])
    quantity = models.IntegerField()
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'inventory_logs'

    def __str__(self):
        return f"{self.product} - {self.change_type} ({self.quantity})"


class Wishlist(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')

    class Meta:
        db_table = 'wishlist'
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user} - {self.product}"

class ProductView(models.Model):
    product = models.ForeignKey('Product',on_delete=models.CASCADE, related_name='views', db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='product_views')
    session_key = models.CharField(max_length=40, blank=True, null=True, help_text="Anonymous session identifier")
    ip_address = models.GenericIPAddressField( blank=True, null=True,  help_text="Optional: track visitor IP")
    user_agent = models.CharField(max_length=255, blank=True,null=True,help_text="Browser or device info")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_views'
        verbose_name_plural = 'Product Views'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'session_key']),
            models.Index(fields=['product', 'created_at']),
        ]
    
    @classmethod
    def cleanup_old_views(cls, days=180):
        cutoff = timezone.now() - timedelta(days=days)
        cls.objects.filter(created_at__lt=cutoff).delete()
        

    def __str__(self):
        viewer = self.user.username if self.user else f"Session {self.session_key}"
        return f"{self.product.name} viewed by {viewer}"

