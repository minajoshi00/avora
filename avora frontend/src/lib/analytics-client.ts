/**
 * AVORA Analytics Client (frontend)
 *
 * Fetches the REAL aggregated dashboard data from the analytics server.
 * Authentication uses the low-privilege VITE_ANALYTICS_VIEW_KEY (safe to ship).
 * The admin key lives ONLY on the server and is never bundled into client JS.
 *
 * Exposes a typed AnalyticsSummary plus simple loading/error/empty handling
 * helpers used by every admin section.
 */

export const ANALYTICS_API =
  (import.meta.env.VITE_ANALYTICS_API as string | undefined) || '/api';

/**
 * IMPORTANT: This is a LOW-PRIVILEGE *read/view* token, NOT the admin key.
 * The admin key (AVORA_ANALYTICS_ADMIN_KEY) lives ONLY on the server and is
 * never bundled into client JavaScript. The view key simply gates read access
 * to aggregated, non-sensitive analytics. It is safe to ship to the browser.
 */
const VIEW_KEY = (import.meta.env.VITE_ANALYTICS_VIEW_KEY as string | undefined) || '';

export type Range = 'today' | '7d' | '30d' | '90d' | 'all';

export interface AnalyticsSummary {
  range: Range;
  generatedAt: string;
  hasData: boolean;
  totals: {
    totalUsers: number;
    activeUsers: number;
    newUsers: number;
    returningUsers: number;
    totalConversations: number;
    messagesSent: number;
    aiRequests: number;
    aiResponses: number;
    missionsCreated: number;
    missionsCompleted: number;
    tasksCompleted: number;
    downloads: number;
    appLaunches: number;
    errors: number;
    feedbackTotal: number;
    totalEvents: number;
  };
  rates: {
    downloads: number;
    conversations: number;
    newUsers: number;
    pageviews: number;
  };
  breakdowns: {
    providers: { name: string; count: number; percentage: number }[];
    platforms: { name: string; count: number; percentage: number }[];
    countries: { name: string; count: number; percentage: number }[];
  };
  series: {
    labels: string[];
    pageviews: number[];
    downloads: number[];
    conversations: number[];
    aiRequests: number[];
    errors: number[];
  };
}

export type AnalyticsState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: AnalyticsSummary };

/**
 * Fetch the dashboard summary. Throws if the admin key is missing or the
 * server rejects the request — callers should surface this as an error state
 * rather than showing fake numbers.
 */
export async function fetchAnalyticsSummary(
  range: Range = '7d',
  signal?: AbortSignal
): Promise<AnalyticsSummary> {
  const headers: Record<string, string> = {};
  if (VIEW_KEY) headers['Authorization'] = `Bearer ${VIEW_KEY}`;

  const res = await fetch(`${ANALYTICS_API}/analytics/summary?range=${range}`, {
    headers,
    signal,
  });

  if (res.status === 401) {
    throw new Error('Unauthorized: analytics admin key missing or invalid.');
  }
  if (res.status === 503) {
    throw new Error('Analytics server not configured.');
  }
  if (!res.ok) {
    throw new Error(`Analytics request failed (${res.status}).`);
  }
  return (await res.json()) as AnalyticsSummary;
}

/** Format a count with compact suffixes (e.g. 11200 -> 11.2K). */
export function formatCount(n: number): string {
  if (!Number.isFinite(n)) return '0';
  if (n < 1000) return String(n);
  if (n < 1_000_000) return (n / 1000).toFixed(n < 10_000 ? 1 : 0) + 'K';
  return (n / 1_000_000).toFixed(1) + 'M';
}

export function formatRate(rate: number): { text: string; positive: boolean } {
  const positive = rate >= 0;
  return { text: `${positive ? '+' : ''}${rate}%`, positive };
}
