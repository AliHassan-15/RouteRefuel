"""OSRM routing client — ideally one call per trip plan."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

from fuel.exceptions import NoDrivingRoute, RoutingUnavailable
from fuel.services.call_stats import ExternalCallStats
from fuel.services.geo import decode_polyline
from fuel.services.http import request_json

logger = logging.getLogger(__name__)

METERS_PER_MILE = 1609.344


def _route_cache_key(start_lat, start_lon, end_lat, end_lon) -> str:
    raw = (
        f"{round(start_lat, 4)},{round(start_lon, 4)}:"
        f"{round(end_lat, 4)},{round(end_lon, 4)}"
    )
    return "osrm:" + hashlib.sha256(raw.encode()).hexdigest()[:32]


@dataclass(frozen=True)
class RouteResult:
    distance_miles: float
    duration_seconds: float
    geometry_latlon: list[tuple[float, float]]  # (lat, lon)
    geometry_geojson: dict  # GeoJSON LineString lon,lat


class RoutingService:
    def __init__(self, stats: ExternalCallStats | None = None) -> None:
        self.base_url = settings.OSRM_BASE_URL.rstrip("/")
        self.stats = stats or ExternalCallStats()

    def route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
    ) -> RouteResult:
        cache_key = _route_cache_key(start_lat, start_lon, end_lat, end_lon)
        cached = cache.get(cache_key)
        if cached:
            self.stats.routing_cache_hits += 1
            return RouteResult(**cached)

        coords = f"{start_lon},{start_lat};{end_lon},{end_lat}"
        url = f"{self.base_url}/route/v1/driving/{coords}"
        params = {
            "overview": "full",
            "geometries": "polyline",
            "steps": "false",
        }

        try:
            self.stats.routing_network += 1
            data = request_json("GET", url, params=params, timeout=30.0)
        except Exception as exc:  # noqa: BLE001
            logger.exception("OSRM routing failure")
            raise RoutingUnavailable(
                "Routing service timed out or is unavailable. Please try again shortly.",
                details={"provider": "osrm"},
            ) from exc

        if not isinstance(data, dict) or data.get("code") != "Ok" or not data.get("routes"):
            raise NoDrivingRoute(
                "No driving route could be found between those USA locations.",
                details={
                    "provider_response_code": (data or {}).get("code")
                    if isinstance(data, dict)
                    else None
                },
            )

        route = data["routes"][0]
        distance_miles = float(route["distance"]) / METERS_PER_MILE
        duration_seconds = float(route["duration"])
        latlon = decode_polyline(route["geometry"])
        if len(latlon) < 2:
            raise NoDrivingRoute("Routing provider returned an empty geometry.")

        geojson = {
            "type": "LineString",
            "coordinates": [[lon, lat] for lat, lon in latlon],
        }
        result = RouteResult(
            distance_miles=distance_miles,
            duration_seconds=duration_seconds,
            geometry_latlon=latlon,
            geometry_geojson=geojson,
        )
        cache.set(
            cache_key,
            {
                "distance_miles": result.distance_miles,
                "duration_seconds": result.duration_seconds,
                "geometry_latlon": result.geometry_latlon,
                "geometry_geojson": result.geometry_geojson,
            },
            timeout=60 * 60 * 24 * 7,
        )
        return result
