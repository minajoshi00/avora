'use client';

import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import {
  type VisualMode,
  type VisualConfig,
  getStoredVisualMode,
  setStoredVisualMode,
  getVisualConfig,
  prefersReducedMotion,
} from '../../lib/visual-mode';

interface VisualModeContextValue {
  mode: VisualMode;
  config: VisualConfig;
  setMode: (mode: VisualMode) => void;
  toggleMode: () => void;
  isCalm: boolean;
  isCinematic: boolean;
  reducedMotion: boolean;
}

const VisualModeContext = createContext<VisualModeContextValue | undefined>(undefined);

export function useVisualMode(): VisualModeContextValue {
  const ctx = useContext(VisualModeContext);
  if (!ctx) {
    throw new Error('useVisualMode must be used within a VisualModeProvider');
  }
  return ctx;
}

interface VisualModeProviderProps {
  children: ReactNode;
}

export function VisualModeProvider({ children }: VisualModeProviderProps) {
  const [mode, setMode] = useState<VisualMode>('cinematic');
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const initialMode = getStoredVisualMode();
    setMode(initialMode);
    setReducedMotion(prefersReducedMotion());

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handler = (e: MediaQueryListEvent) => {
      setReducedMotion(e.matches);
      if (e.matches) {
        try {
          const raw = localStorage.getItem('avora_visual_mode');
          if (!raw) {
            setMode('calm');
          }
        } catch {}
      }
    };
    mediaQuery.addEventListener('change', handler);

    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  const setModePersisted = (newMode: VisualMode) => {
    setMode(newMode);
    setStoredVisualMode(newMode);
  };

  const toggleMode = () => {
    const next: VisualMode = mode === 'cinematic' ? 'calm' : 'cinematic';
    setModePersisted(next);
  };

  const value = useMemo(
    () => ({
      mode,
      config: getVisualConfig(mode),
      setMode: setModePersisted,
      toggleMode,
      isCalm: mode === 'calm',
      isCinematic: mode === 'cinematic',
      reducedMotion,
    }),
    [mode, reducedMotion]
  );

  // Set data attribute and CSS custom properties on document body for CSS-based mode switching
  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('data-visual-mode', mode);

    const cfg = getVisualConfig(mode);
    // Expose mode config as CSS custom properties so CSS glow/shadow effects adapt
    root.style.setProperty('--mode-glow', String(cfg.glowIntensity));
    root.style.setProperty('--mode-particle-opacity', String(cfg.particleOpacity));
    root.style.setProperty('--mode-particle-speed', String(cfg.particleSpeed));
    root.style.setProperty('--mode-parallax', String(cfg.parallaxIntensity));
    root.style.setProperty('--mode-animation-speed', String(cfg.animationSpeed));
    root.style.setProperty('--mode-blur', String(cfg.blurStrength));
    root.style.setProperty('--mode-bg-glow', String(0.06 * cfg.glowIntensity));
    root.style.setProperty('--mode-scrim', String(0.85 - 0.3 * cfg.glowIntensity));
  }, [mode]);

  return (
    <VisualModeContext.Provider value={value}>
      {children}
    </VisualModeContext.Provider>
  );
}
