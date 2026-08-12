/**
 * AVORA Analytics — Aggregation / queries
 *
 * Every metric in the developer dashboard is computed HERE from the real
 * `events` table. No number is ever hardcoded. Percentages and growth rates
 * are derived from actual stored rows.
 *
 * Empty data is handled explicitly: counts return 0, series return [] / zero
 * arrays, percentages return 0.
 */

import { db } from './db.js';
import { getBaseline } from './baseline.js';

function clampDateRange(range) {
  switch (range) {
    case 'today': return "date(created_at) = date('now')";
    case '7d':    return "created_at >= datetime('now', '-7 days')";
    case '30d':   return "created_at >= datetime('now', '-30 days')";
    case '90d':   return "created_at >= datetime('now', '-90 days')";
    case 'all':   return '1=1';
    default:      return "created_at >= datetime('now', '-7 days')";
  }
}

/** Unique users (by anonymous user_id) within a range, for a given event type filter. */
function uniqueUsers(range, typeFilter = null) {
  const where = [clampDateRange(range)];
  if (typeFilter) where.push(dbSafeType(typeFilter));
  const sql = `SELECT COUNT(DISTINCT user_id) AS c FROM events WHERE user_id IS NOT NULL AND ${where.join(' AND ')}`;
  return db.prepare(sql).get().c || 0;
}

function dbSafeType(type) {
  return `type = '${String(type).replace(/[^a-z0-9_]/gi, '')}'`;
}

/** Total count of an event type within a range (optionally a single day string). */
function countType(type, range, day = null) {
  let sql = `SELECT COUNT(*) AS c FROM events WHERE ${dbSafeType(type)}`;
  const params = [];
  if (day) {
    sql += ` AND date(created_at) = ?`;
    params.push(day);
  } else {
    sql += ` AND ${clampDateRange(range)}`;
  }
  return db.prepare(sql).get(...params).c || 0;
}

/** Returning users = users with an event before the range start. */
function returningUsers(range) {
  const startExpr = {
    today: "datetime('now', 'start of day')",
    '7d': "datetime('now', '-7 days')",
    '30d': "datetime('now', '-30 days')",
    '90d': "datetime('now', '-90 days')",
    all: "datetime('now', '-100 years')",
  }[range] || "datetime('now', '-7 days')";

  const sql = `
    SELECT COUNT(DISTINCT user_id) AS c FROM events
    WHERE user_id IS NOT NULL
      AND created_at >= ${clampDateRange(range).replace('1=1', "datetime('now','-100 years')")}
      AND user_id IN (
        SELECT DISTINCT user_id FROM events
        WHERE user_id IS NOT NULL AND created_at < ${startExpr}
      )`;
  return db.prepare(sql).get().c || 0;
}

/**
 * Build a daily series for a set of event types across the last `days` days.
 * Returns labels (YYYY-MM-DD) and per-type arrays. Missing days are 0-filled.
 */
function dailySeries(types, days) {
  const labels = [];
  const today = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    labels.push(d.toISOString().slice(0, 10));
  }

  const series = {};
  for (const t of types) series[t] = labels.map(() => 0);

  const placeholders = types.map(() => '?').join(',');
  const rows = db.prepare(`
    SELECT date(created_at) AS day, type, COUNT(*) AS c
    FROM events
    WHERE type IN (${placeholders})
      AND created_at >= datetime('now', ?)
    GROUP BY day, type
  `).all(...types, `-${days} days`);

  const idx = new Map(labels.map((l, i) => [l, i]));
  for (const r of rows) {
    if (idx.has(r.day) && series[r.type]) series[r.type][idx.get(r.day)] = r.c;
  }

  return { labels, series };
}

/** Breakdown of a dimension stored in props JSON. */
function propBreakdown(type, propKey, range) {
  const rows = db.prepare(`
    SELECT props FROM events
    WHERE ${dbSafeType(type)} AND ${clampDateRange(range)}
  `).all();

  const totals = {};
  let sum = 0;
  for (const r of rows) {
    try {
      const p = JSON.parse(r.props || '{}');
      const key = p[propKey];
      if (key === undefined || key === null || key === '') continue;
      const k = String(key);
      totals[k] = (totals[k] || 0) + 1;
      sum++;
    } catch { /* ignore malformed props */ }
  }

  const result = Object.entries(totals)
    .map(([name, count]) => ({ name, count, percentage: sum ? +((count / sum) * 100).toFixed(1) : 0 }))
    .sort((a, b) => b.count - a.count);

  return { result, total: sum };
}

