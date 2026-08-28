'use client';

import { motion, useInView } from 'framer-motion';
import { useRef, useEffect, useState } from 'react';

interface ScrollRevealProps {
  children: React.ReactNode;
  delay?: number;
  direction?: 'up' | 'down' | 'left' | 'right';
  duration?: number;
  className?: string;
}

export function ScrollReveal({
  children,
  delay = 0,
  direction = 'up',
  duration = 0.8,
  className = ''
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    try {
      const m = window.matchMedia('(prefers-reduced-motion: reduce)');
      setReduced(m.matches);
      const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
      m.addEventListener('change', handler);
      return () => m.removeEventListener('change', handler);
    } catch {
      setReduced(false);
    }
  }, []);

  const directions = {
    up: { y: 40, x: 0 },
    down: { y: -40, x: 0 },
    left: { x: 28, y: 0 },
    right: { x: -28, y: 0 },
  };

  if (reduced) {
    // No motion, instantly visible
    return <div ref={ref as any} className={className}>{children}</div>;
  }

  return (
    <motion.div
      ref={ref}
      initial={{ 
        opacity: 0, 
        ...directions[direction],
        scale: 0.98
      }}
      animate={isInView ? { 
        opacity: 1, 
        x: 0, 
        y: 0, 
        scale: 1 
      } : { 
        opacity: 0, 
        ...directions[direction],
        scale: 0.98 
      }}
      transition={{
        duration,
        delay,
        ease: [0.16, 1, 0.3, 1],
      }}
      className={className}
      style={{ willChange: 'transform, opacity' }}
    >
      {children}
    </motion.div>
  );
}