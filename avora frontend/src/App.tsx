import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { InteractiveBackground } from './components/ui/InteractiveBackground';
import { CursorGlow } from './components/interactions/CursorGlow';
import { CustomCursor } from './components/interactions/CustomCursor';
import { Home } from './pages/Home';
import { SoundToggle } from './components/ui/SoundToggle';

export default function App() {
  return (
    <>
      <InteractiveBackground />
      <CursorGlow />
      <CustomCursor />
      <SoundToggle />
      <div className="relative z-10">
        <Navbar />
        <Home />
        <Footer />
      </div>
    </>
  );
}
