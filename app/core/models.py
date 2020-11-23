import os
import uuid

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)
from django.conf import settings


def avatar_file_path(instance, filename):
    """Generating a file path for avatar image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('uploads/avatar/', filename)


def thread_img_file_path(instance, filename):
    """Generating a file path for avatar image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('uploads/thread/', filename)


def reply_img_file_path(instance, filename):
    """Generating a file path for avatar image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('uploads/reply/', filename)


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

    def __str__(self):
        return self.username


# * 6CHAN APP MODELS


class Board(models.Model):
    """Board model for chan app in the system"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=4, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Thread(models.Model):
    """Thread model for chan app in the system"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to=thread_img_file_path, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    board = models.ForeignKey('Board', on_delete=models.CASCADE)
    is_edited = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Reply(models.Model):
    """Reply model for thread"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    text = models.TextField()
    image = models.ImageField(upload_to=reply_img_file_path, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    thread = models.ForeignKey(
        'Thread',
        on_delete=models.CASCADE,
        related_name='reply_to_thread',
        null=True
    )
    reply = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='reply_to_reply',
        null=True
    )
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Upvote(models.Model):
    """Upvote model for thread"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    thread = models.ForeignKey(
        'Thread',
        on_delete=models.CASCADE,
        related_name='upvote_thread'
    )


class Downvote(models.Model):
    """Upvote model for thread"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    thread = models.ForeignKey(
        'Thread',
        on_delete=models.CASCADE,
        related_name='downvote_thread'
    )
