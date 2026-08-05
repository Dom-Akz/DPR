from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


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
    ROLE_CHOICES = [
        ("N2", "Stratégique (N+2)"),
        ("N1", "Tactique (N+1)"),
        ("N", "Opérationnel (N)"),
        ("N0", "Technique (Niveau 1)"),
    ]

    departement = models.ForeignKey(
        Departement, on_delete=models.SET_NULL, null=True, related_name="admin"
    )
    role = models.CharField(
        "Rôle",
        max_length=2,
        choices=ROLE_CHOICES,
        null=True,
        blank=True,
        help_text="Niveau d'indicateurs auquel cet administrateur a accès.",
    )
    is_active = models.BooleanField(default=False)
    is_supperuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name


class Solution(models.Model):
    name = models.CharField("Solution", max_length=100, unique=True)

    class Meta:
        verbose_name = "Solution"
        verbose_name_plural = "Solutions"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Indicator(models.Model):
    LEVEL_CHOICES = [
        ("N2", "Stratégique (N+2)"),
        ("N1", "Tactique (N+1)"),
        ("N", "Opérationnel (N)"),
        ("N0", "Technique (Niveau 1)"),
    ]

    KIND_CHOICES = [
        ("KPI", "KPI"),
        ("KRI", "KRI"),
    ]

    NATURE_CHOICES = [
        ("PCT", "Pourcentage (%)"),
        ("NUM", "Nombre"),
        ("DUR", "Durée"),
    ]

    name = models.CharField("Indicateur", max_length=255)
    level = models.CharField(
        "Niveau", max_length=2, choices=LEVEL_CHOICES, db_index=True
    )
    kind = models.CharField("Type", max_length=3, choices=KIND_CHOICES)
    nature = models.CharField(
        "Nature", max_length=3, choices=NATURE_CHOICES, default="PCT"
    )
    formula = models.TextField("Formule")
    objective = models.TextField("Objectif / Définition")

    solution = models.ForeignKey(
        "Solution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="indicators",
        verbose_name="Solution étudiée",
    )

    class Meta:
        verbose_name = "Indicateur"
        verbose_name_plural = "Indicateurs"
        ordering = ["level", "kind", "name"]


class IndicatorMeasurement(models.Model):
    indicator = models.ForeignKey(
        Indicator, on_delete=models.CASCADE, related_name="measurements"
    )
    value = models.DecimalField("Valeur", max_digits=10, decimal_places=2)
    calculated_at = models.DateTimeField(
        "Calculé le", default=timezone.now, db_index=True
    )

    class Meta:
        verbose_name = "Mesure"
        verbose_name_plural = "Mesures"
        ordering = ["-calculated_at"]

    def __str__(self):
        return f"{self.indicator.name} = {self.value} ({self.calculated_at:%Y-%m-%d %H:%M})"
