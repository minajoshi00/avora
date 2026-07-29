'use client';

import { motion } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';

export function Vision() {
  return (
    <section id="vision" className="relative py-32">
      <div className="max-w-5xl mx-auto px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
        >
          <SectionHeading
            label="Vision"
            title="The future of AI should feel more human"
            description="Powerful enough to think, gentle enough to understand, present enough to care."
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 30 }}
          whileInView={{ opacity: 1, scale: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="mt-16"
        >
          <motion.div
            whileHover={{ scale: 1.05 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className="hover-target inline-flex items-center justify-center"
          >
            <InteractiveAvoraCore state="excited" size={220} />
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-16 grid sm:grid-cols-3 gap-6 text-left"
        >
          {[
            { title: 'Understand', desc: 'Context, nuance, and unspoken meaning.' },
            { title: 'Communicate', desc: 'Natural dialogue, not keyword matching.' },
            { title: 'Help', desc: 'Think, create, learn, and live better.' },
          ].map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.6 + i * 0.15, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              whileHover={{ y: -8, scale: 1.02, transition: { duration: 0.3 } }}
              className="glass-card p-6 rounded-2xl hover-target group"
            >
              <div className="relative z-10">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                  <div className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500" />
                </div>
                <h3 className="text-white font-medium mb-2 group-hover:text-blue-300 transition-colors duration-300">{item.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{item.desc}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

export default Vision;