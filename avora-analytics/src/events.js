/**
 * AVORA Analytics — Event ingestion
 *
 * Inserts a single event with idempotency (duplicate event_key is ignored,
 * so the same client-side event is never counted twice).
 */

import { db } from './db.js';

const INSERT = db.prepare(`
  INSERT OR IGNORE INTO events
    (event_key, type, user_id, visitor_id, value, props, ip, country, created_at)
  VALUES
    (@event_key, @type, @user_id, @visitor_id, @value, @props, @ip, @country, @created_at)
`);

/**
 * Track one event. Returns { inserted: boolean }.
 * `inserted` is false when the event_key already existed (duplicate ignored).
 */
export function trackEvent({ event_key, type, user_id, visitor_id, value, props, ip, country, created_at }) {
  const payload = {
    event_key: event_key || null,
    type: String(type || 'unknown').slice(0, 64),
    user_id: user_id || null,
    visitor_id: visitor_id || null,
    value: Number.isFinite(value) ? value : 0,
    props: typeof props === 'string' ? props : JSON.stringify(props || {}),
    ip: ip ? String(ip).slice(0, 45) : null,
    country: country ? String(country).slice(0, 64) : null,
    created_at: created_at || new Date().toISOString(),
  };

  const info = INSERT.run(payload);
  return { inserted: info.changes > 0 };
}

export { db };
