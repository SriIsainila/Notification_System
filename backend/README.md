# Nilify backend foundation

FastAPI backend for the Nilify React frontend. It uses PostgreSQL, async SQLAlchemy,
Alembic, JWT bearer authentication, bcrypt password hashing, and CORS.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `DATABASE_URL` and `JWT_SECRET` in `.env`, then verify Alembic configuration:

```bash
alembic current
```

Run the application:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 5000
```

The API documentation is available at `http://localhost:5000/docs`.

## Authentication endpoints

- `POST /api/auth/register` — create an account
- `POST /api/auth/login` — set an HttpOnly authentication cookie and return `{ user }`
- `POST /api/auth/token` — receive `{ token, user }` for non-browser bearer clients
- `GET /api/auth/me` — validate a bearer token and return the current user

## Product tracking endpoints

All product routes require a bearer token and are restricted to the current user's data.

- `POST /api/products` — add and enable a URL
- `GET /api/products` — list tracked URLs
- `GET /api/products/{item_id}` — retrieve one tracked URL
- `PATCH /api/products/{item_id}` — update URL or tracking settings
- `DELETE /api/products/{item_id}` — delete a tracked URL
- `POST /api/products/{item_id}/enable` — enable tracking
- `POST /api/products/{item_id}/disable` — pause tracking

## Scraping service

`app.services.scraper.scrape_product()` securely downloads and extracts product title,
price, currency, image, stock status, variants, and a deterministic SHA-256 content
hash. It uses JSON-LD first and falls back to Open Graph, microdata, and visible HTML.
The service validates redirect targets, rejects private/local URLs, limits response size,
and reports timeouts, blocked websites, empty bodies, and non-HTML responses consistently.

## Tracking scheduler

APScheduler runs `tracked-url-check` every minute while enabled. The worker selects
active items, limits scrape concurrency, isolates failures between URLs, stores baseline
and price history, detects title/price/image/stock/variant changes, and creates pending
notifications. Snapshot hashes, atomic transactions, row locks, an advisory leader lock,
and a unique change/channel constraint prevent duplicate notifications. Failed checks record
their last error without stopping the remaining URLs and are retried in the next cycle.

Set `TRACKER_INTERVAL_MINUTES` in `.env` to control the interval. Use `1` for testing
or `1440` to run the tracker once per day, then restart the backend.

## Notification endpoints

All notification routes require a bearer token and are scoped to the current user.

- `GET /api/notifications` — list notifications with `unread`, `limit`, and `offset`
- `GET /api/notifications/unread` — list only unread notifications
- `PATCH /api/notifications/{notification_id}/read` — mark one as read
- `PATCH /api/notifications/read-all` — mark every unread notification as read
- `DELETE /api/notifications/{notification_id}` — delete one notification

Run the authentication tests with:

```bash
pytest -q
```

## Structure

- `app/core` — environment configuration, JWT, bcrypt, and exceptions
- `app/models` — SQLAlchemy models and declarative base
- `app/schemas` — Pydantic API contracts
- `app/routes` — FastAPI routers
- `app/services` — business logic
- `app/utils` — reusable helpers
- `alembic` — schema migrations
