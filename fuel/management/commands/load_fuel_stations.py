from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from decimal import Decimal

from fuel.models import FuelStation
from fuel.services.city_geocoder import attach_coordinates
from fuel.services.ingestion import parse_fuel_csv


class Command(BaseCommand):
    help = (
        "Load and geocode fuel stations from fuel-prices-for-be-assessment.csv. "
        "One-time ingestion — not executed on API requests."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            default=str(settings.FUEL_CSV_PATH),
            help="Path to the fuel prices CSV",
        )
        parser.add_argument(
            "--nominatim-fallback",
            action="store_true",
            help="Fall back to Nominatim for cities missing from the offline index.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Optional cap on stations persisted (smoke tests).",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing FuelStation rows before loading.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv"])
        if not csv_path.is_absolute():
            csv_path = settings.BASE_DIR / csv_path
        if not csv_path.exists():
            raise CommandError(f"CSV not found: {csv_path}")

        if options["flush"]:
            deleted, _ = FuelStation.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing rows."))

        self.stdout.write(f"Parsing {csv_path} ...")
        stations, parse_stats = parse_fuel_csv(csv_path)
        self.stdout.write(f"Parse stats: {parse_stats}")

        if options["limit"] > 0:
            stations = stations[: options["limit"]]
            self.stdout.write(self.style.WARNING(f"Limited to {len(stations)} stations."))

        self.stdout.write("Resolving coordinates via offline US cities index ...")
        enriched, geo_stats = attach_coordinates(
            stations,
            use_nominatim_fallback=options["nominatim_fallback"],
        )
        self.stdout.write(f"Geocode stats: {geo_stats}")

        created = updated = 0
        for row in enriched:
            _, was_created = FuelStation.objects.update_or_create(
                opis_id=row["opis_id"],
                defaults={
                    "name": row["name"],
                    "address": row["address"],
                    "city": row["city"],
                    "state": row["state"],
                    "rack_id": row["rack_id"],
                    "price_per_gallon": Decimal(str(row["price_per_gallon"])),
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "geocode_status": row["geocode_status"],
                    "is_active": row["is_active"],
                },
            )
            created += int(was_created)
            updated += int(not was_created)

        active = FuelStation.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. created={created} updated={updated} active_geocoded={active}"
            )
        )
