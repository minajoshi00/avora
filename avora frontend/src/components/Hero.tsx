'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Play, Sparkles } from 'lucide-react';
import { Button } from './ui/Button';
import { GlassModuleCards } from './ui/GlassModuleCards';

export function Hero() {
  const scrollToDownload = () => {
    const section = document.getElementById('download');
    if (section) section.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#0a0a0f]">
      {/* Subtle animated gradient background */}
      <motion.div
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at 30% 20%, rgba(96,165,250,0.15) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(167,139,250,0.1) 0%, transparent 50%)',
        }}
        transition={{ duration: 20, ease: 'linear' }}
        animate={{ x: -100 }}
      />

      <div className="relative z-10 max-w-6xl mx-auto px-6 text-center">
        {/* Cinematic eyebrow */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{
            duration: 0.8,
            delay: 0.1,
            ease: [0.16, 1, 0.3, 1],
            type: 'spring',
            stiffness: 200,
            damping: 20
          }}
          whileHover={{ scale: 1.05, transition: { duration: 0.2 } }}
          className="magnetic inline-flex items-center gap-2.5 px-4 py-2 rounded-full border border-white/[0.1] bg-white/[0.04] backdrop-blur-md mb-10 hover-target group"
        >
          <motion.div
            animate={{ rotate: [0, 360] }}
            transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
            className="relative"
          >
            <Sparkles size={14} className="text-blue-400" />
          </motion.div>
          <span className="text-[10px] font-medium text-gray-400 tracking-[0.25em] uppercase">
            Introducing AVORA
          </span>
          <motion.span
            className="w-1 h-1 rounded-full bg-emerald-400"
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </motion.div>

        {/* Hero headline - refined typography */}
        <div className="space-y-4">
          <div className="overflow-hidden">
            <motion.h1
              initial={{ opacity: 0, y: 60, filter: 'blur(10px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              transition={{
                duration: 1.2,
                delay: 0.3,
                ease: [0.16, 1, 0.3, 1]
              }}
              className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold text-white tracking-tight leading-[0.9]"
            >
              Meet AVORA
            </motion.h1>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 40, filter: 'blur(8px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            transition={{ duration: 1, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <p className="text-xl sm:text-2xl md:text-3xl lg:text-4xl text-gray-400 font-light tracking-wide">
              An intelligence that grows with you.
            </p>
          </motion.div>
        </div>

        {/* Premium description */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="mt-10"
        >
          <div className="max-w-xl mx-auto space-y-3">
            <p className="text-base sm:text-lg text-gray-300 leading-relaxed">
              Not another chatbot. A new kind of intelligence that understands
              your context, remembers what matters, and evolves alongside you.
            </p>
            <motion.div
              className="flex items-center justify-center gap-6 text-xs text-gray-500 pt-2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.2 }}
            >
              <span className="flex items-center gap-2">
                <div className="w-1 h-1 rounded-full bg-emerald-400" />
                Context-aware
              </span>
              <span className="flex items-center gap-2">
                <div className="w-1 h-1 rounded-full bg-blue-400" />
                Persistent memory
              </span>
              <span className="flex items-center gap-2">
                <div className="w-1 h-1 rounded-full bg-purple-400" />
                Continuously evolving
              </span>
            </motion.div>
          </div>
        </motion.div>

        {/* Premium CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.9, ease: [0.16, 1, 0.3, 1] }}
          className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <motion.div
            whileHover={{ scale: 1.05, y: -3 }}
            whileTap={{ scale: 0.95 }}
            className="hover-target relative group"
          >
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl opacity-20 group-hover:opacity-40 blur transition-opacity" />
            <Button
              size="lg"
              icon={<ArrowRight size={18} />}
              magnetic
              onClick={scrollToDownload}
              className="relative shadow-[0_0_30px_rgba(96,165,250,0.3)]"
            >
              Experience AVORA
            </Button>
          </motion.div>
          <motion.div
            whileHover={{ scale: 1.05, y: -3 }}
            whileTap={{ scale: 0.95 }}
            className="hover-target"
          >
            <Button
              variant="outline"
              size="lg"
              icon={<Play size={18} />}
              magnetic
              className="border-white/[0.15] hover:border-white/[0.3] hover:bg-white/[0.05]"
            >
              Watch the film
            </Button>
          </motion.div>
        </motion.div>

        {/* Glassmorphism module cards */}
        <GlassModuleCards />

        {/* Scroll invitation */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.5 }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3"
        >
          <span className="text-[10px] uppercase tracking-widest text-gray-500">
            Scroll to explore
          </span>
          <motion.div
            animate={{ 
              y: [0, 8, 0],
              opacity: [0.3, 0.7, 0.3]
            }}
            transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
            className="w-px h-10 bg-gradient-to-b from-blue-500/60 via-purple-500/40 to-transparent"
          />
        </motion.div>
      </div>
    </section>
  );
}

export default Hero;