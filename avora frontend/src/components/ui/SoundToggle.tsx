'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Volume2, VolumeX } from 'lucide-react';
import { useSound } from '../../hooks/useSound';

export function SoundToggle() {
  const { enabled, toggle, play } = useSound();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={() => {
        play('click');
        toggle();
      }}
      className="fixed bottom-6 right-6 z-50 p-3 rounded-full glass-panel border border-white/[0.08] bg-white/[0.03] backdrop-blur-xl hover:border-white/[0.15] transition-all"
      aria-label="Toggle sound"
    >
      {enabled ? (
        <Volume2 size={18} className="text-gray-300" />
      ) : (
        <VolumeX size={18} className="text-gray-500" />
      )}
    </motion.button>
  );
}