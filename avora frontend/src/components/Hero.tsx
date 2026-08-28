'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Play, Sparkles } from 'lucide-react';
import { Button } from './ui/Button';
import { HeroCanvas } from './hero/HeroCanvas';

export function Hero() {
  const scrollToDownload = () => {
    const section = document.getElementById('download');
    if (section) section.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="relative min-h-[92vh] flex items-center justify-center overflow-hidden bg-transparent isolate">
      {/* Lightweight alive background — canvas + soft gradients */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <HeroCanvas />
        {/* extra soft vignette to keep text readable */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#08080e]/55" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#0a0b14]/50 via-transparent to-[#0a0b14]/50" />
      </div>

      <div className="relative z-10 w-full max-w-3xl mx-auto px-6 text-center py-20 sm:py-24">
        {/* Eyebrow — AVORA branding */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] backdrop-blur-md mb-8 sm:mb-10 hover-target"
        >
          <Sparkles size={13} className="text-blue-400" />
          <span className="text-[11px] font-medium text-gray-300 tracking-[0.22em] uppercase">
            Introducing AVORA
          </span>
          <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
        </motion.div>

        {/* Headline — focal point */}
        <div className="space-y-5">
          <motion.h1
            initial={{ opacity: 0, y: 28, filter: 'blur(8px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            transition={{ duration: 0.9, delay: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className="text-[40px] sm:text-6xl md:text-7xl font-bold text-white tracking-[-0.04em] leading-[0.92] text-balance"
          >
            Meet AVORA
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.45, ease: [0.16, 1, 0.3, 1] }}
            className="text-[18px] sm:text-2xl md:text-[28px] text-gray-300 font-light tracking-[-0.02em] leading-tight"
          >
            An intelligence that grows with you.
          </motion.p>
        </div>

        {/* Single concise supporting line — breathing room */}
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.58, ease: [0.16, 1, 0.3, 1] }}
          className="mx-auto mt-7 sm:mt-8 max-w-[560px] text-[15px] sm:text-[16px] leading-relaxed text-gray-400 text-balance"
        >
          Not another chatbot. A companion that understands your context, remembers what matters, and evolves with you.
        </motion.p>

        {/* CTAs — generous space */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.72, ease: [0.16, 1, 0.3, 1] }}
          className="mt-9 sm:mt-11 flex flex-col sm:flex-row items-center justify-center gap-3.5"
        >
          <motion.div whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }} className="hover-target relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500/30 to-purple-500/30 rounded-xl opacity-0 group-hover:opacity-40 blur-md transition-opacity" />
            <Button
              size="lg"
              icon={<ArrowRight size={17} />}
              onClick={scrollToDownload}
              className="relative min-w-[184px] shadow-[0_10px_30px_rgba(59,130,246,0.22)]"
            >
              Experience AVORA
            </Button>
          </motion.div>
          <motion.div whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }} className="hover-target">
            <Button
              variant="outline"
              size="lg"
              icon={<Play size={16} />}
              className="min-w-[158px] border-white/[0.14] bg-white/[0.02] hover:bg-white/[0.06] hover:border-white/[0.22] text-gray-200"
            >
              Watch the film
            </Button>
          </motion.div>
        </motion.div>

        {/* Whitespace — no cards/badges, let animation breathe */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 1.1 }}
          className="mt-16 flex flex-col items-center gap-2"
        >
          <span className="text-[10px] uppercase tracking-[0.18em] text-gray-500/70">
            Scroll to explore
          </span>
          <motion.div
            animate={{ y: [0, 6, 0], opacity: [0.35, 0.65, 0.35] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
            className="w-px h-8 bg-gradient-to-b from-blue-400/60 to-transparent"
          />
        </motion.div>
      </div>
    </section>
  );
}

export default Hero;