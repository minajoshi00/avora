/**
 * AVORA Storage Service
 * 
 * Manages localStorage for privacy-respecting client-side storage.
 * Handles settings, feedback, and other persistent data.
 */

const STORAGE_KEYS = {
  // Privacy & Analytics
  analyticsEnabled: 'avora_analytics_enabled',
  analyticsConsent: 'avora_analytics_consent',
  
  // First Run
  firstRunComplete: 'avora_first_run_complete',
  firstRunDate: 'avora_first_run_date',
  
  // Feedback
  feedbackPrompted: 'avora_feedback_prompted',
  feedbackDismissed: 'avora_feedback_dismissed',
  feedbackRating: 'avora_feedback_rating',
  feedbackComments: 'avora_feedback_comments',
  feedbackType: 'avora_feedback_type',
  
  // Bug Reports
  bugReports: 'avora_bug_reports',
  
  // Feature Requests
  featureRequests: 'avora_feature_requests',
  
  // App Info
  lastLaunchDate: 'avora_last_launch_date',
  launchCount: 'avora_launch_count',
  installedVersion: 'avora_installed_version',
  
  // Update Check
  lastUpdateCheck: 'avora_last_update_check',
  updateAvailable: 'avora_update_available',
  updateVersion: 'avora_update_version',
  updateUrl: 'avora_update_url',
};

/**
 * Generic storage helper
 */
function getItem<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch {
    return defaultValue;
  }
}

function setItem<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('[Storage] Failed to save:', key, error);
  }
}

// =============================================================
// ANALYTICS SETTINGS
// =============================================================

export function getAnalyticsEnabled(): boolean {
  return getItem(STORAGE_KEYS.analyticsEnabled, true);
}

export function setAnalyticsEnabled(enabled: boolean): void {
  setItem(STORAGE_KEYS.analyticsEnabled, enabled);
}

export function getAnalyticsConsent(): boolean {
  return getItem(STORAGE_KEYS.analyticsConsent, false);
}

export function setAnalyticsConsent(consent: boolean): void {
  setItem(STORAGE_KEYS.analyticsConsent, consent);
}

// =============================================================
// FIRST RUN
// =============================================================

export function isFirstRunComplete(): boolean {
  return getItem(STORAGE_KEYS.firstRunComplete, false);
}

export function completeFirstRun(): void {
  setItem(STORAGE_KEYS.firstRunComplete, true);
  setItem(STORAGE_KEYS.firstRunDate, new Date().toISOString());
}

// =============================================================
// FEEDBACK
// =============================================================

export function hasFeedbackBeenPrompted(): boolean {
  return getItem(STORAGE_KEYS.feedbackPrompted, false);
}

export function markFeedbackPrompted(): void {
  setItem(STORAGE_KEYS.feedbackPrompted, true);
  setItem(STORAGE_KEYS.feedbackDismissed, false);
}

export function isFeedbackDismissed(): boolean {
  return getItem(STORAGE_KEYS.feedbackDismissed, false);
}

export function dismissFeedback(): void {
  setItem(STORAGE_KEYS.feedbackDismissed, true);
}

export function getFeedbackRating(): number | null {
  return getItem(STORAGE_KEYS.feedbackRating, null);
}

export function saveFeedback(rating: number, comments: string, type: string): void {
  setItem(STORAGE_KEYS.feedbackRating, rating);
  setItem(STORAGE_KEYS.feedbackComments, comments);
  setItem(STORAGE_KEYS.feedbackType, type);
}

// =============================================================
// BUG REPORTS
// =============================================================

export function getBugReports(): any[] {
  return getItem(STORAGE_KEYS.bugReports, []);
}

export function addBugReport(report: {
  appVersion: string;
  os: string;
  errorMessage?: string;
  comments: string;
  timestamp: string;
}): void {
  const reports = getBugReports();
  reports.push(report);
  setItem(STORAGE_KEYS.bugReports, reports);
}

// =============================================================
// FEATURE REQUESTS
// =============================================================

export function getFeatureRequests(): any[] {
  return getItem(STORAGE_KEYS.featureRequests, []);
}

export function addFeatureRequest(request: {
  title: string;
  description: string;
  date: string;
  appVersion: string;
}): void {
  const requests = getFeatureRequests();
  requests.push(request);
  setItem(STORAGE_KEYS.featureRequests, requests);
}

// =============================================================
// APP STATS
// =============================================================

export function getLaunchCount(): number {
  return getItem(STORAGE_KEYS.launchCount, 0);
}

export function incrementLaunchCount(): number {
  const count = getLaunchCount() + 1;
  setItem(STORAGE_KEYS.launchCount, count);
  return count;
}

export function getLastLaunchDate(): string | null {
  return getItem(STORAGE_KEYS.lastLaunchDate, null);
}

export function updateLastLaunchDate(): void {
  setItem(STORAGE_KEYS.lastLaunchDate, new Date().toISOString());
}

export function getInstalledVersion(): string | null {
  return getItem(STORAGE_KEYS.installedVersion, null);
}

export function setInstalledVersion(version: string): void {
  setItem(STORAGE_KEYS.installedVersion, version);
}

// =============================================================
// UPDATE CHECK
// =============================================================

export function getLastUpdateCheck(): string | null {
  return getItem(STORAGE_KEYS.lastUpdateCheck, null);
}

export function setLastUpdateCheck(timestamp: string): void {
  setItem(STORAGE_KEYS.lastUpdateCheck, timestamp);
}

export function getUpdateInfo(): { version: string; url: string } | null {
  const info = getItem<{ version: string; url: string } | null>(
    STORAGE_KEYS.updateAvailable,
    null
  );
  return info;
}

export function setUpdateInfo(version: string, url: string): void {
  setItem(STORAGE_KEYS.updateAvailable, { version, url });
}

export function clearUpdateInfo(): void {
  localStorage.removeItem(STORAGE_KEYS.updateAvailable);
  localStorage.removeItem(STORAGE_KEYS.updateVersion);
  localStorage.removeItem(STORAGE_KEYS.updateUrl);
}