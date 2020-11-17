import os
import uuid

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)


def avatar_file_path(instance, filename):
    """Generating a file path for avatar image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('uploads/avatar/', filename)


class UserManager(BaseUserManager):
    """Custom user model manager to support custom user model"""

    def create_user(self, email, username, password=None, **extra_fields):
        """Create and save a new user"""
        if not email:
            raise ValueError('User must have an email address!')

        if not username:
            raise ValueError('User must have an username!')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, username, password):
        """Create and save a new superuser"""
        user = self.create_user(email, username, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for db in the system"""
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=255, unique=True)
    date_of_birth = models.DateField(null=True)
    avatar = models.ImageField(
        upload_to=avatar_file_path,
        default='uploads/defaults/default.png'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', ]
