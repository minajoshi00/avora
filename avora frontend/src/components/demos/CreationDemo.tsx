'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Image as ImageIcon } from 'lucide-react';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';

export function CreationDemo() {
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleGenerate = () => {
    if (!input.trim()) return;
    setIsGenerating(true);
    setResult(null);
    setTimeout(() => {
      setIsGenerating(false);
      setResult('Created from your imagination');
    }, 1800);
  };

  return (
    <div className="flex flex-col items-center gap-5">
      <div className="relative">
        <InteractiveAvoraCore state={isGenerating ? 'excited' : 'idle'} size={140} />
      </div>

      <div className="w-full space-y-3">
        <motion.input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe what you imagine..."
          className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-blue-400/30 transition-colors"
          whileFocus={{ scale: 1.02 }}
        />
        <motion.div
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="hover-target"
        >
          <button
            onClick={handleGenerate}
            disabled={!input.trim() || isGenerating}
            className="w-full px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white text-sm font-medium disabled:opacity-50 transition-opacity"
          >
            {isGenerating ? 'Generating...' : 'Create'}
          </button>
        </motion.div>
      </div>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="w-full rounded-xl border border-white/[0.08] bg-white/[0.02] p-4 text-center text-xs text-gray-400"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.1 }}
              className="inline-block mb-2"
            >
              <ImageIcon size={16} className="text-purple-400" />
            </motion.div>
            {result}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default CreationDemo;