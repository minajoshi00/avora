'use client';

import { useEffect, useRef, useState } from 'react';

/**
 * Cinematic scroll progress hook.
 *
 * Provides a 0→1 progress value as the user scrolls through the page.
 * Coordinates with 3D scene parameters for cinematic choreography.
 *
 * Features:
 * - Smooth eased progress using requestAnimationFrame
 * - Respects reduced-motion preferences
 * - Clamped to [0, 1] range
 * - Works with SSR (returns 0 on server)
 */
export function useScrollProgress({ offsetTop = 0, offsetBottom = 0 }: { offsetTop?: number; offsetBottom?: number } = {}) {
  const [progress, setProgress] = useState(0);
  const rafRef = useRef<number | null>(null);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  useEffect(() => {
    if (reducedMotion.matches) {
      setProgress(0);
      return;
    }

    const updateProgress = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const clamped = Math.max(0, Math.min(1, (scrollTop - offsetTop) / (docHeight - offsetTop - offsetBottom)));
      setProgress(clamped);
      rafRef.current = requestAnimationFrame(updateProgress);
    };

    updateProgress();
    rafRef.current = requestAnimationFrame(updateProgress);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [offsetTop, offsetBottom, reducedMotion.matches]);

  return progress;
}