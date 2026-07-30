'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { verifyPassword, isLockedOut, getLockoutRemaining, getFailedAttempts } from '../lib/admin';
import { trackEvent } from '../lib/analytics';

/**
 * Admin Login Page
 * 
 * Hidden entry point for developer access.
 * Access via /admin route.
 */
export default function AdminLogin() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [lockedOut, setLockedOut] = useState(false);
  const [lockoutRemaining, setLockoutRemaining] = useState(0);

  useEffect(() => {
    // Check lockout status
    if (isLockedOut()) {
      setLockedOut(true);
      setLockoutRemaining(getLockoutRemaining());
      
      // Update countdown
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
    
    // Simulate slight delay for security
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const success = verifyPassword(password);
    
    if (success) {
      trackEvent('admin_login', { success: true });
      // Redirect to dashboard
      window.location.href = '/admin/dashboard';
    } else {
      const attempts = getFailedAttempts();
      setError(`Invalid password. ${5 - attempts} attempts remaining.`);
      trackEvent('admin_login', { success: false, attempts });
      setIsLoading(false);
      
      // Check if now locked out
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
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/[0.08] mb-4">
            <span className="text-3xl">🔒</span>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Developer Console</h1>
          <p className="text-sm text-gray-400">Enter admin password to continue</p>
        </div>

        {/* Login Form */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Message */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="p-4 rounded-xl bg-red-500/10 border border-red-500/20"
                >
                  <p className="text-sm text-red-300">{error}</p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Lockout Warning */}
            <AnimatePresence>
              {lockedOut && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20"
                >
                  <p className="text-sm text-yellow-300 mb-2">
                    Too many failed attempts. Account locked.
                  </p>
                  <p className="text-xs text-yellow-400">
                    Time remaining: {formatTime(lockoutRemaining)}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Password Input */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter admin password"
                disabled={lockedOut || isLoading}
                className="w-full px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.08] text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                autoFocus
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={lockedOut || isLoading || !password}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white font-medium hover:from-blue-600 hover:to-purple-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isLoading ? 'Authenticating...' : 'Access Console'}
            </button>

            {/* Info */}
            <p className="text-xs text-gray-500 text-center">
              Authorized personnel only. All access is logged.
            </p>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-600 mt-6">
          AVORA Developer Console v1.0
        </p>
      </motion.div>
    </div>
  );
}