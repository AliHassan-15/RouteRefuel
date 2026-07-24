"""
Fuel-stop optimization.

Tradeoff (also documented in README):
- We do NOT pick the nearest station. Nearest is often expensive.
- Within each reachable window along the route (current position → remaining
  usable range), we select the *lowest price/gallon* station that still lies
  inside the route corridor. Among equal prices, we prefer the farthest along
  the route to reduce stop count.
- This greedy look-ahead is not a global DP optimum, but it is deterministic,
  fast, respects the 500-mile hard constraint, and matches the assignment's
  "cost-effective" intent without per-station external API calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Sequence

from fuel.constants import (
    FUEL_STOP_DWELL_SECONDS,
    MAX_FUEL_STOPS,
    MAX_RANGE_MILES,
    MPG,
    RANGE_RESERVE_MILES,
    ROUTE_CORRIDOR_MILES,
    USABLE_RANGE_MILES,
)
from fuel.exceptions import NoFeasibleFuelPlan
from fuel.services.geo import build_route_mile_markers, stations_near_route


@dataclass
class PlannedStop:
    sequence: int
    station_id: int
    name: str
    address: str
    city: str
    state: str
    latitude: float
    longitude: float
    price_per_gallon: Decimal
    route_mile_marker: float
    leg_distance_miles: float
    gallons_for_leg: float
    cost_exact: Decimal  # full precision; round only at serialization
    remaining_range_before_refuel_miles: float
    eta: datetime


@dataclass
class FuelPlan:
    stops: list[PlannedStop]
    total_distance_miles: float
    total_gallons_used: float
    total_cost_exact: Decimal
    destination_eta: datetime


def _select_stops_along_route(nearby: list[dict], total_miles: float) -> list[dict]:
    """Greedy cheapest-in-window selection with hard range constraints."""
    if total_miles <= MAX_RANGE_MILES:
        return []

    selected: list[dict] = []
    position = 0.0
    remaining_range = MAX_RANGE_MILES

    while total_miles - position > remaining_range:
        window_end = position + remaining_range - RANGE_RESERVE_MILES
        candidates = [
            s
            for s in nearby
            if position < s["route_mile"] <= window_end
        ]
        if not candidates:
            raise NoFeasibleFuelPlan(
                (
                    f"No viable fuel stop found within the remaining "
                    f"{remaining_range:.0f}-mile vehicle range near mile "
                    f"{position:.1f} of the route (search window ends at mile "
                    f"{window_end:.1f}). The route corridor may lack priced "
                    f"stations in this stretch, or stations are too far from "
                    f"the driving path. Try different USA endpoints."
                ),
                details={
                    "reason": "no_station_in_reachable_window",
                    "position_mile": round(position, 3),
                    "remaining_range_miles": remaining_range,
                    "window_end_mile": round(window_end, 3),
                    "max_range_miles": MAX_RANGE_MILES,
                    "corridor_miles": ROUTE_CORRIDOR_MILES,
                },
            )

        # Cost-driven: cheapest price; tie-break farthest along route (fewer stops).
        best = min(
            candidates,
            key=lambda s: (float(s["price_per_gallon"]), -float(s["route_mile"])),
        )
        selected.append(best)
        if len(selected) > MAX_FUEL_STOPS:
            raise NoFeasibleFuelPlan(
                "Fuel plan exceeded maximum allowed stops.",
                details={"max_stops": MAX_FUEL_STOPS},
            )

        # Fill to full at each chosen stop.
        position = float(best["route_mile"])
        remaining_range = MAX_RANGE_MILES

    # Ensure finish is reachable from last stop (or start).
    if total_miles - position > MAX_RANGE_MILES:
        raise NoFeasibleFuelPlan(
            "Last fuel stop cannot reach the destination within vehicle range.",
            details={"position_mile": position, "total_miles": total_miles},
        )
    return selected


def build_fuel_plan(
    *,
    stations: Sequence[dict],
    route_points_latlon: Sequence[tuple[float, float]],
    total_distance_miles: float,
    total_duration_seconds: float,
    depart_at: datetime,
    corridor_miles: float = ROUTE_CORRIDOR_MILES,
) -> FuelPlan:
    """
    Build an ordered, cost-auditable fuel plan.

    Cost model (auditable):
    - total_gallons_used = total_route_miles / MPG
    - Partition the trip into legs between waypoints
      [start, stop_1, ..., stop_k, finish].
    - Gallons for leg j = leg_miles_j / MPG.
    - Leg start→stop_1 is priced at stop_1.
    - Leg stop_i → stop_{i+1} is priced at stop_{i+1}.
    - Leg last_stop → finish is priced at last_stop.
      (If there are no stops, total cost is 0 and gallons_used still reported.)

    Remaining range before refuel at a stop = miles of fuel left on arrival,
    assuming a full tank at start and fill-to-full at each prior stop.
    """
    if depart_at.tzinfo is None:
        depart_at = depart_at.replace(tzinfo=timezone.utc)

    mile_markers = build_route_mile_markers(route_points_latlon, total_distance_miles)
    nearby = stations_near_route(
        stations, route_points_latlon, mile_markers, corridor_miles
    )
    chosen = _select_stops_along_route(nearby, total_distance_miles)

    waypoints_miles = [0.0] + [float(s["route_mile"]) for s in chosen] + [total_distance_miles]
    planned: list[PlannedStop] = []
    total_cost = Decimal("0")
    cursor_time = depart_at

    # Track range assuming fill-to-full after each stop / full at start.
    range_at_departure = MAX_RANGE_MILES

    for idx, station in enumerate(chosen):
        prev_mile = waypoints_miles[idx]
        stop_mile = waypoints_miles[idx + 1]
        next_mile = waypoints_miles[idx + 2]

        inbound = stop_mile - prev_mile
        outbound = next_mile - stop_mile

        remaining_before = range_at_departure - inbound
        if remaining_before < -1e-6:
            raise NoFeasibleFuelPlan(
                "Vehicle would run out of fuel before reaching a planned stop.",
                details={"stop": station.get("name"), "remaining_before": remaining_before},
            )

        # Cost attribution for this stop:
        # - prices the inbound leg (start→S1 or S_{i-1}→S_i)
        # - and, if this is the last stop, also prices the final outbound leg.
        gallons = inbound / MPG
        if idx == len(chosen) - 1:
            gallons += outbound / MPG

        price = Decimal(str(station["price_per_gallon"]))
        cost = Decimal(str(gallons)) * price
        total_cost += cost

        drive_seconds = (
            total_duration_seconds * (inbound / total_distance_miles)
            if total_distance_miles > 0
            else 0.0
        )
        eta = cursor_time + timedelta(seconds=drive_seconds)

        planned.append(
            PlannedStop(
                sequence=idx + 1,
                station_id=int(station["opis_id"]),
                name=station["name"],
                address=station["address"],
                city=station["city"],
                state=station["state"],
                latitude=float(station["latitude"]),
                longitude=float(station["longitude"]),
                price_per_gallon=price,
                route_mile_marker=stop_mile,
                leg_distance_miles=inbound,
                gallons_for_leg=gallons,
                cost_exact=cost,
                remaining_range_before_refuel_miles=max(0.0, remaining_before),
                eta=eta,
            )
        )

        cursor_time = eta + timedelta(seconds=FUEL_STOP_DWELL_SECONDS)
        range_at_departure = MAX_RANGE_MILES  # fill to full

    # Destination ETA: drive final outbound (or full trip if no stops)
    if chosen:
        final_leg = waypoints_miles[-1] - waypoints_miles[-2]
    else:
        final_leg = total_distance_miles
    final_drive = (
        total_duration_seconds * (final_leg / total_distance_miles)
        if total_distance_miles > 0
        else 0.0
    )
    destination_eta = cursor_time + timedelta(seconds=final_drive)

    return FuelPlan(
        stops=planned,
        total_distance_miles=total_distance_miles,
        total_gallons_used=total_distance_miles / MPG,
        total_cost_exact=total_cost,
        destination_eta=destination_eta,
    )


# Re-export for tests / clarity
__all__ = [
    "FuelPlan",
    "PlannedStop",
    "build_fuel_plan",
    "MAX_RANGE_MILES",
    "MPG",
    "USABLE_RANGE_MILES",
]
