'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';
import { ArrowRight, Play, Sparkles } from 'lucide-react';
import { Button } from './ui/Button';
import { InteractiveBackground } from './ui/InteractiveBackground';
import { GlassModuleCards } from './ui/GlassModuleCards';
import { InteractiveAvoraCore } from './brand/InteractiveAvoraCore';

export function Hero() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const heroRef = useRef<HTMLElement>(null);

  const mouseX = useSpring(useMotionValue(0), { stiffness: 40, damping: 20 });
  const mouseY = useSpring(useMotionValue(0), { stiffness: 40, damping: 20 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!heroRef.current) return;
      const rect = heroRef.current.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      setMousePosition({ x, y });
      mouseX.set(x * 20);
      mouseY.set(y * 20);
    };

    const hero = heroRef.current;
    if (hero) {
      hero.addEventListener('mousemove', handleMouseMove, { passive: true });
      return () => hero.removeEventListener('mousemove', handleMouseMove);
    }
  }, [mouseX, mouseY]);

  const scrollToDownload = () => {
    const section = document.getElementById('download');
    if (section) section.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section
      ref={heroRef}
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
    >
      {/* Deep space base */}
      <div className="absolute inset-0 bg-[#0a0a0f]" />
      
      {/* 3D interactive universe background */}
      <InteractiveBackground />

      {/* Atmospheric gradient layer with mouse reactivity */}
      <motion.div
        className="absolute inset-0 opacity-50"
        style={{
          background: `radial-gradient(circle at ${50 + mousePosition.x * 20}% ${50 + mousePosition.y * 20}%, rgba(96,165,250,0.12) 0%, rgba(167,139,250,0.06) 35%, transparent 65%)`,
        }}
      />

      {/* Smart contrast scrim */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a0a0f]/60 via-[#0a0a0f]/20 to-[#0a0a0f]/70 pointer-events-none" />

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
          className="magnetic inline-flex items-center gap-2.5 px-4 py-2 rounded-full border border-white/[0.1] bg-white/[0.04] backdrop-blur-md mb-10 hover-target group shadow-[0_0_30px_rgba(96,165,250,0.1)]"
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

        {/* Interactive AVORA Core */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, delay: 1.4, ease: [0.16, 1, 0.3, 1] }}
          className="mt-16 relative inline-flex items-center justify-center"
          style={{ perspective: 1000 }}
        >
          <motion.div
            style={{
              x: mouseX,
              y: mouseY,
            }}
            transition={{ type: 'spring', stiffness: 40, damping: 20 }}
          >
            <InteractiveAvoraCore state="focused" size={120} />
          </motion.div>

          {/* Soft refined glow */}
          <div
            className="absolute inset-0 blur-3xl opacity-50 pointer-events-none"
            style={{
              background: 'radial-gradient(circle, rgba(96,165,250,0.6) 0%, rgba(167,139,250,0.35) 40%, transparent 70%)',
              transform: 'scale(2.5)',
            }}
          />
        </motion.div>

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