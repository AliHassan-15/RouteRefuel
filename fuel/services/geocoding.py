"""Nominatim geocoding client + Django cache / DB persistence."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

from fuel.exceptions import GeocodeFailed, GeocodingUnavailable, LocationNotInUSA
from fuel.models import GeocodeCache
from fuel.services.call_stats import ExternalCallStats
from fuel.services.http import request_json

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeocodedPlace:
    query: str
    label: str
    latitude: float
    longitude: float
    country_code: str


def normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def _cache_key(prefix: str, *parts: str) -> str:
    raw = "|".join(parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
    return f"{prefix}:{digest}"


class GeocodingService:
    """Resolve free-text places to coordinates (USA only for trip endpoints)."""

    def __init__(self, stats: ExternalCallStats | None = None) -> None:
        self.base_url = settings.NOMINATIM_BASE_URL.rstrip("/")
        self.user_agent = settings.NOMINATIM_USER_AGENT
        self.stats = stats or ExternalCallStats()

    def geocode_usa(self, query: str) -> GeocodedPlace:
        place = self._geocode(query, country_codes="us")
        if place.country_code and place.country_code.lower() not in {"us", "usa", ""}:
            raise LocationNotInUSA(
                f"'{query}' resolved outside the USA ({place.label}). "
                "Only USA start and finish locations are supported.",
                details={"query": query, "resolved_address": place.label},
            )
        if not place.country_code:
            label_l = place.label.lower()
            if any(x in label_l for x in ("canada", "mexico", "ontario", "quebec")):
                raise LocationNotInUSA(
                    f"'{query}' appears to be outside the USA ({place.label}). "
                    "Only USA start and finish locations are supported.",
                    details={"query": query, "resolved_address": place.label},
                )
        return place

    def geocode_city_state(self, city: str, state: str) -> GeocodedPlace | None:
        try:
            return self._geocode(f"{city}, {state}, USA", country_codes="us")
        except (GeocodeFailed, GeocodingUnavailable, LocationNotInUSA):
            return None

    def _geocode(self, query: str, *, country_codes: str | None = None) -> GeocodedPlace:
        key = normalize_query(query)
        cache_key = _cache_key("geocode", key, country_codes or "")

        cached = cache.get(cache_key)
        if cached:
            self.stats.geocode_cache_hits += 1
            return GeocodedPlace(**cached)

        row = GeocodeCache.objects.filter(query_key=key).first()
        if row:
            self.stats.geocode_cache_hits += 1
            place = GeocodedPlace(
                query=query,
                label=row.label,
                latitude=row.latitude,
                longitude=row.longitude,
                country_code=row.country_code,
            )
            cache.set(cache_key, place.__dict__, timeout=60 * 60 * 24 * 30)
            return place

        params: dict = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        if country_codes:
            params["countrycodes"] = country_codes

        try:
            self.stats.geocode_network += 1
            data = request_json(
                "GET",
                f"{self.base_url}/search",
                params=params,
                headers={"User-Agent": self.user_agent},
                timeout=25.0,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Geocoding provider failure for %r", query)
            raise GeocodingUnavailable(
                "Geocoding service timed out or is unavailable. Please try again shortly.",
                details={"provider": "nominatim", "query": query},
            ) from exc

        if not isinstance(data, list) or not data:
            raise GeocodeFailed(
                f"Could not resolve location '{query}'. "
                "Try a clearer USA place like 'City, ST' or a full street address.",
                details={"query": query},
            )

        hit = data[0]
        address = hit.get("address") or {}
        country_code = (address.get("country_code") or "").upper()
        place = GeocodedPlace(
            query=query,
            label=hit.get("display_name") or query,
            latitude=float(hit["lat"]),
            longitude=float(hit["lon"]),
            country_code=country_code,
        )

        GeocodeCache.objects.update_or_create(
            query_key=key,
            defaults={
                "label": place.label,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "country_code": place.country_code,
            },
        )
        cache.set(cache_key, place.__dict__, timeout=60 * 60 * 24 * 30)
        return place
