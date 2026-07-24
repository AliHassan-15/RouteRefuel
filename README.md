# RouteRefuel

**USA route planner that recommends cost-optimal fuel stops** from a truck-stop price dataset.

Given free-text **start** and **finish** locations in the United States, RouteRefuel returns:

- the **driving route** (polyline geometry for a map)
- **ordered fuel stops** chosen for **lowest reachable $/gal** within a **500-mile** tank
- **total fuel cost** at **10 MPG**, with an auditable per-stop breakdown

Built by **Ali Hassan** ([hassanakramali@gmail.com](mailto:hassanakramali@gmail.com)) as a Backend Django Engineer assessment — **API-first**, with an optional React + Leaflet UI for demos.

**Repository:** [github.com/AliHassan-15/RouteRefuel](https://github.com/AliHassan-15/RouteRefuel)

---

## Quick links

| Resource | URL |
|---|---|
| Plan a route (API) | `POST /api/v1/route/` |
| Health | `GET /api/v1/health/` |
| OpenAPI / Swagger | [/api/docs/](http://127.0.0.1:8000/api/docs/) |
| Contract | [`API_CONTRACT.md`](API_CONTRACT.md) |
| Frontend (local) | http://127.0.0.1:5173 |

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| API | **Django 5.2** + Django REST Framework | Latest LTS-class Django 5.x, clear project layout |
| Docs | drf-spectacular | Swagger UI out of the box |
| Geocoding | **Nominatim** (OpenStreetMap) | Free, no API key |
| Routing | **OSRM** public demo | Free, one call returns full geometry + duration |
| Prices | Assessment CSV (`Data/fuel-prices-for-be-assessment.csv`) | Loaded once into SQLite |
| UI (optional) | React 19 + Vite + Leaflet + Tailwind | Map demo for reviewers |

Vehicle constants (named, not magic numbers):

```python
MAX_RANGE_MILES = 500
MPG = 10
```

---

## How it works (high level)

```text
Client  →  POST /api/v1/route/  { start, finish }
              │
              ├─ Geocode start/finish (Nominatim, cached)     0–2 calls
              ├─ Drive route (OSRM, cached)                   0–1 call
              ├─ Load corridor stations from DB               0 calls
              ├─ Pick cheapest reachable stop each tank window
              └─ Return geometry + stops + totals + meta.external_calls
```

**Cold request budget:** ≤ **3** external HTTP calls (2 geocode + 1 route).  
**Warm / cached:** often **0**.  
**Per-station network calls:** always **0** (coordinates attached at ingest).

---

## Setup

### Prerequisites

- Python **3.12+**
- Node.js **20+** (only if you run the frontend)
- Internet for first Nominatim / OSRM requests

### 1. Clone and configure

```bash
git clone https://github.com/AliHassan-15/RouteRefuel.git
cd RouteRefuel
cp .env.example .env
```

Edit `.env`:

- `DJANGO_SECRET_KEY` — any long random string
- `NOMINATIM_USER_AGENT` — identify yourself (e.g. your email), per Nominatim usage policy

### 2. Backend

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py load_fuel_stations
python manage.py runserver
```

`load_fuel_stations` parses the CSV, filters non-USA rows, dedupes OPIS IDs, and attaches coordinates via an offline US cities index. Expect ~**6,600** active USA stations.

### 3. Frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — Vite proxies `/api` to the Django server.

### 4. Tests

```bash
pytest
```

---

## API usage

### Postman / curl

**POST** `http://127.0.0.1:8000/api/v1/route/`

Headers: `Content-Type: application/json`

```json
{
  "start": "Chicago, IL",
  "finish": "Dallas, TX"
}
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/route/ \
  -H "Content-Type: application/json" \
  -d '{"start":"Chicago, IL","finish":"Dallas, TX"}'
```

### Success response (shape)

- `route_summary` — distance, duration, resolved places, destination ETA  
- `route_geometry` / `coordinates` — driving polyline for the map  
- `fuel_stops` — sequence, name, city/state, price, gallons, cost, remaining range, ETA  
- `trip_summary` — total gallons, total fuel $, average $/gal, stop count  
- `vehicle` — `max_range_miles`, `mpg`  
- `meta.external_calls` — exact network call counts for the request  

Full field list: [`API_CONTRACT.md`](API_CONTRACT.md).

### Verified scenarios

| Scenario | Expected |
|---|---|
| Chicago → Milwaukee (~89 mi) | **0** stops, **$0** purchased (fits one tank) |
| Chicago → Dallas | Multi-stop plan; Σ stop costs ≈ trip total |
| Los Angeles → New York | Long corridor; gaps ≤ 500 mi |
| Invalid place | `400` with typed `error.code` (e.g. `GEOCODE_FAILED`) |
| Same request again (warm) | `meta.external_calls.total` often **0** |

Server logs:

```text
EXTERNAL_CALLS total=3 geocode=2 routing=1 ...
```

---

## Design decisions

### Why Nominatim + OSRM?

Both are **free**, need **no paid billing**, and match OpenStreetMap tiles in the UI. One OSRM call returns the full drive path. Alternatives like OpenRouteService work too but usually need a signup token — this project stays “clone and run.”

### Why cost-first stops (not nearest)?

“Optimal” in the brief means **cost-effective**. Nearest pumps on interstates are often expensive. Algorithm:

1. Snap pre-geocoded stations to a route corridor (local geometry — no API).
2. While remaining range cannot finish the trip, in the reachable window pick the **lowest $/gal**.
3. Fill to full at that stop; repeat.

Deterministic and fast. It is a **greedy feasible** plan under the 500 mi / 10 MPG constraints — not a global dynamic-programming optimum. With more time: discretized DP or two-tank look-ahead, plus exact exit-level station geocoding.

### Cost math

- `total_gallons_used = route_miles / MPG`
- Per stop: `gallons × price_per_gallon = cost_usd`
- Currency rounded to **2 decimals only at the response/display layer**

Short trips that fit in one tank return **0 stops** and **$0** purchased (assumes departing with a full tank; no on-route purchase required).

---

## Project layout

```text
config/                 Django settings, URLs, OpenAPI
fuel/
  constants.py          MAX_RANGE_MILES, MPG, corridor
  models.py             FuelStation, geocode/route caches
  management/commands/load_fuel_stations.py
  services/
    ingestion.py        CSV parse + dedupe
    city_geocoder.py    Offline station coordinates
    geocoding.py        Nominatim + cache
    routing.py          OSRM + cache
    geo.py              Corridor / snap helpers
    optimizer.py        Cost-optimal stop selection
    planner.py          Orchestration + EXTERNAL_CALLS logging
frontend/               React + Leaflet demo UI
Data/fuel-prices-for-be-assessment.csv
tests/
API_CONTRACT.md
```

---

## Loom demo outline (≤ 5 minutes)

1. **Setup** — show GitHub README, `pytest` green, `runserver`  
2. **Postman** — Chicago → Dallas; highlight stops, totals, `meta.external_calls`; repeat for cache hit  
3. **Edge cases** — short trip (0 stops); invalid location error shape  
4. **Code** — `optimizer.py`, `planner.py`, `load_fuel_stations`  
5. **Close** — Swagger `/api/docs/`, thank the reviewer  

*(Add your Loom link here after recording.)*

---

## Author

**Ali Hassan**  
Email: [hassanakramali@gmail.com](mailto:hassanakramali@gmail.com)  
GitHub: [AliHassan-15](https://github.com/AliHassan-15)

---

## License

Assessment / portfolio use. Fuel price data remains subject to the provider’s terms attached to the original CSV.
