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
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';
import { initAnalytics } from './lib/analytics';
import { getAnalyticsEnabled, getAnalyticsConsent } from './lib/storage';

type Page = 'home' | 'admin-login' | 'admin-dashboard';

export default function App() {
  const [page, setPage] = useState<Page>('home');

  // Initialize analytics on mount
  if (typeof window !== 'undefined') {
    const analyticsEnabled = getAnalyticsEnabled();
    const consent = getAnalyticsConsent();
    initAnalytics(analyticsEnabled, consent);
  }

  useEffect(() => {
    // Simple hash-based routing
    const handleHashChange = () => {
      const hash = window.location.hash;
      if (hash.includes('#admin') && !hash.includes('/dashboard')) {
        setPage('admin-login');
      } else if (hash.includes('#admin/dashboard')) {
        setPage('admin-dashboard');
      } else {
        setPage('home');
      }
    };

    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Public background and modals
  const publicUI = (
    <>
      <InteractiveBackground />
      <CursorGlow />
      <CustomCursor />
      <SoundToggle />
      <FirstRunExperience />
      <FeedbackPrompt />
      <UpdateNotification />
    </>
  );

  if (page === 'admin-login') {
    return (
      <>
        {publicUI}
        <AdminLogin />
      </>
    );
  }

  if (page === 'admin-dashboard') {
    return <AdminDashboard />;
  }

  return (
    <>
      {publicUI}
      <div className="relative z-10">
        <Navbar />
        <Home />
        <Footer />
      </div>
    </>
  );
}
