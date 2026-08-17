/**
 * AVORA Analytics Server
 *
 * Production analytics API using file-based persistence.
 * This provides a working analytics system that can be upgraded to full SQLite
 * when the environment supports native database modules.
 *
 * Endpoints:
 *   POST /api/events            — track one or many events (idempotent via event_key)
 *   GET  /api/analytics/summary — aggregated dashboard metrics
 *   GET  /api/health           — liveness probe
 *
 * Deployment:
 *   - Binds 0.0.0.0 and honours PORT from the platform.
 *   - Data stored in ./data/analytics.json for basic persistence.
 */

import express from 'express';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdirSync, existsSync, readFileSync, writeFileSync } from 'node:url';

import { trackEvent } from './src/events.js';
import { getSummary } from './src/queries.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = join(__dirname, '..', 'data');
const JSON_PATH = join(DATA_DIR, 'analytics.json');

// Ensure data directory exists
if (!existsSync(DATA_DIR)) {
  mkdirSync(DATA_DIR, { recursive: true });
}

// Load existing data or initialize empty
let analyticsData = { events: [], counters: {} };
if (existsSync(JSON_PATH)) {
  try {
    analyticsData = JSON.parse(readFileSync(JSON_PATH, 'utf8'));
  } catch {
    analyticsData = { events: [], counters: {} };
  }
}

/* -------------------------------------------------------------------------- */
/*                            Express Configuration                           */
/* -------------------------------------------------------------------------- */

const app = express();
app.use(express.json({ limit: '64kb' }));

/* -------------------------------------------------------------------------- */
/*                            API Routes                                      */
/* -------------------------------------------------------------------------- */

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, timestamp: new Date().toISOString() });
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

    // Simple idempotency check using event_key
    const existingKeys = new Set(analyticsData.events?.map(e => e.event_key) || []);

    for (const raw of list) {
      const { event_key, type, user_id, visitor_id, value, props, ip, country, created_at } = raw;

      // Skip duplicate event_keys
      if (event_key && existingKeys.has(event_key)) {
        results.push({ ok: true, inserted: false, duplicate: true });
        duplicates++;
        continue;
      }

      // Generate a unique event key if not provided
      const key = event_key || `${type || 'unknown'}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

      // Normalize the event
      const normalized = {
        event_key: key,
        type: String(type || 'unknown').slice(0, 64),
        user_id: user_id || 'anon',
        visitor_id: visitor_id || 'session_' + Date.now(),
        value: Number(value) || 0,
        props: typeof props === 'string' ? props : JSON.stringify(props || {}),
        ip: ip ? String(ip).slice(0, 45) : null,
        country: country ? String(country).slice(0, 64) : null,
        created_at: created_at || new Date().toISOString(),
      };

      // Add to analytics data
      analyticsData.events = analyticsData.events || [];
      analyticsData.events.push(normalized);

      existingKeys.add(normalized.event_key);
      inserted++;

      results.push({ ok: true, inserted: true });
    }

    // Persist to disk
    writeFileSync(JSON_PATH, JSON.stringify(analyticsData));

    res.status(200).json({ ok: true, received: list.length, inserted, duplicates, results });
  } catch (err) {
    console.error('[analytics] event ingest error:', err);
    res.status(500).json({ error: 'Internal error' });
  }
});

app.get('/api/analytics/summary', (req, res) => {
  try {
    const range = ['today', '7d', '30d', '90d', 'all'].includes(req.query.range)
      ? req.query.range
      : '7d';

    const summary = getSummary(range, analyticsData);
    res.json(summary);
  } catch (err) {
    console.error('[analytics] summary error:', err);
    res.status(500).json({ error: 'Failed to compute summary' });
  }
});

/* -------------------------------------------------------------------------- */
/*                            Health Check                                    */
/* -------------------------------------------------------------------------- */

app.get('/api/status', (req, res) => {
  res.json({
    status: 'operational',
    eventsTracked: analyticsData.events?.length || 0,
    dataFile: JSON_PATH,
    timestamp: new Date().toISOString(),
  });
});

/* -------------------------------------------------------------------------- */
/*                            Start Server                                    */
/* -------------------------------------------------------------------------- */

const PORT = process.env.PORT || 8787;
const HOST = '0.0.0.0';

app.listen(PORT, HOST, () => {
  console.log(`[AVORA Analytics] listening on http://${HOST}:${PORT}`);
  console.log(`[AVORA Analytics] Events stored at: ${JSON_PATH}`);
  console.log(`[AVORA Analytics] Events count: ${analyticsData.events?.length || 0}`);
});

export default app;