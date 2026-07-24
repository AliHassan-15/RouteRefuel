# RouteRefuel UI

React + Vite + TypeScript + Leaflet client for the RouteRefuel Django API.

Author: **Ali Hassan** · [hassanakramali@gmail.com](mailto:hassanakramali@gmail.com)

Full setup and API docs: **[root README](../README.md)**.

## Run

```bash
# Terminal 1 — API (repo root)
python manage.py runserver

# Terminal 2 — UI
cd frontend
cp .env.example .env   # optional
npm install
npm run dev
```

Open http://127.0.0.1:5173

Env vars: see `.env.example` (`VITE_API_BASE_URL`, `VITE_DEV_PROXY_TARGET`).
