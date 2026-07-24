"""Resolve station coordinates from a public US cities dataset (+ optional Nominatim)."""

from __future__ import annotations

import csv
import logging
import re
import time
from pathlib import Path

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Public US cities list with state codes + coordinates (no API key).
US_CITIES_CSV_URL = (
    "https://raw.githubusercontent.com/kelvins/US-Cities-Database/main/csv/us_cities.csv"
)


def _norm_city(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


class CityCoordinateIndex:
    """Offline city→lat/lon index for USA stations."""

    def __init__(self) -> None:
        self._index: dict[tuple[str, str], tuple[float, float]] = {}

    @classmethod
    def load_or_download(cls, cache_path: Path) -> "CityCoordinateIndex":
        instance = cls()
        if not cache_path.exists():
            logger.info("Downloading US cities reference to %s", cache_path)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            response = requests.get(US_CITIES_CSV_URL, timeout=120)
            response.raise_for_status()
            lines = response.text.splitlines()
            reader = csv.DictReader(lines)
            with cache_path.open("w", newline="", encoding="utf-8") as out:
                writer = csv.DictWriter(
                    out, fieldnames=["city", "state", "latitude", "longitude"]
                )
                writer.writeheader()
                for row in reader:
                    # Upstream: ID,STATE_CODE,STATE_NAME,CITY,COUNTY,LATITUDE,LONGITUDE
                    state = (row.get("STATE_CODE") or "").strip().upper()
                    city = (row.get("CITY") or "").strip()
                    if not city or not state:
                        continue
                    try:
                        lat = float(row["LATITUDE"])
                        lon = float(row["LONGITUDE"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    writer.writerow(
                        {
                            "city": city,
                            "state": state,
                            "latitude": lat,
                            "longitude": lon,
                        }
                    )
            logger.info("Wrote US cities cache: %s", cache_path)

        with cache_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                city = _norm_city(row["city"])
                state = row["state"].strip().upper()
                try:
                    lat = float(row["latitude"])
                    lon = float(row["longitude"])
                except (TypeError, ValueError):
                    continue
                key = (city, state)
                # Keep first; good enough for corridor matching
                if key not in instance._index:
                    instance._index[key] = (lat, lon)

        logger.info("Loaded %s US city coordinates", len(instance._index))
        return instance

    def lookup(self, city: str, state: str) -> tuple[float, float] | None:
        return self._index.get((_norm_city(city), state.strip().upper()))


def attach_coordinates(
    stations: list,
    *,
    use_nominatim_fallback: bool = False,
    nominatim_delay_seconds: float = 1.1,
) -> tuple[list[dict], dict[str, int]]:
    """
    Attach lat/lon to RawStation-like objects.

    Primary path: offline US city index (no per-station external calls).
    Optional Nominatim fallback for unmatched cities (rate-limited).
    """
    from fuel.services.geocoding import GeocodingService

    index = CityCoordinateIndex.load_or_download(settings.US_CITIES_CACHE_PATH)
    geocoder = GeocodingService() if use_nominatim_fallback else None
    city_cache: dict[tuple[str, str], tuple[float, float] | None] = {}

    stats = {
        "geocoded_ok": 0,
        "geocode_failed": 0,
        "nominatim_lookups": 0,
    }
    enriched: list[dict] = []

    for station in stations:
        key = (_norm_city(station.city), station.state)
        coords = index.lookup(station.city, station.state)

        if coords is None and key not in city_cache and geocoder is not None:
            time.sleep(nominatim_delay_seconds)
            place = geocoder.geocode_city_state(station.city, station.state)
            stats["nominatim_lookups"] += 1
            city_cache[key] = (
                (place.latitude, place.longitude) if place else None
            )
            coords = city_cache[key]
        elif coords is None and key in city_cache:
            coords = city_cache[key]

        payload = {
            "opis_id": station.opis_id,
            "name": station.name,
            "address": station.address,
            "city": station.city,
            "state": station.state,
            "rack_id": station.rack_id,
            "price_per_gallon": station.price_per_gallon,
            "latitude": coords[0] if coords else None,
            "longitude": coords[1] if coords else None,
            "geocode_status": "ok" if coords else "failed",
            "is_active": bool(coords),
        }
        if coords:
            stats["geocoded_ok"] += 1
        else:
            stats["geocode_failed"] += 1
        enriched.append(payload)

    return enriched, stats
