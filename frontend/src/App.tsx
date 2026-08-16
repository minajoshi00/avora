import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { InteractiveBackground } from './components/ui/InteractiveBackground';
import { CursorGlow } from './components/interactions/CursorGlow';
import { CustomCursor } from './components/interactions/CustomCursor';
import { Home } from './pages/Home';
import { FirstRunExperience } from './components/modals/FirstRunExperience';
import { FeedbackPrompt } from './components/modals/FeedbackPrompt';
import { UpdateNotification } from './components/modals/UpdateNotification';
import AdminLogin from './pages/AdminLogin';
import AdminDashboardPage from './pages/AdminDashboardPage';
import { hasValidSession } from './lib/admin';
import { initAnalytics, trackPageView } from './lib/analytics';
import { getAnalyticsEnabled, getAnalyticsConsent } from './lib/storage';
import { useVisualMode } from './components/ui/VisualModeProvider';
import { TakeOver } from './components/takeover';

export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.hash);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const { isCalm } = useVisualMode();

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

  // Track page views on hash/route changes (real events, consent-gated).
  useEffect(() => {
    const onRoute = () => trackPageView(window.location.hash || window.location.pathname);
    window.addEventListener('hashchange', onRoute);
    return () => window.removeEventListener('hashchange', onRoute);
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
      <InteractiveBackground quality="high" />
      <CursorGlow />
      <CustomCursor />
      <Home />
      <FirstRunExperience />
      <FeedbackPrompt />
      <UpdateNotification />
      <div className="relative z-10">
        <Navbar />
        <Footer />
      </div>

      {/* Take Over experience */}
      <TakeOver />

      {/* Single ambient glow layer — intensity adapts to visual mode */}
      <div
        className={`fixed inset-0 pointer-events-none transition-opacity duration-1000 ${
          isCalm ? 'opacity-10' : 'opacity-20'
        }`}
        style={{
          background:
            'radial-gradient(ellipse at center, rgba(96,165,250,0.06) 0%, rgba(167,139,250,0.03) 35%, transparent 70%)',
          zIndex: 0,
        }}
      />
    </>
  );
}