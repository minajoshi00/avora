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
          whileHover={{ scale: 1.02 }}
          className="group relative"
        >
          {/* Simplified card - reduced decorative effects */}
          <div className="relative px-4 py-3 rounded-xl border border-white/[0.05] bg-white/[0.01] transition-all duration-300 hover:border-white/[0.08] hover:bg-white/[0.02] min-w-[150px]">
            
            {/* Simple icon background */}
            <div className="relative flex items-center justify-center w-8 h-8 rounded-bg mb-2">
              <module.icon size={16} className="text-gray-400" />
            </div>
            
            {/* Simplified text */}
            <div className="relative text-left">
              <h4 className="text-xs font-medium text-gray-300 mb-0.5">
                {module.label}
              </h4>
              <p className="text-[10px] text-gray-500">
                {module.detail}
              </p>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}