# ResQ
Its disaster management and releif tool using croud sourcing 
we have to manage this site for government , we had to take the data from the local government officials 
through which we had easily collect the data
we are making it as soon as possible
## it is on hold for some time

# RESQ Backend (FastAPI)

Backend for RESQ: a disaster relief platform where victims submit disaster reports and NGOs manage rescue operations.

## Project Structure

- `main.py` - FastAPI app entrypoint
- `api/` - API routers
- `models/` - SQLModel DB models + DB session
- `schemas/` - Pydantic request/response schemas
- `services/` - validation + clustering service
- `ml_logic/` - placeholder for future ML modules

## Requirements

- Python 3.10+
- PostgreSQL running (or update `DATABASE_URL` accordingly)

## Configuration

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/YOUR_DB
DEBUG=True
LOG_LEVEL=info
CORS_ORIGINS=["*"]
```

## Install

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Server runs at:

- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

## API Endpoints

### Victim reporting

- `POST /reports/submit`
  - Submit a single report.
- `POST /reports/sync`
  - Offline-first batch upload. Accepts a list of reports and clusters them into incidents.

### NGO / Admin

- `GET /admin/dashboard`
  - Returns verified + clustered incidents.
- `GET /admin/incidents/{incident_id}`
  - Incident details by incident id (example: `incident_1`).
- `GET /admin/statistics`
  - Platform statistics.

## Notes

- Location clustering uses K-Means and a 50m proximity heuristic.
- Authenticity validation uses simple text similarity against mock `latest_disaster_news`.
