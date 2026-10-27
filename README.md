# UK Wind Forecast Monitor

A web app that helps a UK energy utility's day-ahead power buying team see the wind generation forecasts available when they must decide, and measure how accurate those forecasts are.

**Live app:** <FRONTEND_URL>
**API:** <BACKEND_URL>/docs

## Problem and approach

Day-ahead purchases are decided the day before delivery, so only forecasts published *before* that point are usable. For each target time the app picks the **latest forecast published at least H hours earlier** (H is the "forecast horizon", selectable 0-48 h, default 24 h) and compares it with actual wind generation.

- Actuals: Elexon `FUELHH`, `fuelType = WIND` (national, half-hourly).
- Forecasts: Elexon `WINDFOR` (`startTime`, `publishTime`, `generation`).
- Scope: January 2026 only. January is GMT, so UK time equals UTC.

### Metrics
Error = forecast - actual (positive = over-forecast). The app reports MAE, RMSE, bias, MAE as a percentage of mean output, and P50/P90/P99/max absolute error, plus error by hour of day and accuracy by forecast horizon. Percentile errors show a buyer how large a safety margin may be needed.

### Assumptions and notes
- `WINDFOR` is hourly and `FUELHH` is half-hourly, so accuracy is evaluated on the hourly timestamps present in both (744 points for January).
- Forecasts published after their target time are never used.
- At a 24 h horizon for all of January 2026: MAE about 2,050 MW (17.7% of mean actual), bias about +1,854 MW (the forecast is higher than actuals on average), P90 absolute error about 4,129 MW.
- The bias is similar at every horizon, so it looks like a persistent offset between the two datasets rather than ordinary forecast decay. The cause has not been verified.

## Repository layout

```
.
├── docker-compose.yml        Runs backend and frontend together
├── backend/
│   ├── app/
│   │   ├── main.py           FastAPI routes
│   │   ├── forecast_logic.py Horizon-based forecast selection
│   │   ├── metrics.py        MAE, RMSE, bias, percentiles, by hour
│   │   └── data_loader.py    Loads the cached CSVs
│   ├── scripts/fetch_data.py Downloads data from the Elexon API
│   ├── data/                 actuals.csv, forecasts.csv (cached January 2026 data)
│   ├── tests/test_logic.py   Unit tests
│   ├── api/index.py          Vercel entry point
│   ├── vercel.json
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/                 React (Vite) + Recharts
    ├── src/App.jsx, api.js
    ├── src/components/       Controls, MetricCards, Charts
    ├── nginx.conf
    └── Dockerfile
```

## Run with Docker

```
docker compose up --build
```
Open http://localhost:8080 (API docs at http://localhost:8000/docs).

## Run without Docker

Backend (Python 3.11+):
```
cd backend
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Frontend:
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (the dev server proxies `/api` to port 8000).

Tests: `cd backend && python -m pytest`

Refresh the data: `cd backend && python scripts/fetch_data.py`

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/meta` | Data range, defaults, row counts |
| `GET /api/actuals` | Actual wind generation |
| `GET /api/forecasts?horizon=` | Horizon-selected forecasts |
| `GET /api/series?horizon=` | Actual vs forecast per timestamp |
| `GET /api/metrics?horizon=` | Accuracy summary and by hour of day |
| `GET /api/metrics/by-horizon` | Accuracy across horizons |

`start` (inclusive) and `end` (exclusive) are optional ISO dates within January 2026.

## Deployment

Two Vercel projects from this repo: the backend (root directory `backend`, FastAPI as a Python function) and the frontend (root directory `frontend`, env var `VITE_API_URL` set to the backend URL).

## AI tools

This project was built with AI assistance (Claude by Anthropic) for planning, code generation and debugging. I reviewed, ran and tested the code.