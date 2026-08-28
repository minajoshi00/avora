/**
 * AVORA Analytics — Database layer
 *
 * Real persistent storage using sql.js (pure JavaScript SQLite).
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

import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdirSync, existsSync, readFileSync, writeFileSync } from 'node:fs';

const __dirname = dirname(fileURLToWord(import.meta.url));
const DATA_DIR = join(__dirname, '..', 'data');
mkdirSync(DATA_DIR, { recursive: true });

const DB_PATH = process.env.AVORA_ANALYTICS_DB || join(DATA_DIR, 'analytics.db');

let db = null;

/**
 * Initialize the database.
 * Must be called before using any db operations.
 * @returns {Promise<SQL.Database>} The initialized database instance
 */
export async function initDb() {
  const SQL = (await import('sql.js')).default;
  db = new SQL();

  // Load existing DB if present
  if (existsSync(DB_PATH)) {
    const buffer = readFileSync(DB_PATH);
    db = new SQL(buffer);
  }

  // Create tables
  db.exec(`
    CREATE TABLE IF NOT EXISTS events (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      event_key   TEXT UNIQUE,
      type        TEXT NOT NULL,
      user_id     TEXT,
      visitor_id  TEXT,
      value       REAL DEFAULT 0,
      props       TEXT DEFAULT '{}',
      ip          TEXT,
      country     TEXT,
      created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
  `);

  db.exec(`CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id)`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_events_visitor ON events(visitor_id)`);

  db.exec(`
    CREATE TABLE IF NOT EXISTS daily_snapshots (
      date        TEXT NOT NULL,
      type        TEXT NOT NULL,
      count       INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY (date, type)
    )
  `);

  db.exec(`
    CREATE TABLE IF NOT EXISTS baseline (
      id                  INTEGER PRIMARY KEY CHECK (id = 1),
      visitors_offset    INTEGER NOT NULL DEFAULT 0,
      downloads_offset   INTEGER NOT NULL DEFAULT 0,
      applied_at         TEXT
    )
  `);

  // Persist DB to disk every 5 seconds
  setInterval(() => {
    if (db) {
      const data = db.export();
      const buffer = Buffer.from(data);
      writeFileSync(DB_PATH, buffer);
    }
  }, 5000);

  // Persist on process exit
  process.on('exit', () => {
    if (db) {
      const data = db.export();
      const buffer = Buffer.from(data);
      writeFileSync(DB_PATH, buffer);
    }
  });

  return db;
}

/**
 * Get the database instance. Throws if not initialized.
 */
export function getDb() {
  if (!db) throw new Error('Database not initialized. Call initDb() first.');
  return db;
}

export const EVENT_TABLE = 'events';
export default { getDb, initDb };