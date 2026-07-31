'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { verifyPassword, isLockedOut, getLockoutRemaining, getFailedAttempts } from '../../lib/admin';
import { trackEvent } from '../../lib/analytics';
import { Eye, EyeOff } from 'lucide-react';

interface AdminLoginModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function AdminLoginModal({ onClose, onSuccess }: AdminLoginModalProps) {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [lockedOut, setLockedOut] = useState(false);
  const [lockoutRemaining, setLockoutRemaining] = useState(0);

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

  const handleEsc = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  useEffect(() => {
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [handleEsc]);

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
      trackEvent('admin_login', { success: true });
      onSuccess();
    } else {
      const attempts = getFailedAttempts();
      setError(`Invalid password. ${5 - attempts} attempts remaining.`);
      trackEvent('admin_login', { success: false, attempts });
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
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[300] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="w-full max-w-sm rounded-2xl border border-white/[0.08] bg-[#0a0a0f] backdrop-blur-xl p-6 shadow-2xl"
      >
        <h2 className="text-lg font-bold text-white mb-4 text-center bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Developer Login</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <AnimatePresence>
            {error && (
              <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }} className="p-3 rounded-xl bg-red-500/10 border border-red-500/20">
                <p className="text-xs text-red-300">{error}</p>
              </motion.div>
            )}
          </AnimatePresence>
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
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={lockedOut || isLoading || !password} className="flex-1 py-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-sm font-medium hover:from-blue-600 hover:to-purple-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 transition-all">
              {isLoading ? 'Authenticating...' : 'Login'}
            </button>
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl border border-white/[0.08] text-sm text-gray-300 hover:bg-white/[0.04] transition-all">
              Cancel
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}
