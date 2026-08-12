'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { completeFirstRun, isFirstRunComplete } from '../../lib/storage';
import { initAnalytics, updateAnalyticsSettings, trackNewUser } from '../../lib/analytics';
import { Button } from '../ui/Button';

/**
 * FirstRunExperience
 * 
 * Welcome screen shown on first launch.
 * Never shown again after completion.
 */
export function FirstRunExperience() {
  const [show, setShow] = useState(false);
  const [analyticsOptIn, setAnalyticsOptIn] = useState(true);

  useEffect(() => {
    // Check if first run is complete
    const complete = isFirstRunComplete();
    if (!complete) {
      // Small delay for better UX
      setTimeout(() => setShow(true), 500);
    }
  }, []);

  const handleGetStarted = () => {
    // Save first run complete
    completeFirstRun();
    
    // Initialize analytics with user choice
    if (analyticsOptIn) {
      updateAnalyticsSettings(true, true);
      initAnalytics(true, true);
      trackNewUser();
    } else {
      updateAnalyticsSettings(false, false);
      initAnalytics(false, false);
    }
    
    setShow(false);
  };

  const handleSkip = () => {
    // User skipped - disable analytics by default
    completeFirstRun();
    updateAnalyticsSettings(false, false);
    initAnalytics(false, false);
    setShow(false);
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 30 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 24 }}
            className="relative w-full max-w-md rounded-3xl border border-white/[0.08] bg-[#0a0a0f] backdrop-blur-xl p-8 shadow-2xl"
          >
            {/* Decorative gradient */}
            <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 pointer-events-none" />
            
            <div className="relative space-y-6">
              {/* Welcome Icon */}
              <div className="flex justify-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/[0.08] flex items-center justify-center">
                  <span className="text-4xl">👋</span>
                </div>
              </div>

              {/* Content */}
              <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-white">Welcome to AVORA!</h2>
                <p className="text-sm text-gray-400 leading-relaxed">
                  Thank you for trying AVORA. We're excited to have you here.
                </p>
              </div>

              {/* Analytics Opt-in */}
              <div className="space-y-3">
                <label className="flex items-start gap-3 p-4 rounded-xl border border-white/[0.08] bg-white/[0.02] cursor-pointer hover:bg-white/[0.04] transition-colors">
                  <input
                    type="checkbox"
                    checked={analyticsOptIn}
                    onChange={(e) => setAnalyticsOptIn(e.target.checked)}
                    className="mt-1 w-4 h-4 rounded border-gray-600 bg-transparent text-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  />
                  <div className="space-y-1">
                    <span className="text-sm font-medium text-white">Help improve AVORA</span>
                    <p className="text-xs text-gray-500 leading-relaxed">
                      Share anonymous usage data to help us fix bugs and prioritize features.
                      No personal information is collected.
                    </p>
                  </div>
                </label>
              </div>

              {/* Actions */}
              <div className="flex flex-col gap-3 pt-2">
                <Button
                  size="lg"
                  onClick={handleGetStarted}
                  className="w-full"
                  magnetic
                >
                  Get Started
                </Button>
                <Button
                  size="md"
                  variant="ghost"
                  onClick={handleSkip}
                  className="w-full text-gray-400 hover:text-white"
                >
                  Skip Tutorial
                </Button>
              </div>

              {/* Footer note */}
              <p className="text-center text-[10px] text-gray-600 pt-2">
                You can change this anytime in Settings
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default FirstRunExperience;