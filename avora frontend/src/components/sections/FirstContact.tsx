'use client';

import { motion } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';

export function FirstContact() {
  return (
    <section className="relative py-32 overflow-hidden">
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(700px,92vw)] h-[400px] rounded-full bg-blue-500/5 blur-3xl avora-drift"
          animate={{ scale: [1, 1.06, 1], opacity: [0.4, 0.65, 0.4] }}
          transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>
      <div className="max-w-4xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="text-center"
        >
          <SectionHeading
            label="First Contact"
            title="Not another chatbot"
            description="This is not a search box with a personality. This is an intelligence that is aware of you."
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 20 }}
          whileInView={{ opacity: 1, scale: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.9, delay: 0.16, ease: [0.16, 1, 0.3, 1] }}
          className="mt-16 flex flex-col items-center gap-8"
        >
          <motion.div
            className="avora-float hover-target"
            whileHover={{ scale: 1.04 }}
            transition={{ type: 'spring', stiffness: 280, damping: 18 }}
          >
            <InteractiveAvoraCore state="listening" size={200} />
          </motion.div>
          <motion.p
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="text-gray-400 max-w-lg leading-relaxed text-center"
          >
            When you speak, AVORA listens. When you type, AVORA understands. When you share,
            AVORA remembers. This is a relationship, not a transaction.
          </motion.p>
        </motion.div>
      </div>
    </section>
  );
}

export default FirstContact;