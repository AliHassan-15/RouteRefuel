from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from fuel.models import FuelStation
from fuel.services.geocoding import GeocodedPlace
from fuel.services.routing import RouteResult


@pytest.mark.django_db
def test_route_endpoint_end_to_end_with_mocks():
    points = [(39.0, -110.0 + i) for i in range(0, 21)]
    expensive_lat, expensive_lon = points[2]
    cheap_lat, cheap_lon = points[8]
    late_lat, late_lon = points[15]

    FuelStation.objects.create(
        opis_id=101,
        name="Test Cheap Stop",
        address="I-80 EXIT 1",
        city="Lincoln",
        state="NE",
        rack_id="1",
        price_per_gallon=Decimal("2.999"),
        latitude=cheap_lat,
        longitude=cheap_lon,
        geocode_status="ok",
        is_active=True,
    )
    FuelStation.objects.create(
        opis_id=102,
        name="Test Expensive Stop",
        address="I-80 EXIT 2",
        city="Omaha",
        state="NE",
        rack_id="2",
        price_per_gallon=Decimal("4.999"),
        latitude=expensive_lat,
        longitude=expensive_lon,
        geocode_status="ok",
        is_active=True,
    )
    FuelStation.objects.create(
        opis_id=103,
        name="Test Late Stop",
        address="I-80 EXIT 3",
        city="Des Moines",
        state="IA",
        rack_id="3",
        price_per_gallon=Decimal("3.499"),
        latitude=late_lat,
        longitude=late_lon,
        geocode_status="ok",
        is_active=True,
    )

    start = GeocodedPlace(
        query="Start, CO",
        label="Start, USA",
        latitude=points[0][0],
        longitude=points[0][1],
        country_code="US",
    )
    finish = GeocodedPlace(
        query="Finish, IL",
        label="Finish, USA",
        latitude=points[-1][0],
        longitude=points[-1][1],
        country_code="US",
    )

    route = RouteResult(
        distance_miles=900.0,
        duration_seconds=50000,
        geometry_latlon=points,
        geometry_geojson={
            "type": "LineString",
            "coordinates": [[lon, lat] for lat, lon in points],
        },
    )

    client = APIClient()
    with (
        patch.object(
            __import__("fuel.services.geocoding", fromlist=["GeocodingService"]).GeocodingService,
            "geocode_usa",
            side_effect=[start, finish],
        ),
        patch.object(
            __import__("fuel.services.routing", fromlist=["RoutingService"]).RoutingService,
            "route",
            return_value=route,
        ),
    ):
        response = client.post(
            reverse("route-plan"),
            {"start": "Start, CO", "finish": "Finish, IL"},
            format="json",
        )

    assert response.status_code == 200, response.content
    body = response.json()

    # Final frontend contract keys
    assert "route_summary" in body
    assert "route_geometry" in body
    assert "coordinates" in body
    assert "fuel_stops" in body
    assert "trip_summary" in body
    assert "meta" in body

    assert body["route_summary"]["distance_miles"] == 900.0
    assert body["route_summary"]["start"]["address"] == "Start, USA"
    assert body["route_geometry"]["type"] == "LineString"
    assert body["coordinates"][0] == [39.0, -110.0]
    assert body["trip_summary"]["total_gallons_used"] == pytest.approx(90.0)
    assert body["trip_summary"]["stop_count"] >= 1
    assert body["fuel_stops"][0]["name"] == "Test Cheap Stop"
    assert "distance_from_start_miles" in body["fuel_stops"][0]
    assert "gallons_purchased" in body["fuel_stops"][0]
    assert "average_price_per_gallon_usd" in body["trip_summary"]
    assert "response_time_ms" in body["meta"]
    assert "external_calls" in body["meta"]
    assert body["meta"]["external_calls"]["per_station"] == 0


@pytest.mark.django_db
def test_health_and_stations_not_ready():
    client = APIClient()
    health = client.get(reverse("health"))
    assert health.status_code == 200
    assert health.json()["stations_active"] == 0

    response = client.post(
        reverse("route-plan"),
        {"start": "Chicago, IL", "finish": "Dallas, TX"},
        format="json",
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "STATIONS_NOT_READY"


@pytest.mark.django_db
def test_validation_error_shape():
    FuelStation.objects.create(
        opis_id=1,
        name="X",
        address="A",
        city="C",
        state="IL",
        price_per_gallon=Decimal("3.0"),
        latitude=41.0,
        longitude=-87.0,
        geocode_status="ok",
        is_active=True,
    )
    client = APIClient()
    response = client.post(reverse("route-plan"), {}, format="json")
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "message" in body["error"]
