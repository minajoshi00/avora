'use client';

import { motion } from 'framer-motion';
import { Brain, Network, Zap, Shield, Globe } from 'lucide-react';

const modules = [
  { icon: Brain, label: 'Neural Core', detail: 'Deep reasoning engine' },
  { icon: Network, label: 'Data Stream', detail: 'Real-time processing' },
  { icon: Zap, label: 'Instant AI', detail: 'Sub-100ms response' },
  { icon: Shield, label: 'Privacy', detail: 'End-to-end encrypted' },
  { icon: Globe, label: 'Global', detail: 'Multi-language native' },
];

export function GlassModuleCards() {
  return (
    <div className="flex items-center justify-center gap-5 mt-14 flex-wrap">
      {modules.map((module, index) => (
        <motion.div
          key={module.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.7,
            delay: 1.2 + index * 0.1,
            ease: [0.16, 1, 0.3, 1],
          }}
          whileHover={{ 
            scale: 1.05, 
            y: -4,
            transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] }
          }}
          className="group relative"
        >
          {/* Glassmorphism card */}
          <div className="relative px-5 py-4 rounded-2xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-xl transition-all duration-500 hover:border-white/[0.15] hover:bg-white/[0.06] min-w-[160px]">
            
            {/* Neon border glow on hover */}
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/0 via-purple-500/0 to-pink-500/0 group-hover:from-blue-500/10 group-hover:via-purple-500/10 group-hover:to-pink-500/10 transition-all duration-500 blur-xl opacity-0 group-hover:opacity-100" />
            
            {/* Icon */}
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-white/[0.06] mb-3 group-hover:border-white/[0.12] transition-all duration-300">
              <module.icon size={18} className="text-gray-300 group-hover:text-white transition-colors" />
            </div>
            
            {/* Text */}
            <div className="relative text-left">
              <h4 className="text-xs font-semibold text-gray-200 group-hover:text-white transition-colors mb-0.5">
                {module.label}
              </h4>
              <p className="text-[10px] text-gray-500 group-hover:text-gray-400 transition-colors">
                {module.detail}
              </p>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}