'use client';

import { motion } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { VoiceDemo } from '../demos/VoiceDemo';
import { CreationDemo } from '../demos/CreationDemo';
import { MemoryDemo } from '../demos/MemoryDemo';
import { useState } from 'react';
import { cn } from '../../lib/utils';

type Tab = 'voice' | 'creation' | 'memory';

export function ProductExperience() {
  const [tab, setTab] = useState<Tab>('voice');

  return (
    <section id="showcase" className="relative py-32 overflow-hidden">
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <motion.div
          className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[min(600px,92vw)] h-[300px] rounded-full bg-purple-500/5 blur-3xl avora-drift"
          animate={{ x: ['-50%', '-48%', '-50%'], opacity: [0.5, 0.7, 0.5] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>
      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          <SectionHeading
            label="Showcase"
            title="See AVORA in action"
            description="Real interactions. Real intelligence. Experience the difference."
          />
        </motion.div>

        <div className="mt-16">
          <motion.div
            className="flex justify-center gap-2 mb-10"
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.12, ease: [0.16, 1, 0.3, 1] }}
          >
            {(['voice','creation','memory'] as Tab[]).map((t, i) => (
              <motion.button
                key={t}
                onClick={() => setTab(t)}
                className={cn(
                  'px-4 py-2 rounded-full text-sm border transition-all duration-300 capitalize hover-target',
                  tab === t
                    ? 'bg-white/[0.08] border-white/[0.15] text-white shadow-[0_0_20px_rgba(139,92,246,0.15)]'
                    : 'bg-white/[0.02] border-white/[0.08] text-gray-400 hover:text-gray-200'
                )}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 + i * 0.06, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
              >
                {t}
              </motion.button>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="max-w-2xl mx-auto"
            key={tab}
          >
            <div className="hover-lift">
              {tab === 'voice' && <VoiceDemo />}
              {tab === 'creation' && <CreationDemo />}
              {tab === 'memory' && <MemoryDemo />}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export default ProductExperience;