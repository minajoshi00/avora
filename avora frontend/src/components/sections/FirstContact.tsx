'use client';

import { motion } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';

export function FirstContact() {
  return (
    <section className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="text-center"
        >
          <SectionHeading
            label="First Contact"
            title="Not another chatbot"
            description="This is not a search box with a personality. This is an intelligence that is aware of you."
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 30 }}
          whileInView={{ opacity: 1, scale: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="mt-16 flex flex-col items-center gap-8"
        >
          <motion.div
            whileHover={{ scale: 1.05 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className="hover-target"
          >
            <InteractiveAvoraCore state="listening" size={200} />
          </motion.div>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-gray-500 max-w-lg leading-relaxed"
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