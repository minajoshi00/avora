'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { toggleMaintenance, getMaintenanceStatus } from '../../lib/maintenance';
import { trackEvent } from '../../lib/analytics';

const ADMIN_PASSWORD = import.meta.env.VITE_MAINTENANCE_ADMIN_PASSWORD || '';

export function MaintenanceManagementPanel() {
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [confirmMode, setConfirmMode] = useState<'off' | 'on' | null>(null);
  const [pendingToggle, setPendingToggle] = useState<'off' | 'on' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isToggling, setIsToggling] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState('');

  useEffect(() => {
    const checkInitialStatus = async () => {
      try {
        const res = await getMaintenanceStatus();
        setMaintenanceMode(res.maintenanceMode || false);
      } catch {
        // Ignore errors on initial load
      }
    };

    checkInitialStatus();
    const interval = setInterval(() => {
      checkInitialStatus();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const showConfirmation = (action: 'off' | 'on') => {
    setConfirmMode(action);
    setPassword('');
    setShowPassword(true);
  };

  const handlePasswordSubmit = async () => {
    if (!password.trim()) {
      setError('Please enter the admin password.');
      return;
    }

    setError(null);
    setIsToggling(true);
    setSuccess(null);

    try {
      const res = await toggleMaintenance({ password, expectedPassword: ADMIN_PASSWORD });
      if (res.maintenanceMode !== undefined) {
        setMaintenanceMode(res.maintenanceMode);
        setConfirmMode(null);
        setPendingToggle(null);
        setIsToggling(false);
        setSuccess(
          pendingToggle === 'on'
            ? 'Website disabled successfully. Public visitors now see the maintenance screen.'
            : 'Website reopened successfully. The public website is now accessible again.'
        );
        trackEvent('maintenance_toggle', { success: true, mode: pendingToggle });
      } else {
        setError(res.error || 'Unknown error from server');
        setIsToggling(false);
      }
    } catch (err) {
      console.error('Maintenance toggle error:', err);
      setError('Failed to toggle maintenance mode. Please try again.');
      setIsToggling(false);
    }
  };

  const handleCancel = () => {
    setConfirmMode(null);
    setShowPassword(false);
    setPassword('');
  };

  return (
    <div className="p-8 space-y-6">
      {/* Status Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6"
      >
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-500/20 to-orange-500/20 border border-red-500/30 flex items-center justify-center shrink-0">
            <AlertCircle className="w-6 h-6 text-red-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold text-white">Website Status</h3>
            <p className="text-sm text-gray-400">
              {maintenanceMode ? '🔴 OFFLINE' : '🟢 ONLINE'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {maintenanceMode
                ? 'Public visitors will see the maintenance screen.'
                : 'The existing AVORA website is fully accessible.'}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Action Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Disable Website Button */}
        <button
          onClick={() => showConfirmation('off')}
          disabled={isToggling || maintenanceMode}
          className={`w-full py-3 px-4 rounded-xl transition-all ${
            isToggling
              ? 'bg-gray-600/50 cursor-not-allow'
              : maintenanceMode
                ? 'bg-red-500/20 text-red-300 border border-red-500/30 cursor-not-allow'
                : 'bg-red-500/20 text-red-200 hover:bg-red-400/30 border border-red-300/50'
          }`}
        >
          {isToggling ? (
            <Loader2 className="mr-2 w-4 h-4 animate-spin" />
          ) : (
            <span>{maintenanceMode ? 'Maintenance Enabled' : 'Disable Website'}</span>
          )}
        </button>

        {/* Reopen Website Button */}
        <button
          onClick={() => showConfirmation('on')}
          disabled={!maintenanceMode || isToggling}
          className={`w-full py-3 px-4 rounded-xl transition-all ${
            isToggling
              ? 'bg-gray-600/50 cursor-not-allow'
              : !maintenanceMode
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 cursor-not-allow'
                : 'bg-emerald-500/20 text-emerald-200 hover:bg-emerald-400/30 border border-emerald-300/50'
          }`}
        >
          {isToggling ? (
            <Loader2 className="mr-2 w-4 h-4 animate-spin" />
          ) : (
            <span>{!maintenanceMode ? 'Reopen Website' : 'Website Enabled'}</span>
          )}
        </button>
      </div>

      {/* Confirmation Modal with Password */}
      {showPassword && (
        <motion.div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center"
          animate={{ opacity: [0, 1], transition: { duration: 0.2 } }}
        >
          <div className="bg-white/[0.02] border border-white/[0.08] rounded-2xl p-8 max-w-sm w-full text-center backdrop-blur-xl">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="mb-6"
            >
              {confirmMode === 'on' ? (
                <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              ) : (
                <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
              )}
            </motion.div>

            <h3 className="text-xl font-bold text-white mb-3">
              {confirmMode === 'on' ? 'Disable Public Website?' : 'Reopen Public Website?'}
            </h3>

            <p className="text-sm text-gray-400 mb-6 line-clamp-2">
              {confirmMode === 'on'
                ? 'Visitors will temporarily see the maintenance screen. No existing website content will be changed.'
                : 'The existing AVORA website will become publicly accessible again.'}
            </p>

            <div>
              <label className="block text-sm text-gray-300 mb-2">
                Admin password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'password' : 'text'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter admin password"
                  className="w-full px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.08] text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-400 hover:text-gray-200 transition-all"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            <div className="flex gap-3 pt-6">
              <button
                onClick={handleCancel}
                className="flex-1 py-2 px-4 rounded-xl bg-white/[0.03] border border-white/[0.08] text-gray-400 hover:text-gray-200 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handlePasswordSubmit}
                className="flex-1 py-2 px-4 rounded-xl bg-gradient-to-r from-red-500 to-purple-500 text-white hover:from-red-600 hover:to-purple-600 focus:outline-none focus:ring-2 focus:ring-red-500/50 transition-all"
                disabled={isToggling}
              >
                {isToggling ? 'Authenticating...' : 'Toggle Website'}
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Status and Feedback */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 mb-4"
        >
          <p className="text-sm text-red-300">{error}</p>
        </motion.div>
      )}

      {success && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 mb-4"
        >
          <p className="text-sm text-emerald-400">{success}</p>
        </motion.div>
      )}

      {/* Last checked info */}
      <div className="pt-4 border-t border-white/[0.08]">
        <p className="text-xs text-gray-500">
          Status checked every 30 seconds. Admin authentication required for changes.
        </p>
      </div>
    </div>
  );
}