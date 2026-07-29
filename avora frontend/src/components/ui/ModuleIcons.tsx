'use client';

import { motion } from 'framer-motion';
import { Brain, Network, Zap, Shield, Globe } from 'lucide-react';

const modules = [
  { icon: Brain, label: 'Neural Core', delay: 0 },
  { icon: Network, label: 'Data Stream', delay: 0.1 },
  { icon: Zap, label: 'Real-time', delay: 0.2 },
  { icon: Shield, label: 'Privacy', delay: 0.3 },
  { icon: Globe, label: 'Global', delay: 0.4 },
];

export function ModuleIcons() {
  return (
    <div className="flex items-center justify-center gap-6 mt-12">
      {modules.map((module) => (
        <motion.div
          key={module.label}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{
            duration: 0.6,
            delay: 1.2 + module.delay,
            ease: [0.16, 1, 0.3, 1],
          }}
          className="relative group"
        >
          <div className="relative flex items-center justify-center w-12 h-12 rounded-xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-sm transition-all duration-300 group-hover:border-white/[0.15] group-hover:bg-white/[0.04] group-hover:scale-110">
            <module.icon size={20} className="text-gray-400 group-hover:text-white transition-colors" />
            
            {/* Subtle glow on hover */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-blue-500/0 to-purple-500/0 group-hover:from-blue-500/10 group-hover:to-purple-500/10 transition-all duration-300 blur-sm" />
          </div>
          
          {/* Tooltip */}
          <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 rounded bg-black/80 border border-white/10 text-[10px] text-gray-300 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
            {module.label}
          </div>
        </motion.div>
      ))}
    </div>
  );
}