# Nilify — Frontend

Price/stock tracking website frontend. React + Vite + Tailwind CSS.

## Setup

```bash
npm install
cp .env.example .env
```

Development requests use Vite's same-origin `/api` proxy, which forwards to
`http://127.0.0.1:5000`. Set `VITE_API_BASE_URL` only when a deployed API is
hosted at a different origin.

## Run locally

```bash
npm run dev
```

Opens at http://localhost:5173

## Build for production

```bash
npm run build
```

## Folder guide

- `src/pages/` — route-level screens
- `src/components/` — reusable UI components
- `src/routes/` — route definitions and access guards
- `src/api/` — the configured Axios HTTP client
- `src/services/` — backend operations grouped by domain
- `src/context/` — authentication provider and hook
- `src/utils/` — storage and formatting helpers

## Note on backend

This frontend expects the backend on port `5000` during development, or at the
URL set in `VITE_API_BASE_URL` for a separate production API,
with routes for `/auth/register`, `/auth/login`, `/auth/logout`, `/auth/me`,
`/products`, and `/notifications`. Browser authentication uses an HttpOnly JWT
cookie sent through the shared credentialed Axios client; no token is stored in
browser storage.
