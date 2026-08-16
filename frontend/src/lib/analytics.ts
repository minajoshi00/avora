/**
 * AVORA Analytics Service (frontend)
 *
 * Sends REAL events to the AVORA analytics server. Every event is:
 *   - gated by user consent (no tracking unless the visitor opted in)
 *   - assigned a unique idempotency key so the server never double counts
 *   - sent with an anonymous user_id (never PII)
 *
 * If the analytics server is unreachable, events are silently dropped (best
 * effort). Nothing is faked or stored in the browser as a substitute source.
 */

export const ANALYTICS_API =
  (import.meta.env.VITE_ANALYTICS_API as string | undefined) || '/api';

// Anonymous, stable-per-browser identifier. NOT linked to any real identity.
function getAnonymousId(): string {
  try {
    const KEY = 'avora_anon_id';
    let id = localStorage.getItem(KEY);
    if (!id) {
      id = 'u_' + crypto.randomUUID().slice(0, 24);
      localStorage.setItem(KEY, id);
    }
    return id;
  } catch {
    return 'u_anon';
  }
}

function getVisitorId(): string {
  try {
    let id = sessionStorage.getItem('avora_visitor_id');
    if (!id) {
      id = 'v_' + crypto.randomUUID().slice(0, 20);
      sessionStorage.setItem('avora_visitor_id', id);
    }
    return id;
  } catch {
    return 'v_anon';
  }
}

let analyticsEnabled = true;
let trackingConsent = false;

export function initAnalytics(enabled: boolean, hasConsent: boolean): void {
  analyticsEnabled = enabled;
  trackingConsent = hasConsent;
}

export function updateAnalyticsSettings(enabled: boolean, hasConsent: boolean): void {
  analyticsEnabled = enabled;
  trackingConsent = hasConsent;
}

export function isAnalyticsEnabled(): boolean {
  return analyticsEnabled && trackingConsent;
}

interface TrackOptions {
  user_id?: string;
  visitor_id?: string;
  value?: number;
  props?: Record<string, unknown>;
  created_at?: string;
  /** Optional explicit idempotency key. If omitted, one is generated. */
  event_key?: string;
  /** Free-form properties, e.g. { success: true, action: 'clicked' }. */
  [key: string]: unknown;
}

/**
 * Track a real event. Returns a promise resolving to whether it was accepted.
 * Resolves to { sent: false } when disabled or no consent — never throws.
 *
 * Accepts either a structured options object or a flat props bag
 * (e.g. trackEvent('admin_login', { success: true })).
 */
export async function trackEvent(
  type: string,
  options: TrackOptions = {}
): Promise<{ sent: boolean; inserted?: boolean }> {
  if (!analyticsEnabled || !trackingConsent) {
    return { sent: false };
  }

  const known = new Set(['user_id', 'visitor_id', 'value', 'props', 'created_at', 'event_key']);
  const extraProps: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(options)) {
    if (!known.has(k)) extraProps[k] = v;
  }

  const payload = {
    type,
    user_id: options.user_id || getAnonymousId(),
    visitor_id: options.visitor_id || getVisitorId(),
    value: options.value ?? 0,
    props: { ...(options.props || {}), ...extraProps },
    created_at: options.created_at,
    event_key:
      options.event_key ||
      `${type}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`,
  };

  try {
    const res = await fetch(`${ANALYTICS_API}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      keepalive: true,
    });
    if (!res.ok) return { sent: false };
    const data = (await res.json()) as { inserted?: number };
    return { sent: true, inserted: (data.inserted ?? 0) > 0 };
  } catch {
    return { sent: false };
  }
}

export function trackPageView(path: string): void {
  void trackEvent('pageview', { props: { path, title: document.title } }).catch(() => {});
}

export function trackDownload(version: string, platform: string, source = 'download_center'): void {
  void trackEvent('download', { props: { version, platform, source } }).catch(() => {});
}

export function trackFeedback(rating: number, type: string, hasComments: boolean): void {
  void trackEvent('feedback', { value: rating, props: { type, hasComments } });
}

export function trackAppLaunch(): void {
  void trackEvent('app_launch', {});
}

export function trackConversation(): void {
  void trackEvent('conversation', {});
}

export function trackMessage(): void {
  void trackEvent('message', {});
}

export function trackAiRequest(provider: string): void {
  void trackEvent('ai_request', { props: { provider } });
}

export function trackAiResponse(): void {
  void trackEvent('ai_response', {});
}

export function trackMission(created: boolean, completed: boolean): void {
  if (created) void trackEvent('mission_created', {});
  if (completed) void trackEvent('mission_completed', {});
}

export function trackTaskCompleted(): void {
  void trackEvent('task_completed', {});
}

export function trackError(kind: string): void {
  void trackEvent('error', { props: { kind } });
}

export function trackNewUser(): void {
  void trackEvent('new_user', {});
}
