import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface CinematicIntroProps {
  reducedMotion: boolean;
  lowQuality: boolean;
  onProgress: (progress: number) => void;
  onComplete: () => void;
}

const INTRO_DURATION = 8000;
const MOBILE_DURATION = 5000;
const STORAGE_KEY = 'avora-intro-seen';

export function CinematicIntro({ reducedMotion, lowQuality, onProgress, onComplete }: CinematicIntroProps) {
  const [visible, setVisible] = useState(true);
  const [showSkip, setShowSkip] = useState(false);
  const startRef = useRef<number | null>(null);
  const rafRef = useRef<number>(0);
  const completedRef = useRef(false);
  
  // Duration adjusted for mobile quality and reduced motion
  const duration = reducedMotion ? 0 : (lowQuality ? MOBILE_DURATION : INTRO_DURATION);

  useEffect(() => {
    if (reducedMotion) {
      onProgress(1);
      onComplete();
      setVisible(false);
      return;
    }
    try {
      if (sessionStorage.getItem(STORAGE_KEY)) {
        onProgress(1);
        onComplete();
        setVisible(false);
        return;
      }
    } catch {}
    const skipTimer = window.setTimeout(() => setShowSkip(true), 1200);
    const tick = (timestamp: number) => {
      if (startRef.current === null) startRef.current = timestamp;
      const elapsed = timestamp - startRef.current;
      const raw = Math.min(1, elapsed / duration);
      const eased = raw < 0.5 ? 2 * raw * raw : 1 - Math.pow(-2 * raw + 2, 2) / 2;
      onProgress(eased);
      if (raw >= 1) {
        if (!completedRef.current) {
          completedRef.current = true;
          try { sessionStorage.setItem(STORAGE_KEY, '1'); } catch {}
          onComplete();
          setVisible(false);
        }
        return;
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      window.clearTimeout(skipTimer);
      cancelAnimationFrame(rafRef.current);
    };
  }, [reducedMotion, lowQuality, duration, onProgress, onComplete]);

  const handleSkip = () => {
    if (completedRef.current) return;
    completedRef.current = true;
    try { sessionStorage.setItem(STORAGE_KEY, '1'); } catch {}
    onProgress(1);
    onComplete();
    setVisible(false);
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.8, ease: 'easeInOut' } }}
          className="absolute inset-0 z-20 pointer-events-none"
          aria-hidden="true"
        >
          <AnimatePresence>
            {showSkip && (
              <motion.button
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
                onClick={handleSkip}
                className="absolute top-20 right-6 z-30 pointer-events-auto px-4 py-2 rounded-full border border-white/[0.1] bg-white/[0.03] backdrop-blur-md text-xs text-gray-400 hover:text-white hover:border-white/[0.25] transition-colors duration-300"
              >
                Skip intro
              </motion.button>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default CinematicIntro;