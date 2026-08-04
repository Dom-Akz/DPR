from django.db import models
from django.contrib.auth.models import AbstractUser


# departement
class Departement(models.Model):
    name = models.CharField(max_length=100, unique=True)
    chef_departement = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# admin
class Administrateur(AbstractUser):
    departement = models.ForeignKey(
        Departement, on_delete=models.SET_NULL, null=True, related_name="admin"
    )
    is_active = models.BooleanField(default=False)
    is_supperuser = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name
