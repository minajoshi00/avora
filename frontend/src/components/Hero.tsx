'use client';

import { useRef } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { Button } from './ui/Button';
import { InteractiveBackground } from './ui/InteractiveBackground';
import { AvoraScene } from './hero/AvoraScene';
import { useVisualMode } from './ui/VisualModeProvider';

export function Hero() {
  const heroRef = useRef<HTMLElement>(null);
  const { config, reducedMotion } = useVisualMode();

  const parallaxScale = config.parallaxIntensity;
  const mouseX = useSpring(useMotionValue(0), { stiffness: 40 * parallaxScale, damping: 20 });
  const mouseY = useSpring(useMotionValue(0), { stiffness: 40 * parallaxScale, damping: 20 });

  const handleMouseMove = (e: React.MouseEvent<HTMLElement>) => {
    if (!heroRef.current) return;
    const rect = heroRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    mouseX.set(x * 12 * parallaxScale);
    mouseY.set(y * 12 * parallaxScale);
  };

  const animScale = Math.min(config.animationSpeed, 1.2);
  const delay = (base: number) => base * (1.4 - config.animationSpeed) * 0.7;

  const scrollToDownload = () => {
    const section = document.getElementById('download');
    if (section) section.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section
      id="hero"
      ref={heroRef}
      className="relative min-h-screen flex items-center overflow-hidden"
      onMouseMove={handleMouseMove}
      style={{
        background: 'radial-gradient(ellipse at center top, #0a0a12, #040408 50%, #000000 80%)',
      }}
    >
      <InteractiveBackground quality={config.particleOpacity > 0.7 ? 'high' : config.particleOpacity > 0.4 ? 'medium' : 'low'} />

      <div className="relative z-10 w-full mx-auto">
        <div className="container mx-auto px-6 py-20 lg:py-24 xl:py-28">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-y-8 lg:gap-x-8 xl:gap-x-12">
            <div className="lg:col-span-5 xl:col-span-5 flex flex-col justify-center">
              <motion.h1
                initial={{ opacity: 0, y: 50, filter: 'blur(12px)' }}
                animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                transition={{
                  duration: 1.2 * animScale,
                  delay: delay(0.2),
                  ease: [0.16, 1, 0.3, 1],
                }}
                className="text-6xl sm:text-7xl md:text-8xl lg:text-9xl xl:text-9xl font-normal text-white tracking-[-0.03em] leading-[0.9]"
              >
                AVORA
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 * animScale, delay: delay(0.4), ease: [0.16, 1, 0.3, 1] }}
                className="mt-6 text-xl sm:text-2xl md:text-2xl text-gray-300 font-light tracking-wider leading-relaxed"
              >
                Your AI Desktop Companion
              </motion.p>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 * animScale, delay: delay(0.6), ease: [0.16, 1, 0.3, 1] }}
                className="mt-8 text-base sm:text-lg text-gray-400 leading-relaxed max-w-md"
              >
                An intelligent companion that understands your workflow,
                helps you get things done, and stays with you while you work.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 * animScale, delay: delay(0.8), ease: [0.16, 1, 0.3, 1] }}
                className="mt-12 flex flex-col sm:flex-row items-start sm:items-center gap-4"
              >
                <motion.div
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.97 }}
                >
                  <Button
                    size="lg"
                    icon={<ArrowRight size={18} />}
                    magnetic
                    onClick={scrollToDownload}
                    className="font-medium text-sm tracking-wider hover:drop-shadow-[0_0_10px_rgba(167,139,250,0.5)]"
                  >
                    Get AVORA
                  </Button>
                </motion.div>

                <motion.button
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.8, delay: delay(1.0) }}
                  className="text-sm text-gray-500 hover:text-gray-300 transition-colors duration-200 flex items-center gap-2 group"
                >
                  <span className="w-5 h-px bg-gray-600 group-hover:bg-gray-400 transition-colors duration-200" />
                  <span className="text-xs font-medium tracking-widest uppercase">
                    Let AVORA Take Over
                  </span>
                </motion.button>
              </motion.div>
            </div>

            <div className="lg:col-span-7 xl:col-span-7 flex items-center justify-center lg:justify-end">
              <motion.div
                initial={{ opacity: 0, scale: 0.9, filter: 'blur(5px)' }}
                animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
                transition={{
                  duration: 1.4 * animScale,
                  delay: delay(0.6),
                  ease: [0.16, 1, 0.3, 1],
                }}
                className="relative w-[340px] h-[340px] sm:w-[400px] sm:h-[400px] md:w-[460px] md:h-[460px] lg:w-[500px] lg:h-[500px] xl:w-[540px] xl:h-[540px]"
              >
                <div
                  className="absolute -inset-1/2 blur-3xl pointer-events-none"
                  style={{
                    opacity: 0.12 * config.glowIntensity,
                    background:
                      'radial-gradient(circle, rgba(108, 92, 231, 0.2) 0%, rgba(167, 139, 250, 0.12) 40%, transparent 70%)',
                  }}
                />

                <AvoraScene
                  reducedMotion={reducedMotion}
                  quality={config.particleOpacity > 0.7 ? 'high' : config.particleOpacity > 0.4 ? 'medium' : 'low'}
                  className="w-full h-full"
                />
              </motion.div>
            </div>
          </div>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 * animScale, delay: delay(1.5) }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 text-[10px] uppercase tracking-widest text-gray-500"
      >
        Scroll
      </motion.div>
    </section>
  );
}

export default Hero;