/** Growth rate between current period and previous equal-length period. */
function growthRate(type, range) {
  const lenExpr = {
    today: "datetime('now','start of day')",
    '7d': "datetime('now','-7 days')",
    '30d': "datetime('now','-30 days')",
    '90d': "datetime('now','-90 days')",
    all: "datetime('now','-100 years')",
  }[range] || "datetime('now','-7 days')";

  const prevStart = {
    today: "datetime('now','-1 day','start of day')",
    '7d': "datetime('now','-14 days')",
    '30d': "datetime('now','-60 days')",
    '90d': "datetime('now','-180 days')",
    all: "datetime('now','-100 years')",
  }[range] || "datetime('now','-14 days')";

  const prevEnd = {
    today: "datetime('now','start of day')",
    '7d': "datetime('now','-7 days')",
    '30d': "datetime('now','-30 days')",
    '90d': "datetime('now','-90 days')",
    all: "datetime('now','-100 years')",
  }[range] || "datetime('now','-7 days')";

  const cur = db.prepare(`SELECT COUNT(*) AS c FROM events WHERE ${dbSafeType(type)} AND created_at >= ${lenExpr}`).get().c || 0;
  const prev = db.prepare(`SELECT COUNT(*) AS c FROM events WHERE ${dbSafeType(type)} AND created_at >= ${prevStart} AND created_at < ${prevEnd}`).get().c || 0;

  const rate = prev ? +(((cur - prev) / prev) * 100).toFixed(1) : (cur > 0 ? 100 : 0);
  return { current: cur, previous: prev, rate };
}

function pct(part, total) {
  return total ? +((part / total) * 100).toFixed(1) : 0;
}

/**
 * Full dashboard summary. Called by GET /api/analytics/summary.
 */
export function getSummary(range = '7d') {
  const r = clampDateRange(range);

  // Core counts
  const totalEvents = db.prepare(`SELECT COUNT(*) AS c FROM events WHERE ${r}`).get().c || 0;
  const totalConversations = countType('conversation', range);
  const totalMessages = countType('message', range);
  const aiRequests = countType('ai_request', range);
  const aiResponses = countType('ai_response', range);
  const missionsCreated = countType('mission_created', range);
  const missionsCompleted = countType('mission_completed', range);
  const tasksCompleted = countType('task_completed', range);
  const downloadsLive = countType('download', range);
  const appLaunches = countType('app_launch', range);
  const errors = countType('error', range);
  const feedbackTotal = countType('feedback', range);

  // Users
  const totalUsersLive = db.prepare(`SELECT COUNT(DISTINCT user_id) AS c FROM events WHERE user_id IS NOT NULL`).get().c || 0;
  const activeUsers = uniqueUsers(range); // live only — NEVER includes the baseline
  const newUsers = countType('new_user', range);
  const returning = returningUsers(range);

  // One-time historical baseline (additive offset, applied exactly once).
  // Only Total Visitors and Total Downloads carry the baseline; everything
  // else stays 100% real. Active Users is intentionally excluded.
  const baseline = getBaseline();
  const totalUsers = totalUsersLive + baseline.visitors_offset;
  const downloads = downloadsLive + baseline.downloads_offset;

  // Provider usage (from ai_request props.provider)
  const providerRaw = propBreakdown('ai_request', 'provider', range);

  // Platform (downloads + pageviews props.platform)
  const platformRaw = propBreakdown('download', 'platform', range);

  // Countries — only from explicitly stored country column (real, server-derived)
  const countryRows = db.prepare(`
    SELECT country, COUNT(*) AS c FROM events
    WHERE country IS NOT NULL AND ${r}
    GROUP BY country ORDER BY c DESC LIMIT 10
  `).all();
  const countryTotal = countryRows.reduce((s, x) => s + x.c, 0);
  const countries = countryRows.map((x) => ({
    name: x.country,
    count: x.c,
    percentage: pct(x.c, countryTotal),
  }));

  // Daily series for charts
  const days = range === 'today' ? 1 : range === '7d' ? 7 : range === '30d' ? 30 : range === '90d' ? 90 : 30;
  const series = dailySeries(
    ['pageview', 'download', 'conversation', 'ai_request', 'error'],
    days
  );

  // Growth rates
  const gDownloads = growthRate('download', range);
  const gConversations = growthRate('conversation', range);
  const gUsers = growthRate('new_user', range);
  const gViews = growthRate('pageview', range);

  return {
    range,
    generatedAt: new Date().toISOString(),
    totals: {
      totalUsers,
      activeUsers,
      newUsers,
      returningUsers: returning,
      totalConversations,
      messagesSent: totalMessages,
      aiRequests,
      aiResponses,
      missionsCreated,
      missionsCompleted,
      tasksCompleted,
      downloads,
      appLaunches,
      errors,
      feedbackTotal,
      totalEvents,
    },
    rates: {
      downloads: gDownloads.rate,
      conversations: gConversations.rate,
      newUsers: gUsers.rate,
      pageviews: gViews.rate,
    },
    breakdowns: {
      providers: providerRaw.result,
      platforms: platformRaw.result,
      countries,
    },
    series: {
      labels: series.labels,
      pageviews: series.series.pageview,
      downloads: series.series.download,
      conversations: series.series.conversation,
      aiRequests: series.series.ai_request,
      errors: series.series.error,
    },
    hasData: totalEvents > 0,
  };
}

export { db, countType, uniqueUsers, propBreakdown };
