'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain } from 'lucide-react';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';

interface MemoryItem {
  id: string;
  label: string;
  detail: string;
  time: string;
}

const memoryItems: MemoryItem[] = [
  { id: '1', label: 'First conversation', detail: 'You asked about creative writing.', time: '2 weeks ago' },
  { id: '2', label: 'Preference learned', detail: 'Prefers concise technical answers.', time: '1 week ago' },
  { id: '3', label: 'Project context', detail: 'Working on a mobile app design.', time: '3 days ago' },
  { id: '4', label: 'Current focus', detail: 'Exploring AVORA capabilities.', time: 'Now' },
];

export function MemoryDemo() {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="relative">
        <InteractiveAvoraCore state="thinking" size={140} />
      </div>

      <div className="w-full space-y-2">
        {memoryItems.map((item, index) => (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            onClick={() => setSelected(selected === item.id ? null : item.id)}
            className={`w-full text-left px-4 py-3 rounded-xl border transition-all duration-300 hover-target ${
              selected === item.id
                ? 'bg-white/[0.08] border-white/[0.15]'
                : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04]'
            }`}
            whileHover={{ scale: 1.02, x: 4 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <motion.div
                  animate={selected === item.id ? { scale: [1, 1.2, 1] } : {}}
                  transition={{ duration: 0.3 }}
                >
                  <Brain size={14} className={selected === item.id ? 'text-purple-400' : 'text-gray-500'} />
                </motion.div>
                <span className="text-xs font-medium text-gray-300">{item.label}</span>
              </div>
              <motion.span
                className="text-[10px] text-gray-600"
                animate={{ opacity: selected === item.id ? 1 : 0.5 }}
              >
                {item.time}
              </motion.span>
            </div>

            <AnimatePresence>
              {selected === item.id && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-2 text-xs text-gray-500 leading-relaxed"
                >
                  {item.detail}
                </motion.p>
              )}
            </AnimatePresence>
          </motion.button>
        ))}
      </div>
    </div>
  );
}

export default MemoryDemo;