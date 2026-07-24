# API response contract (frontend-facing)

**Endpoint:** `POST /api/v1/route/`  
**Docs:** `http://127.0.0.1:8000/api/docs/`  
**OpenAPI schema:** `http://127.0.0.1:8000/api/schema/`

This is the locked contract for the React frontend. Field names below are stable.

## Success `200`

```json
{
  "route_summary": {
    "distance_miles": 966.923,
    "duration_seconds": 61575.6,
    "duration_hours": 17.104,
    "destination_eta": "2026-07-25T11:58:49.911434Z",
    "start": {
      "query": "Chicago, IL",
      "address": "Chicago, Cook County, Illinois, United States",
      "latitude": 41.8755616,
      "longitude": -87.6244212
    },
    "finish": {
      "query": "Dallas, TX",
      "address": "Dallas, Dallas County, Texas, United States",
      "latitude": 32.7762719,
      "longitude": -96.7968559
    }
  },
  "route_geometry": {
    "type": "LineString",
    "coordinates": [[-87.62435, 41.87556], [-87.62435, 41.87531]]
  },
  "coordinates": [[41.87556, -87.62435], [41.87531, -87.62435]],
  "fuel_stops": [
    {
      "sequence": 1,
      "station_id": 69861,
      "name": "HUCKS FOOD & FUEL #379",
      "address": "I-57, EXIT 53",
      "city": "Marion",
      "state": "IL",
      "latitude": 37.725662,
      "longitude": -88.929447,
      "price_per_gallon": 2.929,
      "distance_from_start_miles": 317.143,
      "gallons_purchased": 31.714286,
      "cost_usd": 92.89,
      "remaining_range_before_refuel_miles": 182.857,
      "eta": "2026-07-25T00:05:10.612793Z",
      "dwell_minutes": 12
    }
  ],
  "trip_summary": {
    "total_gallons_used": 96.692267,
    "total_fuel_cost_usd": 282.35,
    "average_price_per_gallon_usd": 2.92,
    "stop_count": 2
  },
  "vehicle": {
    "mpg": 10,
    "max_range_miles": 500,
    "tank_capacity_gallons": 50.0,
    "range_reserve_miles": 30,
    "route_corridor_miles": 25.0
  },
  "meta": {
    "response_time_ms": 712.4,
    "external_calls": {
      "geocode": 0,
      "routing": 0,
      "total": 0,
      "geocode_cache_hits": 2,
      "routing_cache_hits": 1,
      "per_station": 0
    },
    "stations_considered": 6614,
    "stations_in_route_bbox": 842,
    "depart_at": "2026-07-24T18:28:34.311434Z",
    "currency_rounding": "USD values rounded to 2 decimals only in this response; internal math uses full-precision Decimals."
  }
}
```

### Geometry notes for the frontend

- `route_geometry` — GeoJSON LineString, coordinates are **`[longitude, latitude]`** (Mapbox / GeoJSON standard).
- `coordinates` — same path as **`[latitude, longitude]`** pairs (Leaflet `L.polyline` friendly). Prefer one; both are always present and aligned.

### Request body

```json
{
  "start": "Chicago, IL",
  "finish": "Dallas, TX",
  "depart_at": "2026-07-24T15:00:00Z"
}
```

`depart_at` is optional.

## Errors (all same envelope)

```json
{
  "error": {
    "code": "GEOCODE_FAILED",
    "message": "Human-readable explanation.",
    "details": {}
  }
}
```

| HTTP | `error.code` | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Missing/invalid body fields |
| 400 | `GEOCODE_FAILED` | Unresolvable place text |
| 400 | `LOCATION_NOT_IN_USA` | Non-USA location |
| 400 | `NO_DRIVING_ROUTE` | OSRM found no path |
| 422 | `NO_FEASIBLE_FUEL_PLAN` | No in-range station on a required leg |
| 429 | `RATE_LIMITED` | Throttle exceeded (default 60/min) |
| 502 | `GEOCODING_UNAVAILABLE` | Nominatim down/timeout |
| 502 | `ROUTING_UNAVAILABLE` | OSRM down/timeout |
| 503 | `STATIONS_NOT_READY` | Ingestion not run |

## CORS

Allowed by default: `localhost:5173`, `127.0.0.1:5173`, `localhost:3000`, `127.0.0.1:3000`.  
Override with `CORS_ALLOWED_ORIGINS` in `.env`.
