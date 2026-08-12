/**
 * AVORA Analytics — Historical Baseline Migration
 *
 * Adds a REAL historical baseline on top of the existing live data so the
 * dashboard continues counting from an established starting point:
 *   Total Visitors  -> 400
 *   Total Downloads -> 98
 *
 * Design guarantees (per requirements):
 *   - Never wipes, deletes, or recreates the existing database.
 *   - Never manufactures fake visitor/download EVENTS (no rows inserted into
 *     `events`). The baseline is stored as an ADDITIVE OFFSET only.
 *   - Applied exactly ONCE. Idempotent across restarts/deploys.
 *   - Restarting the server cannot duplicate the baseline.
 *   - All other analytics remain 100% real (derived from `events`).
 *   - Active Users is intentionally NOT affected by the baseline.
 *
 * How the offset is computed (so it lands exactly on target regardless of
 * how many real events already exist):
 *   visitors_offset  = max(0, TARGET_VISITORS  - currentDistinctUsers)
 *   downloads_offset = max(0, TARGET_DOWNLOADS - currentDownloadEvents)
 * The single baseline row (id=1) is inserted with INSERT OR IGNORE, so a
 * second call is a no-op even if the process restarts.
 */

import { db } from './db.js';

const TARGET_VISITORS = Number(process.env.AVORA_BASELINE_VISITORS ?? 400);
const TARGET_DOWNLOADS = Number(process.env.AVORA_BASELINE_DOWNLOADS ?? 98);

function currentDistinctUsers() {
  return db.prepare(`SELECT COUNT(DISTINCT user_id) AS c FROM events WHERE user_id IS NOT NULL`).get().c || 0;
}

function currentDownloads() {
  return db.prepare(`SELECT COUNT(*) AS c FROM events WHERE type = 'download'`).get().c || 0;
}

export function getBaseline() {
  const row = db.prepare(`SELECT visitors_offset, downloads_offset, applied_at FROM baseline WHERE id = 1`).get();
  return row || { visitors_offset: 0, downloads_offset: 0, applied_at: null };
}

/**
 * Apply the baseline once. Safe to call on every startup; only the first call
 * writes a row. Returns the (possibly pre-existing) baseline offsets.
 */
export function applyBaseline() {
  const existing = db.prepare(`SELECT id FROM baseline WHERE id = 1`).get();

  if (existing) {
    // Already applied in a previous run — do nothing (idempotent).
    const b = getBaseline();
    console.log(`[baseline] already applied at ${b.applied_at} (visitors+${b.visitors_offset}, downloads+${b.downloads_offset}). Skipping.`);
    return b;
  }

  const visitorsOffset = Math.max(0, TARGET_VISITORS - currentDistinctUsers());
  const downloadsOffset = Math.max(0, TARGET_DOWNLOADS - currentDownloads());

  db.prepare(`
    INSERT OR IGNORE INTO baseline (id, visitors_offset, downloads_offset, applied_at)
    VALUES (1, @visitors_offset, @downloads_offset, @applied_at)
  `).run({
    visitors_offset: visitorsOffset,
    downloads_offset: downloadsOffset,
    applied_at: new Date().toISOString(),
  });

  const b = getBaseline();
  console.log(`[baseline] applied once — visitors+${b.visitors_offset}, downloads+${b.downloads_offset} (targets ${TARGET_VISITORS}/${TARGET_DOWNLOADS}).`);
  return b;
}

export { TARGET_VISITORS, TARGET_DOWNLOADS };
