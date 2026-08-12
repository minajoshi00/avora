# AVORA Analytics — Production Deployment

## Architecture
- **Frontend** (Vercel, static SPA) calls `VITE_ANALYTICS_API` (= `/api` in prod).
- **`/api/*` is rewritten** by `avora frontend/vercel.json` to the deployed analytics service.
- **Analytics service** (`avora-analytics/`) is a standalone Node + Express + SQLite service
  with a **persistent disk** (Render/Railway/VPS). It is the single source of truth.

```
Browser ──/api/*──▶ Vercel rewrite ──▶ avora-analytics service ──▶ SQLite (persistent volume)
```

## Secret model (no admin secret in the browser)
- `AVORA_ANALYTICS_ADMIN_KEY` — **server-only**, full key. Never set in the frontend. Never committed.
- `AVORA_ANALYTICS_VIEW_KEY` — **low-privilege read token**, safe to ship. The browser uses it as
  `VITE_ANALYTICS_VIEW_KEY`. The summary endpoint accepts admin OR view key; ingest stays open.
  → A leaked view key cannot grant admin access.

## Environment variables
Frontend (`avora frontend/.env`, git-ignored):
- `VITE_ANALYTICS_API=/api`
- `VITE_ANALYTICS_VIEW_KEY=<matches server AVORA_ANALYTICS_VIEW_KEY>`

Analytics service (`avora-analytics/.env`, git-ignored):
- `AVORA_ANALYTICS_ADMIN_KEY=<strong random>` (server-only)
- `AVORA_ANALYTICS_VIEW_KEY=<matches frontend>`
- `AVORA_ANALYTICS_SEED=false` (NEVER seed production)
- `AVORA_ANALYTICS_DB` (optional absolute persistent path)
- `PORT` (set by platform)

## Deploy steps
1. Deploy `avora-analytics/` to Render/Railway (see `render.yaml`). Set the env vars above.
2. Set the persistent disk mount to `.../avora-analytics/data`.
3. In `avora frontend/vercel.json`, replace `REPLACE_WITH_YOUR_ANALYTICS_SERVICE_URL`
   with your deployed service URL.
4. Set `VITE_ANALYTICS_VIEW_KEY` in the Vercel project env (same value as the service's view key).
5. Deploy the frontend to Vercel.

## Do NOT
- Do NOT set `VITE_ANALYTICS_ADMIN_KEY` anywhere in the frontend.
- Do NOT run `npm run seed` in production.
- Do NOT commit `.env` files (both are git-ignored).

## Verify after deploy
- `GET /api/health` → `{ "ok": true }`
- `POST /api/events` with a real event → `inserted:1`
- `GET /api/analytics/summary` with view key → real data
- Same `event_key` twice → second `inserted:0` (dedup)
- No key / wrong key → `401`
