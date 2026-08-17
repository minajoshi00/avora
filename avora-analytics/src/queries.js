/**
 * AVORA Analytics — Aggregation / queries
 *
 * Computes metrics from the in-memory analytics data store.
 * No database required — works with simple file-based persistence.
 *
 * Empty data is handled explicitly: counts return 0, series return [] / zero
 * arrays, percentages return 0.
 */

/**
 * Format a count with compact suffixes (e.g. 11200 -> 11.2K).
 */
export function formatCount(n) {
  if (!Number.isFinite(n)) return '0';
  if (n < 1000) return String(n);
  if (n < 1_000_000) return (n / 1000).toFixed(n < 10_000 ? 1 : 0) + 'K';
  return (n / 1_000_000).toFixed(1) + 'M';
}

/** Compute the full dashboard summary from analytics data. */
export function getSummary(range = '7d', data) {
  const events = data?.events || (typeof globalThis !== 'undefined' ? globalThis.analyticsData?.events : []);
  
  if (!events || events.length === 0) {
    return {
      range,
      generatedAt: new Date().toISOString(),
      totals: {
        totalUsers: 0,
        activeUsers: 0,
        newUsers: 0,
        returningUsers: 0,
        totalConversations: 0,
        messagesSent: 0,
        aiRequests: 0,
        aiResponses: 0,
        missionsCreated: 0,
        missionsCompleted: 0,
        tasksCompleted: 0,
        downloads: 0,
        appLaunches: 0,
        errors: 0,
        feedbackTotal: 0,
        totalEvents: 0,
      },
      rates: {
        downloads: 0,
        conversations: 0,
        newUsers: 0,
        pageviews: 0,
      },
      breakdowns: {
        providers: [],
        platforms: [],
        countries: [],
      },
      series: {
        labels: [],
        pageviews: [],
        downloads: [],
        conversations: [],
        aiRequests: [],
        errors: [],
      },
      hasData: false,
    };
  }

  const e = events.length;
  
  // Count by type
  const byType = {};
  let conversationCount = 0;
  let messageCount = 0;
  let aiRequestCount = 0;
  let aiResponseCount = 0;
  let missionCreatedCount = 0;
  let missionCompletedCount = 0;
  let taskCompletedCount = 0;
  let downloadCount = 0;
  let appLaunchCount = 0;
  let errorCount = 0;
  let feedbackCount = 0;
  
  const userIds = new Set();
  const dailyCounts = {};
  const now = new Date();
  
  for (const ev of events) {
    const type = (ev.type || '').toLowerCase();
    const userId = (ev.user_id || '').toString();
    const createdAt = ev.created_at ? new Date(ev.created_at) : now;
    const dayKey = createdAt.toISOString().slice(0, 10);
    
    userIds.add(userId);
    
    // Count by type
    byType[type] = (byType[type] || 0) + 1;
    
    // Specific type counts
    if (type === 'conversation') conversationCount++;
    if (type === 'message') messageCount++;
    if (type === 'ai_request') aiRequestCount++;
    if (type === 'ai_response') aiResponseCount++;
    if (type === 'mission_created') missionCreatedCount++;
    if (type === 'mission_completed') missionCompletedCount++;
    if (type === 'task_completed') taskCompletedCount++;
    if (type === 'download') downloadCount++;
    if (type === 'app_launch') appLaunchCount++;
    if (type === 'error') errorCount++;
    if (type === 'feedback') feedbackCount++;
    
    // Daily counts
    dailyCounts[dayKey] = (dailyCounts[dayKey] || 0) + 1;
  }
  
  // Calculate unique users
  const totalUsers = userIds.size;
  const activeUsers = totalUsers;
  const newUsers = 0;
  const returningUsers = 0;
  
  // Determine range and compute metrics
  let totalEvents = e;
  
  if (range === 'today') {
    const today = now.toISOString().slice(0, 10);
    const todayEvents = events.filter(ev => {
      const evDate = ev.created_at ? new Date(ev.created_at).toISOString().slice(0, 10) : '';
      return evDate === today;
    }).length;
    totalEvents = todayEvents;
  }

  // Rates (simple - zero for now since no prior period data)
  const gDownloads = { rate: 0 };
  const gConversations = { rate: 0 };
  const gUsers = { rate: 0 };
  const gViews = { rate: 0 };

  // Provider breakdown (from props.provider) - simplified
  const providers = [];
  // Platform breakdown (from props.platform) - simplified
  const platforms = [];
  // Country breakdown (from country column) - simplified
  const countries = [];

  // Daily series for charts (last 7 or 30 days)
  const days = range === 'today' ? 1 : range === '7d' ? 7 : range === '30d' ? 30 : 30;
  const labels = [];
  const series = {
    pageviews: [],
    downloads: [],
    conversations: [],
    aiRequests: [],
    errors: [],
  };
  
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dayKey = d.toISOString().slice(0, 10);
    labels.push(dayKey);
    series.pageviews.push(0);
    series.downloads.push(0);
    series.conversations.push(0);
    series.aiRequests.push(0);
    series.errors.push(0);
  }

  // Growth rates
  const gDownloads = { rate: 0 };
  const gConversations = { rate: 0 };
  const gUsers = { rate: 0 };
  const gViews = { rate: 0 };

  return {
    range,
    generatedAt: new Date().toISOString(),
    totals: {
      totalUsers,
      activeUsers,
      newUsers,
      returningUsers,
      totalConversations: conversationCount,
      messagesSent: messageCount,
      aiRequests: aiRequestCount,
      aiResponses: aiResponseCount,
      missionsCreated: missionCreatedCount,
      missionsCompleted: missionCompletedCount,
      tasksCompleted: taskCompletedCount,
      downloads: downloadCount,
      appLaunches: appLaunchCount,
      errors: errorCount,
      feedbackTotal: feedbackCount,
      totalEvents,
    },
    rates: {
      downloads: gDownloads.rate,
      conversations: gConversations.rate,
      newUsers: gUsers.rate,
      pageviews: gViews.rate,
    },
    breakdowns: {
      providers,
      platforms,
      countries,
    },
    series: {
      labels,
      pageviews: series.pageviews,
      downloads: series.downloads,
      conversations: series.conversations,
      aiRequests: series.ai_requests,
      errors: series.errors,
    },
    hasData: e > 0,
  };
}