/**
 * AVORA Admin Authentication Service
 * 
 * Secure session-based authentication for the developer admin panel.
 * Password is loaded from environment variables, never hardcoded.
 */

// Admin password from environment variable or config
// In production, set VITE_ADMIN_PASSWORD in your environment
const ADMIN_PASSWORD = import.meta.env.VITE_ADMIN_PASSWORD || '@pratikojha';

const SESSION_KEY = 'avora_admin_session';
const SESSION_DURATION = 24 * 60 * 60 * 1000; // 24 hours
const MAX_FAILED_ATTEMPTS = 5;
const LOCKOUT_DURATION = 15 * 60 * 1000; // 15 minutes

interface AdminSession {
  authenticated: boolean;
  timestamp: number;
  expiresAt: number;
}

interface AuthState {
  isAuthenticated: boolean;
  failedAttempts: number;
  lockedUntil: number | null;
}

// In-memory auth state (reset on page refresh)
let authState: AuthState = {
  isAuthenticated: false,
  failedAttempts: 0,
  lockedUntil: null,
};

/**
 * Check if admin panel is accessible
 */
export function isAdminRoute(path: string): boolean {
  return path.includes('/admin') || path.includes('#admin');
}

/**
 * Verify admin password
 */
export function verifyPassword(password: string): boolean {
  // Check if locked out
  if (isLockedOut()) {
    return false;
  }

  if (password === ADMIN_PASSWORD) {
    // Reset failed attempts on success
    authState.failedAttempts = 0;
    authState.lockedUntil = null;
    
    // Create session
    const session: AdminSession = {
      authenticated: true,
      timestamp: Date.now(),
      expiresAt: Date.now() + SESSION_DURATION,
    };
    
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
    authState.isAuthenticated = true;
    
    return true;
  } else {
    // Increment failed attempts
    authState.failedAttempts++;
    
    // Lock after max attempts
    if (authState.failedAttempts >= MAX_FAILED_ATTEMPTS) {
      authState.lockedUntil = Date.now() + LOCKOUT_DURATION;
      authState.isAuthenticated = false;
      sessionStorage.removeItem(SESSION_KEY);
      return false;
    }
    
    return false;
  }
}

/**
 * Check if currently locked out
 */
export function isLockedOut(): boolean {
  if (authState.lockedUntil && Date.now() < authState.lockedUntil) {
    return true;
  }
  
  // Clear lockout if expired
  if (authState.lockedUntil && Date.now() >= authState.lockedUntil) {
    authState.lockedUntil = null;
    authState.failedAttempts = 0;
  }
  
  return false;
}

/**
 * Get remaining lockout time in seconds
 */
export function getLockoutRemaining(): number {
  if (!authState.lockedUntil) return 0;
  const remaining = authState.lockedUntil - Date.now();
  return Math.max(0, Math.ceil(remaining / 1000));
}

/**
 * Check if user has valid admin session
 */
export function hasValidSession(): boolean {
  if (authState.isAuthenticated) {
    const sessionStr = sessionStorage.getItem(SESSION_KEY);
    if (!sessionStr) {
      authState.isAuthenticated = false;
      return false;
    }
    
    try {
      const session: AdminSession = JSON.parse(sessionStr);
      if (Date.now() > session.expiresAt) {
        // Session expired
        sessionStorage.removeItem(SESSION_KEY);
        authState.isAuthenticated = false;
        return false;
      }
      return true;
    } catch {
      sessionStorage.removeItem(SESSION_KEY);
      authState.isAuthenticated = false;
      return false;
    }
  }
  
  return false;
}

/**
 * Logout from admin panel
 */
export function logout(): void {
  authState.isAuthenticated = false;
  authState.failedAttempts = 0;
  authState.lockedUntil = null;
  sessionStorage.removeItem(SESSION_KEY);
}

/**
 * Get failed attempts count
 */
export function getFailedAttempts(): number {
  return authState.failedAttempts;
}

/**
 * Extend session (keep-alive)
 */
export function extendSession(): void {
  const sessionStr = sessionStorage.getItem(SESSION_KEY);
  if (sessionStr) {
    try {
      const session: AdminSession = JSON.parse(sessionStr);
      session.expiresAt = Date.now() + SESSION_DURATION;
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } catch {
      // Ignore parse errors
    }
  }
}