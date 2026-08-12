/**
 * AVORA Analytics Server
 *
 * Production analytics API backed by SQLite (or an external DB when configured).
 *
 * Endpoints:
 *   POST /api/events            — track one or many events (idempotent via event_key)
 *   GET  /api/analytics/summary — aggregated dashboard metrics (requires a read token)
 *   GET  /api/health           — liveness probe
 *
 * Security model (ZERO client-side admin secret):
 *   - Event tracking is open (any visitor can send events) but gated by client consent.
 *   - AVORA_ANALYTICS_ADMIN_KEY is the FULL server-only key. It is NEVER read by the
 *     browser and is NEVER bundled into client JavaScript.
 *   - The dashboard (browser) authenticates with AVORA_ANALYTICS_VIEW_KEY, a SEPARATE,
 *     low-privilege read token that is safe to ship. The summary route accepts EITHER
 *     the admin key OR the view key. This guarantees the admin secret is not exposed.
 *
 * Deployment:
 *   - Binds 0.0.0.0 and honours PORT from the platform.
 *   - Never seeds in production. Seeding is dev-only and must be explicitly enabled.
 */

import express from 'express';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync, existsSync } from 'node:fs';
import { db } from './src/db.js';
import { trackEvent } from './src/events.js';
import { getSummary } from './src/queries.js';
import { applyBaseline } from './src/baseline.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Load .env if present (works even without --env-file flag).
try {
  const envPath = join(__dirname, '.env');
  if (existsSync(envPath)) {
    for (const line of readFileSync(envPath, 'utf8').split('\n')) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
      if (m && !(m[1] in process.env)) process.env[m[1]] = m[2];
    }
  }
} catch { /* ignore */ }

const PORT = Number(process.env.PORT || process.env.AVORA_ANALYTICS_PORT || 8787);
const HOST = process.env.AVORA_ANALYTICS_HOST || '0.0.0.0';

// Server-only full key — never exposed to the client.
const ADMIN_KEY = process.env.AVORA_ANALYTICS_ADMIN_KEY || '';
// Low-privilege read token — safe to ship to the browser as VITE_ANALYTICS_VIEW_KEY.
const VIEW_KEY = process.env.AVORA_ANALYTICS_VIEW_KEY || '';

const app = express();
app.use(express.json({ limit: '64kb' }));

// ---- helpers -------------------------------------------------------------

function getClientIp(req) {
  const fwd = req.headers['x-forwarded-for'];
  if (typeof fwd === 'string' && fwd.length) return fwd.split(',')[0].trim();
  return req.socket?.remoteAddress || null;
}

/** Validate and normalize a single incoming event payload. */
function normalizeEvent(raw, req) {
  const type = String(raw?.type || '').trim().toLowerCase();
  if (!type || !/^[a-z0-9_]{1,64}$/.test(type)) return null;

  return {
    event_key: raw?.event_key ? String(raw.event_key).slice(0, 128) : null,
    type,
    user_id: raw?.user_id ? String(raw.user_id).slice(0, 64) : null,
    visitor_id: raw?.visitor_id ? String(raw.visitor_id).slice(0, 64) : null,
    value: Number.isFinite(Number(raw?.value)) ? Number(raw.value) : 0,
    props: typeof raw?.props === 'object' && raw.props !== null ? raw.props : {},
    ip: getClientIp(req),
    country: null, // never trust client; server-side geo is the source if enabled
    created_at: raw?.created_at ? String(raw.created_at).slice(0, 32) : new Date().toISOString(),
  };
}

/**
 * Read access for the dashboard. Accepts the server-only admin key OR the
 * low-privilege view key. The admin key is never sent by the browser, so even
 * if the view key leaks it cannot perform admin actions.
 */
function requireReadAuth(req, res, next) {
  if (!ADMIN_KEY && !VIEW_KEY) {
    res.status(503).json({ error: 'Analytics server not configured (missing read key).' });
    return;
  }
  const header = req.headers['authorization'] || '';
  const provided = header.startsWith('Bearer ') ? header.slice(7) : (req.query.key || '');
  const ok = (ADMIN_KEY && provided === ADMIN_KEY) || (VIEW_KEY && provided === VIEW_KEY);
  if (!ok) {
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }
  next();
}

// ---- routes --------------------------------------------------------------

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, time: new Date().toISOString() });
});

app.post('/api/events', (req, res) => {
  try {
    const body = req.body;
    const list = Array.isArray(body) ? body : (body && body.events ? body.events : [body]);

    if (!Array.isArray(list) || list.length === 0) {
      return res.status(400).json({ error: 'No events provided' });
    }

    const results = [];
    let inserted = 0;
    let duplicates = 0;

    for (const raw of list) {
      const ev = normalizeEvent(raw, req);
      if (!ev) { results.push({ ok: false, reason: 'invalid' }); continue; }
      const r = trackEvent(ev);
      if (r.inserted) inserted++; else duplicates++;
      results.push({ ok: true, inserted: r.inserted });
    }

    res.status(200).json({ ok: true, received: list.length, inserted, duplicates, results });
  } catch (err) {
    console.error('[analytics] event ingest error:', err);
    res.status(500).json({ error: 'Internal error' });
  }
});

app.get('/api/analytics/summary', requireReadAuth, (req, res) => {
  try {
    const range = ['today', '7d', '30d', '90d', 'all'].includes(req.query.range)
      ? String(req.query.range)
      : '7d';
    const summary = getSummary(range);
    res.json(summary);
  } catch (err) {
    console.error('[analytics] summary error:', err);
    res.status(500).json({ error: 'Failed to compute summary' });
  }
});

// 404 handler
app.use((_req, res) => res.status(404).json({ error: 'Not found' }));

// One-time historical baseline migration (idempotent; safe to call every boot).
applyBaseline();

app.listen(PORT, HOST, () => {
  console.log(`[AVORA Analytics] listening on http://${HOST}:${PORT}`);
  if (!ADMIN_KEY) {
    console.warn('[AVORA Analytics] WARNING: AVORA_ANALYTICS_ADMIN_KEY is not set (admin access disabled).');
  }
  if (!VIEW_KEY) {
    console.warn('[AVORA Analytics] WARNING: AVORA_ANALYTICS_VIEW_KEY is not set (dashboard read access disabled).');
  }
  if (process.env.AVORA_ANALYTICS_SEED === 'true') {
    console.warn('[AVORA Analytics] WARNING: seeding is ENABLED — only use this in development.');
  } else {
    console.log('[AVORA Analytics] seeding disabled (production-safe).');
  }
});

export default app;
