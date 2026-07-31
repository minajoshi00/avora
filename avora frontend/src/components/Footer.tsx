'use client';

import { useState, useEffect, useCallback } from 'react';
import { hasValidSession, verifyPassword, isLockedOut, getLockoutRemaining, getFailedAttempts } from '../lib/admin';

export function Footer() {
  const [showLogin, setShowLogin] = useState(false);

  useEffect(() => {
    const handlePopState = () => {
      if (window.location.hash === '#/admin') {
        if (!hasValidSession()) {
          window.location.hash = '';
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      }
    };

    window.addEventListener('popstate', handlePopState);
    window.addEventListener('hashchange', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
      window.removeEventListener('hashchange', handlePopState);
    };
  }, []);

  const handleDeveloperClick = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    if (hasValidSession()) {
      window.location.hash = '#/admin/overview';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      setShowLogin(true);
    }
  }, []);

  const handleLoginSuccess = useCallback(() => {
    setShowLogin(false);
    window.location.hash = '#/admin/overview';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  return (
    <>
      <footer className="relative border-t border-white/[0.06] py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <span
              onClick={handleDeveloperClick}
              className="text-xl font-bold text-white cursor-pointer hover:text-blue-300 transition-all duration-300 relative group inline-block"
            >
              Pratik Ojha
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500 group-hover:w-full transition-all duration-300" />
            </span>
            <p className="text-xs leading-relaxed text-gray-500 max-w-md">
              Built with passion by Pratik Ojha. Independent AI project built with passion in Nepal.
            </p>
            <p className="text-[11px] text-gray-600">
              © {new Date().getFullYear()} AVORA. Independent project. Not a company.
            </p>
            <button
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
              className="text-gray-500 hover:text-white transition-colors text-sm"
            >
              Back to Top ↑
            </button>
          </div>
        </div>
      </footer>

      {showLogin && <LoginOverlay onClose={() => setShowLogin(false)} onSuccess={handleLoginSuccess} />}
    </>
  );
}

interface LoginOverlayProps {
  onClose: () => void;
  onSuccess: () => void;
}

function LoginOverlay({ onClose, onSuccess }: LoginOverlayProps) {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [lockedOut, setLockedOut] = useState(false);
  const [lockoutRemaining, setLockoutRemaining] = useState(0);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  useEffect(() => {
    if (isLockedOut()) {
      setLockedOut(true);
      setLockoutRemaining(getLockoutRemaining());
      const interval = setInterval(() => {
        const remaining = getLockoutRemaining();
        setLockoutRemaining(remaining);
        if (remaining <= 0) {
          setLockedOut(false);
          clearInterval(interval);
        }
      }, 1000);
      return () => clearInterval(interval);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (lockedOut) {
      setError(`Too many failed attempts. Please wait ${lockoutRemaining} seconds.`);
      return;
    }
    setIsLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    const success = verifyPassword(password);
    if (success) {
      onSuccess();
    } else {
      const attempts = getFailedAttempts();
      setError(`Invalid password. ${5 - attempts} attempts remaining.`);
      setIsLoading(false);
      if (isLockedOut()) {
        setLockedOut(true);
        setLockoutRemaining(getLockoutRemaining());
      }
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div
      className="fixed inset-0 z-[300] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-sm rounded-2xl border border-white/[0.08] bg-[#0a0a0f] backdrop-blur-xl p-6 shadow-2xl">
        <h2 className="text-lg font-bold text-white mb-4 text-center bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          Developer Login
        </h2>
        <p className="text-xs text-gray-500 text-center mb-4">Enter your credentials to access the admin panel</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20">
              <p className="text-xs text-red-300">{error}</p>
            </div>
          )}
          {lockedOut && (
            <div className="p-3 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
              <p className="text-xs text-yellow-300">Locked. Time remaining: {formatTime(lockoutRemaining)}</p>
            </div>
          )}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={lockedOut || isLoading}
                autoFocus
                className="w-full px-3 py-2 pr-10 rounded-xl bg-white/[0.03] border border-white/[0.08] text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all disabled:opacity-50"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={lockedOut || isLoading || !password}
              className="flex-1 py-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-sm font-medium hover:from-blue-600 hover:to-purple-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 transition-all"
            >
              {isLoading ? 'Authenticating...' : 'Login'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-white/[0.08] text-sm text-gray-300 hover:bg-white/[0.04] transition-all"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
