"""Pure geospatial helpers (no network I/O)."""

from __future__ import annotations

import math
from typing import Iterable, Sequence

EARTH_RADIUS_MILES = 3958.7613


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points, in miles."""
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def decode_polyline(encoded: str, *, precision: int = 5) -> list[tuple[float, float]]:
    """Decode Google Encoded Polyline into (lat, lon) pairs."""
    coordinates: list[tuple[float, float]] = []
    index = 0
    lat = 0
    lon = 0
    length = len(encoded)
    factor = 10**precision

    while index < length:
        result = 0
        shift = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else (result >> 1)
        lat += dlat

        result = 0
        shift = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlon = ~(result >> 1) if result & 1 else (result >> 1)
        lon += dlon
        coordinates.append((lat / factor, lon / factor))

    return coordinates


def build_route_mile_markers(
    points: Sequence[tuple[float, float]],
    total_distance_miles: float,
) -> list[float]:
    """
    Cumulative miles at each polyline vertex, scaled so the final marker
    equals the routing provider's reported total distance.
    """
    if not points:
        return []
    raw = [0.0]
    for i in range(1, len(points)):
        lat1, lon1 = points[i - 1]
        lat2, lon2 = points[i]
        raw.append(raw[-1] + haversine_miles(lat1, lon1, lat2, lon2))
    raw_total = raw[-1]
    if raw_total <= 0:
        return [0.0 for _ in points]
    scale = total_distance_miles / raw_total
    return [m * scale for m in raw]


def point_to_segment_distance_miles(
    plat: float,
    plon: float,
    a_lat: float,
    a_lon: float,
    b_lat: float,
    b_lon: float,
) -> tuple[float, float]:
    """
    Approximate distance from point P to segment AB on a local equirectangular plane.
    Returns (distance_miles, fraction along AB in [0, 1]).
    """
    # Local projection around A
    lat_mid = math.radians((a_lat + b_lat) / 2.0)
    x_a = 0.0
    y_a = 0.0
    x_b = (b_lon - a_lon) * math.cos(lat_mid) * 69.172
    y_b = (b_lat - a_lat) * 69.172
    x_p = (plon - a_lon) * math.cos(lat_mid) * 69.172
    y_p = (plat - a_lat) * 69.172

    dx = x_b - x_a
    dy = y_b - y_a
    if dx == 0 and dy == 0:
        return math.hypot(x_p - x_a, y_p - y_a), 0.0

    t = ((x_p - x_a) * dx + (y_p - y_a) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_x = x_a + t * dx
    proj_y = y_a + t * dy
    return math.hypot(x_p - proj_x, y_p - proj_y), t


def snap_to_route(
    lat: float,
    lon: float,
    points: Sequence[tuple[float, float]],
    mile_markers: Sequence[float],
) -> tuple[float, float]:
    """
    Snap a point to the nearest location on the route polyline.
    Returns (route_mile_marker, distance_to_route_miles).
    """
    best_dist = float("inf")
    best_mile = 0.0
    for i in range(1, len(points)):
        a_lat, a_lon = points[i - 1]
        b_lat, b_lon = points[i]
        dist, t = point_to_segment_distance_miles(lat, lon, a_lat, a_lon, b_lat, b_lon)
        if dist < best_dist:
            best_dist = dist
            best_mile = mile_markers[i - 1] + t * (mile_markers[i] - mile_markers[i - 1])
    return best_mile, best_dist


def downsample_polyline(
    points: Sequence[tuple[float, float]],
    mile_markers: Sequence[float],
    *,
    max_points: int = 250,
) -> tuple[list[tuple[float, float]], list[float]]:
    """Keep polyline size bounded so station snapping stays O(n) and fast."""
    if len(points) <= max_points:
        return list(points), list(mile_markers)
    step = (len(points) - 1) / (max_points - 1)
    idxs = sorted({int(round(i * step)) for i in range(max_points)})
    idxs[0] = 0
    idxs[-1] = len(points) - 1
    return [points[i] for i in idxs], [mile_markers[i] for i in idxs]


def route_bbox(
    points: Sequence[tuple[float, float]],
    pad_degrees: float,
) -> tuple[float, float, float, float]:
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return (
        min(lats) - pad_degrees,
        max(lats) + pad_degrees,
        min(lons) - pad_degrees,
        max(lons) + pad_degrees,
    )


def stations_near_route(
    stations: Iterable[dict],
    points: Sequence[tuple[float, float]],
    mile_markers: Sequence[float],
    corridor_miles: float,
) -> list[dict]:
    """
    Filter stations to those within `corridor_miles` of the polyline and
    annotate each with route_mile + detour_miles.

    Uses bbox prefilter + downsampled polyline so request latency stays low
    even with ~6k stations and dense OSRM geometries.
    """
    points_ds, miles_ds = downsample_polyline(points, mile_markers, max_points=250)
    # ~69 miles/deg latitude; pad corridor in degrees (generous for lon).
    pad = (corridor_miles / 69.0) + 0.15
    min_lat, max_lat, min_lon, max_lon = route_bbox(points_ds, pad)

    nearby: list[dict] = []
    for station in stations:
        lat = station["latitude"]
        lon = station["longitude"]
        if lat is None or lon is None:
            continue
        if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
            continue
        mile, detour = snap_to_route(lat, lon, points_ds, miles_ds)
        if detour <= corridor_miles:
            annotated = dict(station)
            annotated["route_mile"] = mile
            annotated["detour_miles"] = detour
            nearby.append(annotated)
    nearby.sort(key=lambda s: s["route_mile"])
    return nearby
