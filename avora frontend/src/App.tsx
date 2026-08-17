import { useState, useEffect } from 'react';
import { StrictMode } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { InteractiveBackground } from './components/ui/InteractiveBackground';
import { CursorGlow } from './components/interactions/CursorGlow';
import { CustomCursor } from './components/interactions/CustomCursor';
import { Home } from './pages/Home';
import { SoundToggle } from './components/ui/SoundToggle';
import { FirstRunExperience } from './components/modals/FirstRunExperience';
import { FeedbackPrompt } from './components/modals/FeedbackPrompt';
import { UpdateNotification } from './components/modals/UpdateNotification';
import { AdminLogin } from './pages/AdminLogin';
import AdminDashboardPage from './pages/AdminDashboardPage';
import { hasValidSession } from './lib/admin';
import { initAnalytics, trackPageView } from './lib/analytics';
import { getAnalyticsEnabled, getAnalyticsConsent } from './lib/storage';
import { MaintenancePage } from './components/MaintenancePage';

export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.hash);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [maintenanceMode, setMaintenanceMode] = useState(false);

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentPath(window.location.hash);
      setIsAuthenticated(hasValidSession());
    };
    window.addEventListener('hashchange', handleHashChange);
    setIsAuthenticated(hasValidSession());
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const analyticsEnabled = getAnalyticsEnabled();
      const consent = getAnalyticsConsent();
      initAnalytics(analyticsEnabled, consent);
      trackPageView(window.location.hash || window.location.pathname);
    }
  }, []);

  // Check maintenance mode on mount
  useEffect(() => {
    const checkMaintenance = async () => {
      try {
        const res = await fetch('/api/admin/maintenance/status', { cache: 'no-store' });
        const data = await res.json();
        setMaintenanceMode(data.maintenanceMode || false);
        // If coming from admin and turning off maintenance, reload
        if (!data.maintenanceMode && currentPath?.startsWith('#/admin')) {
          window.location.reload();
        }
      } catch {
        setMaintenanceMode(false);
      }
    };

    checkMaintenance();
  }, [currentPath]);

  // Auto-reload if maintenance completes while on the main page
  useEffect(() => {
    if (!maintenanceMode) {
      const timer = setTimeout(() => {
        window.location.reload();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [maintenanceMode]);

  if (maintenanceMode) {
    return <MaintenancePage />;
  }

  // Admin route logic
  const isAdminRoute = currentPath === '#/admin' || currentPath.startsWith('#/admin/');
  const isDashboardRoute = currentPath.startsWith('#/admin/') && currentPath !== '#/admin';

  if (isAdminRoute) {
    if (currentPath === '#/admin') {
      if (isAuthenticated) {
        window.location.hash = '#/admin/overview';
        return null;
      }
      return <AdminLogin />;
    }
    if (isDashboardRoute) {
      if (!isAuthenticated) {
        window.location.hash = '#/admin';
        return null;
      }
      return <AdminDashboardPage />;
    }
  }

  return (
    <StrictMode>
      <InteractiveBackground />
      <CursorGlow />
      <CustomCursor />
      <SoundToggle />
      <FirstRunExperience />
      <FeedbackPrompt />
      <UpdateNotification />
      <div className="relative z-10">
        <Navbar />
        <Home />
        <Footer />
      </div>
    </StrictMode>
  );
}