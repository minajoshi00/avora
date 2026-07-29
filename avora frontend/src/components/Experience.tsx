import { motion } from 'framer-motion';
import { SectionHeading } from './ui/SectionHeading';
import { ChatDemo } from './demos/ChatDemo';

export function Experience() {
  return (
    <section id="experience" className="relative py-32">
      <div className="max-w-7xl mx-auto px-6">
        <SectionHeading
          label="Experience"
          title="A relationship that grows"
          description="AVORA learns your preferences, remembers what matters, and becomes more personal over time."
        />
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-16 rounded-3xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl overflow-hidden hover-target"
        >
          <ChatDemo />
        </motion.div>
      </div>
    </section>
  );
}

export default Experience;