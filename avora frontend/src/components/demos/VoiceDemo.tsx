'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, PhoneOff } from 'lucide-react';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';
import { cn } from '../../lib/utils';

type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking';

export function VoiceDemo() {
  const [status, setStatus] = useState<VoiceState>('idle');

  const startListening = () => {
    setStatus('listening');
    setTimeout(() => setStatus('thinking'), 2000);
    setTimeout(() => setStatus('speaking'), 3500);
    setTimeout(() => setStatus('idle'), 6000);
  }

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="relative">
        <InteractiveAvoraCore
          state={status === 'idle' ? 'idle' : status === 'listening' ? 'listening' : status === 'thinking' ? 'thinking' : 'speaking'}
          size={160}
        />
        <AnimatePresence>
          {status !== 'idle' && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <div className="px-3 py-1 rounded-full bg-white/[0.06] border border-white/[0.08] backdrop-blur-xl">
                <span className="text-[10px] uppercase tracking-widest text-gray-400">
                  {status}
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <motion.button
        onClick={status === 'idle' ? startListening : undefined}
        disabled={status !== 'idle'}
        className={cn(
          'relative w-16 h-16 rounded-full flex items-center justify-center transition-all duration-500 hover-target',
          status === 'idle'
            ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
            : 'bg-white/[0.04] border border-white/[0.06] text-gray-500'
        )}
        whileHover={{ scale: status === 'idle' ? 1.1 : 1 }}
        whileTap={{ scale: status === 'idle' ? 0.9 : 1 }}
        transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      >
        <motion.div
          animate={status === 'idle' ? { scale: [1, 1.1, 1] } : {}}
          transition={{ duration: 2, repeat: Infinity }}
        >
          {status === 'idle' ? <Mic size={22} /> : <PhoneOff size={22} />}
        </motion.div>
        {status !== 'idle' && (
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-blue-500/50"
            animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}
      </motion.button>
      <motion.p
        className="text-xs text-gray-500"
        animate={{ opacity: status === 'idle' ? 1 : [0.5, 1, 0.5] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        {status === 'idle' ? 'Tap to speak' : status === 'listening' ? 'Listening...' : status === 'thinking' ? 'Thinking...' : 'Speaking...'}
      </motion.p>
    </div>
  );
}

export default VoiceDemo;