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
import { initAnalytics } from './lib/analytics';
import { getAnalyticsEnabled, getAnalyticsConsent } from './lib/storage';

export default function App() {
  // Initialize analytics on mount
  if (typeof window !== 'undefined') {
    const analyticsEnabled = getAnalyticsEnabled();
    const consent = getAnalyticsConsent();
    initAnalytics(analyticsEnabled, consent);
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
