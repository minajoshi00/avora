'use client';

import { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { hasValidSession, logout } from '../lib/admin';
import { AdminLoginModal } from './modals/AdminLoginModal';
import { AdminDashboardModal } from './modals/AdminDashboardModal';

export function Footer() {
  const [showLogin, setShowLogin] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);

  useEffect(() => {
    // Check if already authenticated
    if (hasValidSession()) {
      // Preload dashboard, but don't show yet
    }
  }, []);

  const handleDotClick = () => {
    if (hasValidSession()) {
      setShowDashboard(true);
    } else {
      setShowLogin(true);
    }
  };

  const handleLoginSuccess = () => {
    setShowLogin(false);
    setShowDashboard(true);
  };

  const handleLogout = () => {
    logout();
    setShowDashboard(false);
  };

  const handleCloseDashboard = () => {
    setShowDashboard(false);
  };

  return (
    <>
      <footer className="relative border-t border-white/[0.06] py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <h3 className="text-xl font-bold text-white">
              Pratik Ojha
            </h3>
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

            {/* Hidden dot */}
            <button
              onClick={handleDotClick}
              className="mt-4 w-2 h-2 rounded-full bg-transparent hover:bg-white/10 transition-colors opacity-30 hover:opacity-60"
              aria-hidden="true"
            />
          </div>
        </div>
      </footer>

      {/* Login Modal */}
      <AnimatePresence>
        {showLogin && (
          <AdminLoginModal onClose={() => setShowLogin(false)} onSuccess={handleLoginSuccess} />
        )}
      </AnimatePresence>

      {/* Dashboard Modal */}
      <AnimatePresence>
        {showDashboard && (
          <AdminDashboardModal onClose={handleCloseDashboard} onLogout={handleLogout} />
        )}
      </AnimatePresence>
    </>
  );
}
