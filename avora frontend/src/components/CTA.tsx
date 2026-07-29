import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { Button } from './ui/Button';

export function CTA() {
  return (
    <section className="relative py-32 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-blue-500/3 blur-3xl" />
        <div className="absolute top-0 right-1/4 w-[300px] h-[300px] rounded-full bg-purple-500/3 blur-3xl" />
      </div>

      <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <motion.h2
            initial={{ opacity: 0, y: 30, filter: 'blur(10px)' }}
            whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            viewport={{ once: true }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-white tracking-tight leading-[0.95]"
          >
            Ready to meet your{' '}
            <span className="bg-gradient-to-r from-blue-400 via-blue-300 to-purple-400 bg-clip-text text-transparent">
              intelligence
            </span>
            ?
          </motion.h2>
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="mt-8 text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed"
        >
          Join the waitlist and be among the first to experience a new kind of intelligence — one that understands, remembers, and evolves with you.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <motion.div
            whileHover={{ scale: 1.05, y: -3 }}
            whileTap={{ scale: 0.95 }}
            className="relative group"
          >
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl opacity-20 group-hover:opacity-40 blur transition-opacity" />
            <Button
              size="lg"
              icon={<ArrowRight size={18} />}
              className="relative shadow-[0_0_30px_rgba(96,165,250,0.3)]"
              onClick={() => {
                const section = document.getElementById('download');
                if (section) section.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Experience AVORA
            </Button>
          </motion.div>
          <motion.div
            whileHover={{ scale: 1.05, y: -3 }}
            whileTap={{ scale: 0.95 }}
          >
            <Button
              variant="outline"
              size="lg"
              className="border-white/[0.15] hover:border-white/[0.3] hover:bg-white/[0.05]"
            >
              Learn More
            </Button>
          </motion.div>
        </motion.div>

        {/* Trust indicators */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="mt-16 flex items-center justify-center gap-6 text-xs text-gray-500"
        >
          <div className="flex items-center gap-2">
            <div className="w-1 h-1 rounded-full bg-emerald-400" />
            Free to use
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1 h-1 rounded-full bg-blue-400" />
            Privacy first
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1 h-1 rounded-full bg-purple-400" />
            Continuously evolving
          </div>
        </motion.div>
      </div>
    </section>
  );
}
