# RouteRefuel — Implementation Plan

**Status:** Approved via official assignment email + backend-only build brief.  
**Scope for this phase:** Backend API only (no frontend).

---

## Official requirements (restated)

From the hiring email + backend build brief:

1. Django (latest stable) + DRF API accepting free-text USA `start` and `finish`.
2. Return route geometry (map-drawable), distance (miles), duration, ordered cost-optimal fuel stops, total fuel cost, per-stop cost breakdown, remaining range before each stop, ETAs at stops and destination.
3. Vehicle: `MAX_RANGE_MILES = 500`, `MPG = 10` (named constants).
4. Never exceed 500 miles between start→first stop, stop→stop, or last stop→finish.
5. Optimal = lowest `$/gal` among stations reasonably near the route within each reachable window — not merely nearest.
6. Cost math: `total_gallons_used = total_route_miles / MPG`; per-leg gallons × stop price; round currency to 2 dp only at response serialization.
7. CSV is the price source; geocode stations **once** offline via `load_fuel_stations`; request path ≤ 1–3 external calls; never per-station external calls.
8. Filter Canadian provinces; dedupe OPIS IDs (complete name + lowest price); strip whitespace.
9. Cache start/finish geocodes and routes; retries with backoff on transient external failures; clear 4xx/502 errors (no stack traces).
10. Tests: algorithm, ingestion dedupe, API e2e. README with setup + architecture.

---

## Locked design decisions

| Topic | Decision |
|---|---|
| Stack | Django 5.x + DRF + SQLite (default) / Postgres-ready |
| Geocoding | Nominatim (OSM) — free, no key |
| Routing | OSRM public API — free, no key, one call for full route |
| Canada | Exclude on ingest |
| Dedupe | By OPIS ID: longest trimmed name, `min(price)` |
| Optimal stops | Greedy look-ahead within remaining usable range; pick cheapest in route corridor |
| Cost attribution | Each stop prices the outbound leg(s) it fuels (see formulas in README/code) |
| Starting tank | Full at start; range accounting uses fill-to-full at each stop |
| Frontend | **Out of scope this phase** |

---

## API

`POST /api/v1/route/` — body `{ "start": "...", "finish": "...", "depart_at": "..."? }`

---

## Implementation order

1. Scaffold → models → ingest → clients → optimizer → API → tests → README
