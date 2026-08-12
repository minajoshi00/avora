/**
 * AVORA Analytics — Database layer
 *
 * Real persistent storage using SQLite (better-sqlite3).
 * This is the single source of truth for ALL analytics metrics.
 *
 * Schema:
 *   events            — every tracked action (pageview, download, feedback, etc.)
 *   daily_snapshots   — optional pre-aggregated rollups (not required for correctness)
 *
 * Design notes:
 *  - `event_key` (idempotency) prevents double counting of the same client event.
 *  - `user_id` is an anonymous UUID generated client-side; no PII is stored.
 *  - Real timestamps drive all daily/weekly/monthly aggregates.
 */

import Database from 'better-sqlite3';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdirSync } from 'node:fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = join(__dirname, '..', 'data');
mkdirSync(DATA_DIR, { recursive: true });

const DB_PATH = process.env.AVORA_ANALYTICS_DB || join(DATA_DIR, 'analytics.db');

export const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

db.exec(`
  CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key   TEXT UNIQUE,                         -- idempotency key (dedup)
    type        TEXT NOT NULL,                       -- 'pageview' | 'download' | 'feedback' | ...
    user_id     TEXT,                                -- anonymous
    visitor_id  TEXT,                                -- anonymous session-scoped
    value       REAL DEFAULT 0,                      -- numeric payload (e.g. rating)
    props       TEXT DEFAULT '{}',                   -- JSON metadata (platform, version, ...)
    ip          TEXT,                                -- truncated/optional, never shown in UI
    country     TEXT,                                -- optional, derived server-side only
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))  -- UTC
  );

  CREATE INDEX IF NOT EXISTS idx_events_type       ON events(type);
  CREATE INDEX IF NOT EXISTS idx_events_created    ON events(created_at);
  CREATE INDEX IF NOT EXISTS idx_events_user       ON events(user_id);
  CREATE INDEX IF NOT EXISTS idx_events_visitor    ON events(visitor_id);

  CREATE TABLE IF NOT EXISTS daily_snapshots (
    date        TEXT NOT NULL,                       -- 'YYYY-MM-DD'
    type        TEXT NOT NULL,
    count       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (date, type)
  );

  CREATE TABLE IF NOT EXISTS baseline (
    id                  INTEGER PRIMARY KEY CHECK (id = 1),  -- single row, enforced
    visitors_offset    INTEGER NOT NULL DEFAULT 0,           -- additive historical baseline
    downloads_offset   INTEGER NOT NULL DEFAULT 0,           -- additive historical baseline
    applied_at         TEXT                                            -- UTC timestamp of application
  );
`);

export const EVENT_TABLE = 'events';
export default db;
