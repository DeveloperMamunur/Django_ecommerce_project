from django.db import models
from django.utils.text import slugify
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
        return self.brand_name

    class Meta:
        db_table = 'brands'
        verbose_name_plural = 'Brands'
        ordering = ['-is_active','name']

    def get_image_url(self):
        if str(self.image).startswith('http'):
            return self.image
        return f'/media/{self.image}'


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
        if str(self.image).startswith('http'):
            return self.image
        return f'/media/{self.image}'

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
        if str(self.image).startswith('http'):
            return self.image
        return f'/media/{self.image}'

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
        verbose_name_plural = 'Products'
        ordering = ['-is_active']

    def generate_sku(self):
        cat = self.main_category.name[:3].upper() if self.main_category else "XXX"
        brand = self.brand.name[:4].upper() if self.brand else "GEN"
        return f"{cat}-{brand}-{self.id}"

    def __str__(self):
        return self.name

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
        if str(self.image).startswith('http'):
            return self.image
        return f'/media/{self.image}'

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



