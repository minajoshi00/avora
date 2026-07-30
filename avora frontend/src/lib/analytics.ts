/**
 * AVORA Analytics Service
 * 
 * Privacy-respecting analytics using Plausible.
 * All tracking is optional and respects user privacy settings.
 * 
 * Features tracked:
 * - Page views & unique visitors
 * - Download button clicks & conversions
 * - Device type, browser, OS
 * - Country (approximate)
 * - Referrer
 */

// Analytics configuration
const PLAUSIBLE_DOMAIN = 'avora.ai'; // Replace with actual domain
const PLAUSIBLE_API = 'https://plausible.io/api/event';

// Privacy settings
let analyticsEnabled = true;
let trackingConsent = false;

/**
 * Initialize analytics with user consent
 */
export function initAnalytics(enabled: boolean, hasConsent: boolean): void {
  analyticsEnabled = enabled;
  trackingConsent = hasConsent;

  if (!analyticsEnabled || !trackingConsent) {
    console.log('[Analytics] Disabled by user preference');
    return;
  }

  // Load Plausible script
  if (typeof window !== 'undefined' && !document.querySelector('script[data-plausible]')) {
    const script = document.createElement('script');
    script.setAttribute('data-plausible', '');
    script.setAttribute('defer', '');
    script.setAttribute('data-api', PLAUSIBLE_API);
    script.src = `https://plausible.io/js/script.js`;
    script.setAttribute('data-domain', PLAUSIBLE_DOMAIN);
    document.head.appendChild(script);
    
    console.log('[Analytics] Initialized with Plausible');
  }
}

/**
 * Track a custom event
 */
export function trackEvent(
  eventName: string,
  properties?: Record<string, string | number | boolean>
): void {
  if (!analyticsEnabled || !trackingConsent) return;

  try {
    if (typeof window !== 'undefined' && (window as any).plausible) {
      (window as any).plausible(eventName, { props: properties });
    }
  } catch (error) {
    console.error('[Analytics] Event tracking failed:', error);
  }
}

/**
 * Track download event with metadata
 */
export function trackDownload(
  version: string,
  platform: string,
  source: string = 'download_center'
): void {
  trackEvent('Download', {
    version,
    platform,
    source,
    timestamp: new Date().toISOString(),
  });
}

/**
 * Track page view
 */
export function trackPageView(path: string): void {
  trackEvent('PageView', {
    path,
    title: document.title,
  });
}

/**
 * Update analytics settings
 */
export function updateAnalyticsSettings(enabled: boolean, hasConsent: boolean): void {
  analyticsEnabled = enabled;
  trackingConsent = hasConsent;
  
  if (!enabled || !hasConsent) {
    console.log('[Analytics] Disabled');
  }
}

/**
 * Check if analytics is enabled
 */
export function isAnalyticsEnabled(): boolean {
  return analyticsEnabled && trackingConsent;
}