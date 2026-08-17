/**
 * AVORA Analytics — Event ingestion
 *
 * Inserts events with simple idempotency (duplicate event_key is ignored,
 * so the same client-side event is never counted twice).
 * Data is persisted to ./data/analytics.json for cross-request consistency.
 */

// Shared analytics state - initialized from server
let analyticsData = { events: [], counters: me };

/**
 * Set the analytics data reference (called from server startup).
 * @param {object} data - The analytics data object with events array
 */
export function setAnalyticsData(data) {
  analyticsData = data;
}

/**
 * Track a single event. Returns { inserted: boolean; duplicate?: boolean }.
 * `inserted` is true when the event was new.
 * `duplicate` is true when the event_key already existed.
 */
export function trackEvent(raw) {
  const { event_key, type, user_id, visitor_id, value, props, ip, country, created_at } = raw;
  
  // Get current event keys for idempotency check
  const existingKeys = new Set(analyticsData.events?.map(e => e.event_key) || []);
  
  // Skip duplicate event_keys
  if (event_key && existingKeys.has(event_key)) {
    return { inserted: false, duplicate: true };
  }
  
  // Generate a unique event key if not provided
  const key = event_key || `${type || 'unknown'}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  
  // Normalize the event
  const normalized = {
    event_key: key,
    type: String(type || 'unknown').slice(0, 64),
    user_id: user_id || 'anon',
    visitor_id: visitor_id || 'session_' + Date.now(),
    value: Number.isFinite(value) ? value : 0,
    props: typeof props === 'string' ? props : JSON.stringify(props || {}),
    ip: ip ? String(ip).slice(0, 45) : null,
    country: country ? String(country).slice(0, 64) : null,
    created_at: created_at || new Date().toISOString(),
  };
  
  // Add to analytics data
  analyticsData.events = analyticsData.events || [];
  analyticsData.events.push(normalized);
  
  return { inserted: true };
}