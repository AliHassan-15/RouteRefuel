from __future__ import annotations

from django.db import models


class FuelStation(models.Model):
    """A USA truck stop with a known retail diesel/fuel price and coordinates."""

    opis_id = models.PositiveIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=128, db_index=True)
    state = models.CharField(max_length=2, db_index=True)
    rack_id = models.CharField(max_length=32, blank=True, default="")
    price_per_gallon = models.DecimalField(max_digits=10, decimal_places=6)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geocode_status = models.CharField(
        max_length=32,
        default="pending",
        db_index=True,
        help_text="pending | ok | failed",
    )
    is_active = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["state", "is_active"]),
            models.Index(fields=["is_active", "price_per_gallon"]),
        ]
        ordering = ["opis_id"]

    def __str__(self) -> str:
        return f"{self.name} ({self.city}, {self.state}) @ {self.price_per_gallon}"


class GeocodeCache(models.Model):
    """Persistent cache for free-text place → coordinates lookups."""

    query_key = models.CharField(max_length=512, unique=True)
    label = models.CharField(max_length=512)
    latitude = models.FloatField()
    longitude = models.FloatField()
    country_code = models.CharField(max_length=2, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.query_key
