import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
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
import { ErrorPage } from './components/ErrorPage';

export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.hash);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [calmMode, _setCalmMode] = useState(() => {
    if (typeof window !== 'undefined') {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return true;
      }
      const stored = localStorage.getItem('calmMode');
      return stored === 'true';
    }
    return false;
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const html = document.documentElement;
      if (calmMode) {
        html.classList.add('calm');
      } else {
        html.classList.remove('calm');
      }
    }
  }, [calmMode]);

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

  useEffect(() => {
    const checkMaintenance = async () => {
      try {
        const res = await fetch('/api/admin/maintenance/status', { cache: 'no-store' });
        const data = await res.json();
        setMaintenanceMode(data.maintenanceMode || false);
        // NOTE: never reload here. Recovery from the maintenance screen is
        // handled by MaintenancePage (manual/auto refresh). Reloading on
        // admin routes caused an infinite reload loop.
      } catch {
        setMaintenanceMode(false);
      }
    };

    checkMaintenance();
  }, [currentPath]);

  // Admin route logic (evaluated before maintenance gate so admin can recover from maintenance mode)
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

  if (maintenanceMode) {
    return <MaintenancePage />;
  }

  // Handle unknown routes (404)
  const knownPaths = ['', '#/admin', '#/admin/overview'];
  const isKnownPath = knownPaths.some(path => currentPath === path || currentPath.startsWith(path));
  
  if (!isKnownPath && currentPath !== '' && currentPath !== '#') {
    return <ErrorPage statusCode={404} />;
  }

  return (
    <>
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
    </>
  );
}