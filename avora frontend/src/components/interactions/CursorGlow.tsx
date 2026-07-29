'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export function CursorGlow() {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <motion.div
      className="fixed inset-0 pointer-events-none z-0 opacity-40"
      style={{
        background: `radial-gradient(circle at ${position.x}px ${position.y}px, rgba(96,165,250,0.12) 0%, transparent 40%)`,
      }}
    />
  );
}

export default CursorGlow;