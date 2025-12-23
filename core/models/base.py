from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class SoftDeleteModel(models.Model):
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_deleted_by")
    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['deleted_at']),
        ]

    def delete(self, using=None, keep_parents=False, user=None):
        self.is_active = False
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_active', 'deleted_at', 'deleted_by'])


class AuditModel(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_created_by")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_updated_by")

    class Meta:
        abstract = True