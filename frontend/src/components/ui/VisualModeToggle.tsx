'use client';

import { motion } from 'framer-motion';
import { Zap, Moon } from 'lucide-react';
import { useVisualMode } from './VisualModeProvider';
import type { VisualMode } from '../../lib/visual-mode';

export function VisualModeToggle() {
  const { mode, setMode, config } = useVisualMode();

  const isCinematic = mode === 'cinematic';

  return (
    <div
      role="radiogroup"
      aria-label="Visual mode"
      className="inline-flex items-center gap-1 p-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] backdrop-blur-md"
    >
      <VisualModeOption
        mode="cinematic"
        label="Cinematic"
        icon={<Zap size={14} />}
        isActive={isCinematic}
        onClick={() => setMode('cinematic')}
        color="blue"
        glowScale={config.glowIntensity}
      />
      <VisualModeOption
        mode="calm"
        label="Calm"
        icon={<Moon size={14} />}
        isActive={!isCinematic}
        onClick={() => setMode('calm')}
        color="purple"
        glowScale={config.glowIntensity}
      />
    </div>
  );
}

interface VisualModeOptionProps {
  mode: VisualMode;
  label: string;
  icon: React.ReactNode;
  isActive: boolean;
  onClick: () => void;
  color: 'blue' | 'purple';
  glowScale: number;
}

function VisualModeOption({
  mode,
  label,
  icon,
  isActive,
  onClick,
  color,
  glowScale,
}: VisualModeOptionProps) {
  const colorMap = {
    blue: 'from-blue-500 to-cyan-500',
    purple: 'from-purple-500 to-pink-500',
  };

  return (
    <motion.button
      type="button"
      role="radio"
      aria-checked={isActive}
      aria-label={`${mode} mode ${isActive ? '(active)' : ''}`}
      onClick={onClick}
      className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300 ${
        isActive
          ? `text-white bg-gradient-to-r ${colorMap[color]} shadow-[0_0_15px_rgba(96,165,250,0.3)]`
          : 'text-gray-400 hover:text-gray-300 hover:bg-white/[0.05]'
      }`}
      whileHover={isActive ? { scale: 1.05, y: -1 } : { scale: 1.02, y: -1 }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
    >
      {isActive && (
        <motion.span
          layoutId="visualModeActive"
          className="absolute inset-0 rounded-full"
          style={{
            background: `radial-gradient(circle, rgba(96,165,250,${0.15 * glowScale}) 0%, transparent 70%)`,
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
        />
      )}
      <span className="relative z-10 flex items-center gap-1.5">
        {icon}
        {label}
      </span>
    </motion.button>
  );
}
