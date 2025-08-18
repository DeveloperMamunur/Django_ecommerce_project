from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel, SoftDeleteModel, AuditModel




class MenuList(TimeStampedModel, SoftDeleteModel, AuditModel):
    class MenuType(models.TextChoices):
        MAIN = 'main', 'Main Menu'
        SUB = 'sub', 'Sub Menu'
        SUB_CHILD = 'sub_child', 'Sub Child Menu'

    module_name = models.CharField(max_length=100, db_index=True)
    menu_name = models.CharField(max_length=100, unique=True, db_index=True)
    menu_url = models.CharField(max_length=250, unique=True)
    menu_icon = models.CharField(max_length=250, blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    menu_type = models.CharField(max_length=20, choices=MenuType.choices, default=MenuType.MAIN)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "menu_list"
        ordering = ['menu_type', 'menu_name']

    def __str__(self):
        return self.menu_name