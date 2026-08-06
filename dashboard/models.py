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

    risk_threshold = models.DecimalField(
        "Seuil de risque",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=50.00,
    )

    target_value = models.DecimalField(
        "Valeur cible", max_digits=10, decimal_places=2, null=True, blank=True
    )
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

    @property
    def latest_measurement(self):
        """Get the latest measurement for this indicator"""
        return self.measurements.first()

    @property
    def latest_value(self):
        """Get the latest value for this indicator"""
        latest = self.measurements.first()
        return latest.value if latest else None

    @property
    def latest_date(self):
        """Get the latest date for this indicator"""
        latest = self.measurements.first()
        return latest.calculated_at if latest else None

    @property
    def risk_status(self):
        """Determine risk status based on latest value (only for KRI)"""
        if self.kind != "KRI":
            return None

        value = self.latest_value
        if value is None:
            return "green"

        if value > 50:
            return "red"
        elif value > 20:
            return "yellow"
        else:
            return "green"

    @property
    def current_value(self):
        """Alias for latest_value for better readability"""
        return self.latest_value

    @property
    def target_diff(self):
        """Calculate difference from target"""
        if self.current_value is not None and self.target_value is not None:
            return self.current_value - self.target_value
        return None

    @property
    def target_diff_percentage(self):
        """Calculate percentage difference from target"""
        if (
            self.current_value is not None
            and self.target_value
            and self.target_value != 0
        ):
            return (
                (self.current_value - self.target_value) / abs(self.target_value)
            ) * 100
        return None

    @property
    def performance_status(self):
        """Get performance status based on target achievement"""
        diff = self.target_diff_percentage

        if diff is None:
            return "unknown"

        if diff >= 0:
            return "above_target"
        elif diff >= -10:
            return "near_target"
        elif diff >= -25:
            return "below_target"
        else:
            return "far_below_target"

    @property
    def performance_color(self):
        """Get color for performance status"""
        colors = {
            "above_target": "#3dd68c",  # green
            "near_target": "#ffd000",  # yellow
            "below_target": "#ff9500",  # orange
            "far_below_target": "#ff4757",  # red
            "unknown": "#6c757d",  # gray
        }
        return colors.get(self.performance_status, "#6c757d")

    @property
    def performance_label(self):
        """Get human-readable performance label"""
        labels = {
            "above_target": "✓ On Target",
            "near_target": "⚠ Near Target",
            "below_target": "▼ Below Target",
            "far_below_target": "✗ Far Below",
            "unknown": "— No Target",
        }
        return labels.get(self.performance_status, "Unknown")

    @property
    def risk_percentage(self):
        """Calculate risk percentage (0-100)"""
        if not self.current_value or not self.risk_threshold:
            return 0
        percentage = (self.current_value / self.risk_threshold) * 100
        return min(percentage, 100)

    @property
    def risk_color(self):
        """Get color based on risk level"""
        percentage = self.risk_percentage

        if percentage >= 100:
            return "#ff4757"  # red - critical
        elif percentage >= 70:
            return "#ffd000"  # yellow - warning
        else:
            return "#3dd68c"  # green - normal

    @property
    def risk_class(self):
        """Get CSS class based on risk level"""
        percentage = self.risk_percentage

        if percentage >= 100:
            return "risk-critical"
        elif percentage >= 70:
            return "risk-warning"
        else:
            return "risk-normal"

    @property
    def risk_label(self):
        """Get human-readable risk label"""
        percentage = self.risk_percentage

        if percentage >= 100:
            return "CRITICAL"
        elif percentage >= 70:
            return "WARNING"
        else:
            return "NORMAL"


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
