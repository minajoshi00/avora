import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, Wrench, Server } from 'lucide-react';

export function MaintenancePage() {
  const [checking, setChecking] = useState(true);

  const checkStatus = async () => {
    try {
      const res = await fetch('/api/admin/maintenance/status', { cache: 'no-store' });
      const data = await res.json();
      if (!data.maintenanceMode) {
        // Force page reload to load the actual app
        window.location.reload();
      }
    } catch {
      // If check fails, assume still in maintenance
    }
  };

  useEffect(() => {
    // Initial check after a short delay
    const timer = setTimeout(() => {
      setChecking(false);
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex flex-col items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-md w-full text-center"
      >
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/[0.08] flex items-center justify-center">
            <Server className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <h1 className="text-3xl font-bold text-white mb-3">AVORA</h1>
        <p className="text-sm text-gray-500 mb-10 tracking-wide uppercase">Temporarily Offline</p>

        {/* Status Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-8 mb-8"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <Wrench className="w-5 h-5 text-amber-400" />
            <span className="text-sm font-medium text-amber-300">Maintenance Mode Active</span>
          </div>

          <p className="text-gray-300 mb-2">
            AVORA is currently undergoing scheduled maintenance.
          </p>
          <p className="text-gray-500 text-sm">
            We'll be back shortly. Thank you for your patience.
          </p>
        </motion.div>

        {/* Check Status Button */}
        <button
          onClick={checkStatus}
          disabled={checking}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white font-medium hover:from-blue-600 hover:to-purple-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
        >
          {checking ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Checking Status...</span>
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4" />
              <span>Check Status Again</span>
            </>
          )}
        </button>

        <p className="text-center text-xs text-gray-600 mt-6">
          This page auto-refreshes when maintenance completes.
        </p>
      </motion.div>
    </div>
  );
}

export default MaintenancePage;