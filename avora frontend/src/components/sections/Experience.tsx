'use client';

import { motion } from 'framer-motion';
import { ChatDemo } from '../demos/ChatDemo';
import { SectionHeading } from '../ui/SectionHeading';

export function ExperienceSection() {
  return (
    <section id="experience" className="relative py-32 overflow-hidden">
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <motion.div
          className="absolute -top-24 left-1/2 -translate-x-1/2 w-[min(700px,92vw)] h-[400px] rounded-full bg-blue-500/5 blur-3xl avora-drift"
          animate={{ scale: [1, 1.04, 1], opacity: [0.5, 0.7, 0.5] }}
          transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>
      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          <SectionHeading
            label="Experience"
            title="A relationship that grows"
            description="AVORA learns your preferences, remembers what matters, and becomes more personal over time."
          />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 28, scale: 0.98 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.9, delay: 0.18, ease: [0.16, 1, 0.3, 1] }}
          className="mt-16 rounded-3xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl overflow-hidden hover-target hover-lift"
          whileHover={{ y: -4 }}
        >
          <ChatDemo />
        </motion.div>
      </div>
    </section>
  );
}

export default ExperienceSection;