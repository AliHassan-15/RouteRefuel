from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from fuel.constants import MAX_RANGE_MILES, MPG
from fuel.services.ingestion import RawStation, dedupe_stations, parse_fuel_csv
from fuel.services.optimizer import build_fuel_plan


def test_dedupe_keeps_complete_name_and_lowest_price():
    rows = [
        RawStation(
            opis_id=20,
            name="PILOT #1243",
            address="I-8, EXIT 119 & SR-85",
            city="Gila Bend",
            state="AZ",
            rack_id="930",
            price_per_gallon=3.899,
        ),
        RawStation(
            opis_id=20,
            name="PILOT TRAVEL CENTER #1243",
            address="I-8, EXIT 119 & SR-85",
            city="Gila Bend",
            state="AZ",
            rack_id="930",
            price_per_gallon=3.799,
        ),
    ]
    deduped = dedupe_stations(rows)
    assert len(deduped) == 1
    assert deduped[0].name == "PILOT TRAVEL CENTER #1243"
    assert deduped[0].price_per_gallon == 3.799


def test_parse_fuel_csv_filters_canada_and_strips(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "OPIS Truckstop ID,Truckstop Name,Address,City,State,Rack ID,Retail Price\n"
        '7,WOODSHED,"I-44, EXIT 283",Big Cabin ,OK,307,3.007\n'
        "7,WOODSHED OF BIG CABIN,\"I-44, EXIT 283\",Big Cabin,OK,307,2.900\n"
        "629,FLYING J #850,ADDR,Edmonton,AB,1,4.399\n",
        encoding="utf-8",
    )
    stations, stats = parse_fuel_csv(csv_path)
    assert stats["canadian_skipped"] == 1
    assert len(stations) == 1
    assert stations[0].city == "Big Cabin"
    assert stations[0].name == "WOODSHED OF BIG CABIN"
    assert stations[0].price_per_gallon == 2.900


def _straight_route(miles: float, n: int = 50) -> list[tuple[float, float]]:
    """Synthetic west→east route near 39N for deterministic tests."""
    # ~69 miles per degree longitude at this latitude*cos — use crude spacing.
    start_lon = -100.0
    deg = miles / 55.0  # approximate lon span
    return [(39.0, start_lon + (deg * i / (n - 1))) for i in range(n)]


def test_optimizer_picks_cheapest_not_nearest_and_costs_audit():
    """
    Route ~900 miles → needs fuel stops.
    Place an expensive station early (near) and a cheap one farther but still
    inside the first reachable window — algorithm must pick the cheap one.
    """
    total_miles = 900.0
    points = _straight_route(total_miles)
    # Fake stations already annotated-compatible (lat/lon on corridor)
    # mile ~100 expensive, mile ~400 cheap, mile ~700 medium
    stations = [
        {
            "opis_id": 1,
            "name": "EXPENSIVE NEAR",
            "address": "A",
            "city": "Near",
            "state": "OK",
            "price_per_gallon": Decimal("5.000"),
            "latitude": 39.0,
            "longitude": -100.0 + (100 / 55.0),
        },
        {
            "opis_id": 2,
            "name": "CHEAP FARTHER",
            "address": "B",
            "city": "Far",
            "state": "OK",
            "price_per_gallon": Decimal("2.500"),
            "latitude": 39.0,
            "longitude": -100.0 + (400 / 55.0),
        },
        {
            "opis_id": 3,
            "name": "MID LATE",
            "address": "C",
            "city": "Late",
            "state": "TX",
            "price_per_gallon": Decimal("3.000"),
            "latitude": 39.0,
            "longitude": -100.0 + (700 / 55.0),
        },
    ]

    plan = build_fuel_plan(
        stations=stations,
        route_points_latlon=points,
        total_distance_miles=total_miles,
        total_duration_seconds=36000,
        depart_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        corridor_miles=50.0,  # generous for synthetic geometry
    )

    assert plan.total_gallons_used == pytest.approx(total_miles / MPG)
    assert plan.stops, "expected at least one fuel stop for a 900-mile trip"
    assert plan.stops[0].name == "CHEAP FARTHER"

    # Every mile should be priced exactly once across stop gallon attributions.
    priced_gallons = sum(s.gallons_for_leg for s in plan.stops)
    assert priced_gallons == pytest.approx(plan.total_gallons_used, rel=1e-6)

    # Remaining range before first stop should be MAX_RANGE - inbound distance.
    first = plan.stops[0]
    assert first.remaining_range_before_refuel_miles == pytest.approx(
        MAX_RANGE_MILES - first.leg_distance_miles, abs=2.0
    )
    assert first.eta.isoformat().startswith("2026-01-01")
