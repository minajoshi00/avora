import { useState, useEffect } from 'react';
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
import { initAnalytics } from './lib/analytics';
import { getAnalyticsEnabled, getAnalyticsConsent } from './lib/storage';

export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.hash);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

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
    }
  }, []);

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
    <>
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
    </>
  );
}
