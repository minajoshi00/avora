'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useVisualMode } from '../ui/VisualModeProvider';

export function CursorGlow() {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const { config } = useVisualMode();

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Scale glow opacity by mode config
  const baseOpacity = 0.08;
  const opacity = baseOpacity * config.glowIntensity;

  return (
    <motion.div
      className="fixed inset-0 pointer-events-none z-0"
      style={{
        background: `radial-gradient(circle at ${position.x}px ${position.y}px, rgba(96,165,250,${opacity}) 0%, transparent 40%)`,
      }}
    />
  );
}

export default CursorGlow;
