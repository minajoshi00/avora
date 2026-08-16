import { type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  glow?: 'blue' | 'purple' | 'none';
  hover?: boolean;
}

export function GlassCard({
  children,
  className,
  glow = 'none',
  hover = true,
}: GlassCardProps) {
  const glowStyles = {
    blue: 'hover:shadow-[0_0_30px_rgba(96,165,250,0.1)]',
    purple: 'hover:shadow-[0_0_30px_rgba(167,139,250,0.1)]',
    none: '',
  };

  return (
    <motion.div
      whileHover={hover ? { y: -8, scale: 1.02 } : undefined}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      className={cn(
        'relative rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl',
        'p-6 transition-all duration-500 hover-target',
        glowStyles[glow],
        className
      )}
    >
      {/* Subtle inner border glow */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/[0.04] to-transparent pointer-events-none" />
      {children}
    </motion.div>
  );
}
