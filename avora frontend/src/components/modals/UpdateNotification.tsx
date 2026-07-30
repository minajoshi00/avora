'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getStoredUpdateInfo, clearUpdate } from '../../lib/update-checker';
import { trackEvent } from '../../lib/analytics';
import { Button } from '../ui/Button';

/**
 * UpdateNotification
 * 
 * Non-intrusive update notification.
 * Never forces updates - user always has the final say.
 */
export function UpdateNotification() {
  const [show, setShow] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<{ version: string; url: string } | null>(null);

  useEffect(() => {
    // Check for stored update info
    const info = getStoredUpdateInfo();
    if (info) {
      // Small delay before showing
      const timer = setTimeout(() => {
        setUpdateInfo(info);
        setShow(true);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, []);

  const handleUpdate = () => {
    if (!updateInfo) return;

    trackEvent('Update', { action: 'clicked', version: updateInfo.version });
    
    // Open download page
    window.open(updateInfo.url, '_blank');
    
    // Don't clear - user may come back
    setShow(false);
  };

  const handleLater = () => {
    trackEvent('Update', { action: 'later' });
    setShow(false);
  };

  const handleDismiss = () => {
    trackEvent('Update', { action: 'dismissed' });
    clearUpdate();
    setShow(false);
  };

  return (
    <AnimatePresence>
      {show && updateInfo && (
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ type: 'spring', stiffness: 300, damping: 24 }}
          className="fixed top-6 left-1/2 z-[150] -translate-x-1/2 max-w-lg w-full mx-4"
        >
          <div className="relative rounded-2xl border border-blue-500/30 bg-[#0f0f14] backdrop-blur-xl p-5 shadow-2xl overflow-hidden">
            {/* Accent line */}
            <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500" />

            <div className="flex items-start gap-4">
              {/* Icon */}
              <div className="text-3xl">🎉</div>

              {/* Content */}
              <div className="flex-1 space-y-3">
                <div>
                  <h3 className="text-base font-semibold text-white">Update Available</h3>
                  <p className="text-sm text-gray-400 mt-1">
                    AVORA v{updateInfo.version} is ready with the latest features and improvements.
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={handleUpdate}
                  >
                    Update Now
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleLater}
                  >
                    Later
                  </Button>
                  <button
                    onClick={handleDismiss}
                    className="text-gray-500 hover:text-gray-300 transition-colors ml-auto"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 6L6 18M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default UpdateNotification;