from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    # override the default 'groups' M2M
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',  # anything unique
        blank=True,
        help_text=_('The groups this user belongs to.'),
        verbose_name=_('groups'),
        related_query_name='user',
    )
    # override the default 'user_permissions' M2M
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions_set',  # also unique
        blank=True,
        help_text=_('Specific permissions for this user.'),
        verbose_name=_('user permissions'),
        related_query_name='user',
    )
