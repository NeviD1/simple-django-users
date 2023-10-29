from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    username = None  # type: ignore
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: UserManager = UserManager()  # type: ignore

    def __str__(self):
        return self.email
