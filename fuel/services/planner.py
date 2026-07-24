from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings

from fuel.constants import (
    FUEL_STOP_DWELL_SECONDS,
    MAX_RANGE_MILES,
    MPG,
    RANGE_RESERVE_MILES,
    ROUTE_CORRIDOR_MILES,
    TANK_CAPACITY_GALLONS,
)
from fuel.exceptions import StationsNotReady
from fuel.models import FuelStation
from fuel.services.call_stats import ExternalCallStats
from fuel.services.geo import route_bbox
from fuel.services.geocoding import GeocodingService
from fuel.services.optimizer import build_fuel_plan
from fuel.services.routing import RoutingService

logger = logging.getLogger(__name__)


def _money(value: Decimal) -> float:
    """Round currency only at the display/serialization boundary."""
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class TripPlannerService:
    """
    Orchestrates geocode → route → local optimization.

    External network calls per cold request (upper bound = 3):
      1) Nominatim start
      2) Nominatim finish
      3) OSRM route(start→finish)

    Station lookups never hit an external API.
    """

    def plan(
        self,
        start: str,
        finish: str,
        *,
        depart_at: datetime | None = None,
    ) -> dict:
        started = time.perf_counter()
        stats = ExternalCallStats()
        geocoder = GeocodingService(stats=stats)
        router = RoutingService(stats=stats)

        active_count = FuelStation.objects.filter(is_active=True).count()
        if active_count == 0:
            raise StationsNotReady(
                "No geocoded fuel stations are loaded. "
                "Run: python manage.py load_fuel_stations"
            )

        depart_at = depart_at or datetime.now(timezone.utc)
        if depart_at.tzinfo is None:
            depart_at = depart_at.replace(tzinfo=timezone.utc)

        start_place = geocoder.geocode_usa(start)
        finish_place = geocoder.geocode_usa(finish)
        route = router.route(
            start_place.latitude,
            start_place.longitude,
            finish_place.latitude,
            finish_place.longitude,
        )

        pad = (ROUTE_CORRIDOR_MILES / 69.0) + 0.2
        min_lat, max_lat, min_lon, max_lon = route_bbox(route.geometry_latlon, pad)
        stations = list(
            FuelStation.objects.filter(
                is_active=True,
                latitude__gte=min_lat,
                latitude__lte=max_lat,
                longitude__gte=min_lon,
                longitude__lte=max_lon,
            ).values(
                "opis_id",
                "name",
                "address",
                "city",
                "state",
                "price_per_gallon",
                "latitude",
                "longitude",
            )
        )

        fuel_plan = build_fuel_plan(
            stations=stations,
            route_points_latlon=route.geometry_latlon,
            total_distance_miles=route.distance_miles,
            total_duration_seconds=route.duration_seconds,
            depart_at=depart_at,
            corridor_miles=ROUTE_CORRIDOR_MILES,
        )

        fuel_stops = []
        for stop in fuel_plan.stops:
            fuel_stops.append(
                {
                    "sequence": stop.sequence,
                    "station_id": stop.station_id,
                    "name": stop.name,
                    "address": stop.address,
                    "city": stop.city,
                    "state": stop.state,
                    "latitude": stop.latitude,
                    "longitude": stop.longitude,
                    "price_per_gallon": float(stop.price_per_gallon),
                    "distance_from_start_miles": round(stop.route_mile_marker, 3),
                    "gallons_purchased": round(stop.gallons_for_leg, 6),
                    "cost_usd": _money(stop.cost_exact),
                    "remaining_range_before_refuel_miles": round(
                        stop.remaining_range_before_refuel_miles, 3
                    ),
                    "eta": stop.eta.isoformat().replace("+00:00", "Z"),
                    "dwell_minutes": FUEL_STOP_DWELL_SECONDS // 60,
                }
            )

        total_gallons = fuel_plan.total_gallons_used
        total_cost = fuel_plan.total_cost_exact
        if total_gallons > 0 and total_cost > 0:
            avg_price = _money(total_cost / Decimal(str(total_gallons)))
        else:
            avg_price = 0.0

        # Leaflet-friendly [lat, lon] list (optional companion to GeoJSON).
        coordinates_latlon = [
            [round(lat, 6), round(lon, 6)] for lat, lon in route.geometry_latlon
        ]

        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        external = stats.as_dict()

        logger.info(
            "EXTERNAL_CALLS total=%s geocode=%s routing=%s "
            "geocode_cache_hits=%s routing_cache_hits=%s | "
            "route_plan start=%r finish=%r distance_mi=%.2f stops=%s "
            "response_ms=%.1f stations_in_bbox=%s",
            external["total"],
            external["geocode"],
            external["routing"],
            external["geocode_cache_hits"],
            external["routing_cache_hits"],
            start,
            finish,
            route.distance_miles,
            len(fuel_stops),
            elapsed_ms,
            len(stations),
        )

        return {
            "route_summary": {
                "distance_miles": round(route.distance_miles, 3),
                "duration_seconds": round(route.duration_seconds, 1),
                "duration_hours": round(route.duration_seconds / 3600.0, 3),
                "destination_eta": fuel_plan.destination_eta.isoformat().replace(
                    "+00:00", "Z"
                ),
                "start": {
                    "query": start,
                    "address": start_place.label,
                    "latitude": start_place.latitude,
                    "longitude": start_place.longitude,
                },
                "finish": {
                    "query": finish,
                    "address": finish_place.label,
                    "latitude": finish_place.latitude,
                    "longitude": finish_place.longitude,
                },
            },
            "route_geometry": route.geometry_geojson,
            "coordinates": coordinates_latlon,
            "fuel_stops": fuel_stops,
            "trip_summary": {
                "total_gallons_used": round(total_gallons, 6),
                "total_fuel_cost_usd": _money(total_cost),
                "average_price_per_gallon_usd": avg_price,
                "stop_count": len(fuel_stops),
            },
            "vehicle": {
                "mpg": MPG,
                "max_range_miles": MAX_RANGE_MILES,
                "tank_capacity_gallons": TANK_CAPACITY_GALLONS,
                "range_reserve_miles": RANGE_RESERVE_MILES,
                "route_corridor_miles": ROUTE_CORRIDOR_MILES,
            },
            "meta": {
                "response_time_ms": elapsed_ms,
                "external_calls": external,
                "stations_considered": active_count,
                "stations_in_route_bbox": len(stations),
                "depart_at": depart_at.isoformat().replace("+00:00", "Z"),
                "currency_rounding": (
                    "USD values rounded to 2 decimals only in this response; "
                    "internal math uses full-precision Decimals."
                ),
            },
        }
