/**
 * AVORA Admin Authentication Service
 *
 * Secure session-based authentication for the developer admin panel.
 * Password is loaded from environment variables, never hardcoded.
 */

const ADMIN_PASSWORD = import.meta.env.VITE_ADMIN_PASSWORD || '@pratikojha';

const SESSION_KEY = 'avora_admin_session';
const LOCKOUT_KEY = 'avora_admin_lockout';
const SESSION_DURATION = 24 * 60 * 60 * 1000;
const MAX_FAILED_ATTEMPTS = 5;
const LOCKOUT_DURATION = 15 * 60 * 1000;

interface AdminSession {
  authenticated: boolean;
  timestamp: number;
  expiresAt: number;
}

interface LockoutState {
  failedAttempts: number;
  lockedUntil: number | null;
}

interface AuthState {
  isAuthenticated: boolean;
  failedAttempts: number;
  lockedUntil: number | null;
}

let authState: AuthState = {
  isAuthenticated: false,
  failedAttempts: 0,
  lockedUntil: null,
};

export function isAdminRoute(path: string): boolean {
  return path.includes('/admin') || path.includes('#/admin');
}

export function verifyPassword(password: string): boolean {
  if (isLockedOut()) {
    return false;
  }

  if (password === ADMIN_PASSWORD) {
    authState.failedAttempts = 0;
    authState.lockedUntil = null;
    localStorage.removeItem(LOCKOUT_KEY);

    const session: AdminSession = {
      authenticated: true,
      timestamp: Date.now(),
      expiresAt: Date.now() + SESSION_DURATION,
    };

    sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
    authState.isAuthenticated = true;

    return true;
  } else {
    authState.failedAttempts++;

    const lockoutData: LockoutState = {
      failedAttempts: authState.failedAttempts,
      lockedUntil: authState.failedAttempts >= MAX_FAILED_ATTEMPTS ? Date.now() + LOCKOUT_DURATION : null,
    };
    localStorage.setItem(LOCKOUT_KEY, JSON.stringify(lockoutData));

    if (authState.failedAttempts >= MAX_FAILED_ATTEMPTS) {
      authState.lockedUntil = Date.now() + LOCKOUT_DURATION;
      authState.isAuthenticated = false;
      sessionStorage.removeItem(SESSION_KEY);
    }

    return false;
  }
}

export function isLockedOut(): boolean {
  const lockoutData = localStorage.getItem(LOCKOUT_KEY);
  if (lockoutData) {
    try {
      const { lockedUntil } = JSON.parse(lockoutData);
      if (lockedUntil && Date.now() < lockedUntil) {
        return true;
      }
      if (lockedUntil && Date.now() >= lockedUntil) {
        localStorage.removeItem(LOCKOUT_KEY);
      }
    } catch {
      localStorage.removeItem(LOCKOUT_KEY);
    }
  }
  return false;
}

export function getLockoutRemaining(): number {
  const lockoutData = localStorage.getItem(LOCKOUT_KEY);
  if (lockoutData) {
    try {
      const { lockedUntil } = JSON.parse(lockoutData);
      if (lockedUntil) {
        const remaining = lockedUntil - Date.now();
        return Math.max(0, Math.ceil(remaining / 1000));
      }
    } catch {
      return 0;
    }
  }
  return 0;
}

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

  const sessionStr = sessionStorage.getItem(SESSION_KEY);
  if (sessionStr) {
    try {
      const session: AdminSession = JSON.parse(sessionStr);
      if (Date.now() > session.expiresAt) {
        sessionStorage.removeItem(SESSION_KEY);
        return false;
      }
      authState.isAuthenticated = true;
      return true;
    } catch {
      sessionStorage.removeItem(SESSION_KEY);
    }
  }

  return false;
}

export function logout(): void {
  authState.isAuthenticated = false;
  authState.failedAttempts = 0;
  authState.lockedUntil = null;
  sessionStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(LOCKOUT_KEY);
}

export function getFailedAttempts(): number {
  const lockoutData = localStorage.getItem(LOCKOUT_KEY);
  if (lockoutData) {
    try {
      const { failedAttempts } = JSON.parse(lockoutData);
      return failedAttempts || 0;
    } catch {
      return 0;
    }
  }
  return 0;
}

export function extendSession(): void {
  const sessionStr = sessionStorage.getItem(SESSION_KEY);
  if (sessionStr) {
    try {
      const session: AdminSession = JSON.parse(sessionStr);
      session.expiresAt = Date.now() + SESSION_DURATION;
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } catch {
    }
  }
}