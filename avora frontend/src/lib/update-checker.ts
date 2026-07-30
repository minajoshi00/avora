/**
 * AVORA Update Checker
 * 
 * Silently checks for app updates on launch.
 * No forced updates - user always has the final say.
 */

import { getLatestVersion, type Version } from './versions';
import { getLastUpdateCheck, setLastUpdateCheck, getUpdateInfo, setUpdateInfo, clearUpdateInfo } from './storage';

const UPDATE_CHECK_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Check if an update check is due
 */
export function isUpdateCheckDue(): boolean {
  const lastCheck = getLastUpdateCheck();
  if (!lastCheck) return true;

  const checkDate = new Date(lastCheck).getTime();
  const now = Date.now();
  
  return now - checkDate > UPDATE_CHECK_INTERVAL;
}

/**
 * Simulate checking for updates (in production, this would query a server)
 */
export async function checkForUpdates(currentVersion: string): Promise<{
  hasUpdate: boolean;
  latestVersion?: Version;
  updateUrl?: string;
}> {
  try {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500));

    const latest = getLatestVersion();
    
    // Check if there's a newer version
    if (latest.version !== currentVersion && latest.isLatest) {
      // Store update info
      setUpdateInfo(latest.version, latest.platforms[0]?.url || '#');
      setLastUpdateCheck(new Date().toISOString());

      return {
        hasUpdate: true,
        latestVersion: latest,
        updateUrl: latest.platforms[0]?.url,
      };
    }

    // No update available
    clearUpdateInfo();
    setLastUpdateCheck(new Date().toISOString());

    return {
      hasUpdate: false,
    };
  } catch (error) {
    console.error('[UpdateChecker] Failed to check for updates:', error);
    return { hasUpdate: false };
  }
}

/**
 * Get stored update information
 */
export function getStoredUpdateInfo(): { version: string; url: string } | null {
  return getUpdateInfo();
}

/**
 * Clear update information
 */
export function clearUpdate(): void {
  clearUpdateInfo();
}

/**
 * Track update check event
 */
export function trackUpdateCheck(updateAvailable: boolean, version?: string): void {
  // Analytics tracking would go here
  console.log('[UpdateChecker] Update check:', { updateAvailable, version });
}