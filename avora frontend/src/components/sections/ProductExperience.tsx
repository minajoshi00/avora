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
    <section id="showcase" className="relative py-32">
      <div className="max-w-7xl mx-auto px-6">
        <SectionHeading
          label="Showcase"
          title="See NOVA in action"
          description="Real interactions. Real intelligence. Experience the difference."
        />

        <div className="mt-16">
          <motion.div className="flex justify-center gap-2 mb-10">
            {(['voice','creation','memory'] as Tab[]).map((t) => (
              <motion.button
                key={t}
                onClick={() => setTab(t)}
                className={cn(
                  'px-4 py-2 rounded-full text-sm border transition-all duration-300 capitalize hover-target',
                  tab === t
                    ? 'bg-white/[0.08] border-white/[0.15] text-white'
                    : 'bg-white/[0.02] border-white/[0.08] text-gray-400 hover:text-gray-200'
                )}
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
              >
                {t}
              </motion.button>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-2xl mx-auto"
            key={tab}
          >
            {tab === 'voice' && <VoiceDemo />}
            {tab === 'creation' && <CreationDemo />}
            {tab === 'memory' && <MemoryDemo />}
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export default ProductExperience;