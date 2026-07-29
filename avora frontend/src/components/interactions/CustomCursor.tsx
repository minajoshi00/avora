'use client';

import { useEffect, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

type CursorState = 'normal' | 'interactive' | 'button' | 'card' | 'click' | 'loading' | 'hidden';

export function CustomCursor() {
  const [state, setState] = useState<CursorState>('normal');
  const [isVisible, setIsVisible] = useState(false);
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const [clickEffect, setClickEffect] = useState<{ x: number; y: number } | null>(null);
  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);
  const ringX = useSpring(cursorX, { stiffness: 150, damping: 15, mass: 0.1 });
  const ringY = useSpring(cursorY, { stiffness: 150, damping: 15, mass: 0.1 });
  const trailX = useSpring(cursorX, { stiffness: 80, damping: 12, mass: 0.05 });
  const trailY = useSpring(cursorY, { stiffness: 80, damping: 12, mass: 0.05 });

  useEffect(() => {
    // Check for touch device and touch detection
    const checkTouch = () => {
      const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      setIsTouchDevice(hasTouch);
    };
    checkTouch();

    // Check for reduced motion preference with fallback
    let prefersReducedMotion = false;
    try {
      prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (e) {
      // Fallback for browsers without matchMedia support
      prefersReducedMotion = false;
    }
    
    if (prefersReducedMotion || isTouchDevice) {
      document.body.style.cursor = 'auto';
      return;
    }

    document.body.style.cursor = 'none';

    const handleMouseMove = (e: MouseEvent) => {
      cursorX.set(e.clientX);
      cursorY.set(e.clientY);
      if (!isVisible) setIsVisible(true);
    };

    const handleMouseEnter = () => setIsVisible(true);
    const handleMouseLeave = () => setIsVisible(false);

    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const tag = target.tagName;
      const isButton = tag === 'BUTTON' || !!target.closest('button');
      const isLink = tag === 'A' || !!target.closest('a');
      const isCard = !!target.closest('[role="button"]') || target.classList.contains('glass-panel') || !!target.closest('.group');
      const isInput = tag === 'INPUT' || tag === 'TEXTAREA';
      const isInteractive = target.classList.contains('hover-target');

      if (isButton || isLink) {
        setState('button');
      } else if (isCard || isInteractive) {
        setState('card');
      } else if (isInput) {
        setState('interactive');
      } else {
        setState('normal');
      }
    };

    const handleMouseDown = () => {
      setState('click');
      setClickEffect({ x: cursorX.get(), y: cursorY.get() });
      setTimeout(() => setClickEffect(null), 300);
    };

    const handleMouseUp = () => {
      setState('normal');
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('mouseenter', handleMouseEnter);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseover', handleMouseOver);
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.body.style.cursor = 'auto';
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseenter', handleMouseEnter);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseover', handleMouseOver);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isVisible, isTouchDevice, cursorX, cursorY]);

  if (!isVisible || isTouchDevice) return null;

  const getCoreSize = () => {
    switch (state) {
      case 'button': return 8;
      case 'card': return 6;
      case 'click': return 4;
      case 'interactive': return 6;
      default: return 5;
    }
  };

  const getRingSize = () => {
    switch (state) {
      case 'button': return 50;
      case 'card': return 40;
      case 'click': return 60;
      case 'interactive': return 35;
      default: return 30;
    }
  };

  const getRingBorderColor = () => {
    switch (state) {
      case 'button': return 'rgba(96, 165, 250, 0.9)';
      case 'card': return 'rgba(167, 139, 250, 0.7)';
      case 'click': return 'rgba(96, 165, 250, 0.5)';
      case 'interactive': return 'rgba(34, 211, 238, 0.7)';
      default: return 'rgba(96, 165, 250, 0.4)';
    }
  };

  const getGlowIntensity = () => {
    switch (state) {
      case 'button': return '0 0 30px rgba(96, 165, 250, 0.8), 0 0 60px rgba(96, 165, 250, 0.4)';
      case 'card': return '0 0 20px rgba(167, 139, 250, 0.6), 0 0 40px rgba(167, 139, 250, 0.3)';
      case 'click': return '0 0 40px rgba(96, 165, 250, 0.9), 0 0 80px rgba(96, 165, 250, 0.5)';
      case 'interactive': return '0 0 20px rgba(34, 211, 238, 0.5), 0 0 40px rgba(34, 211, 238, 0.2)';
      default: return '0 0 15px rgba(96, 165, 250, 0.4), 0 0 30px rgba(96, 165, 250, 0.2)';
    }
  };

  const coreSize = getCoreSize();
  const ringSize = getRingSize();

  return (
    <>
      {/* Trail ring (slowest) */}
      <motion.div
        className="fixed top-0 left-0 pointer-events-none z-[999997]"
        style={{
          x: trailX,
          y: trailY,
          width: ringSize * 1.5,
          height: ringSize * 1.5,
          marginLeft: -(ringSize * 1.5) / 2,
          marginTop: -(ringSize * 1.5) / 2,
        }}
      >
        <div
          className="w-full h-full rounded-full"
          style={{
            border: '1px solid rgba(96, 165, 250, 0.1)',
            background: 'rgba(96, 165, 250, 0.02)',
            transition: 'all 0.3s ease',
          }}
        />
      </motion.div>

      {/* Main ring */}
      <motion.div
        className="fixed top-0 left-0 pointer-events-none z-[999998]"
        style={{
          x: ringX,
          y: ringY,
          width: ringSize,
          height: ringSize,
          marginLeft: -ringSize / 2,
          marginTop: -ringSize / 2,
        }}
      >
        <div
          className="w-full h-full rounded-full border transition-all duration-300"
          style={{
            borderColor: getRingBorderColor(),
            background: state === 'button' || state === 'card'
              ? 'rgba(96, 165, 250, 0.06)'
              : 'transparent',
            backdropFilter: state === 'button' ? 'blur(8px)' : 'none',
            boxShadow: getGlowIntensity(),
            transform: state === 'click' ? 'scale(1.2)' : 'scale(1)',
          }}
        />
      </motion.div>

      {/* Core dot */}
      <motion.div
        className="fixed top-0 left-0 pointer-events-none z-[999999]"
        style={{
          x: cursorX,
          y: cursorY,
          width: coreSize,
          height: coreSize,
          marginLeft: -coreSize / 2,
          marginTop: -coreSize / 2,
        }}
      >
        <div
          className="w-full h-full rounded-full"
          style={{
            background: 'linear-gradient(135deg, #60a5fa, #a78bfa)',
            boxShadow: getGlowIntensity(),
            transform: state === 'click' ? 'scale(0.8)' : 'scale(1)',
            transition: 'transform 0.15s ease',
          }}
        />
      </motion.div>

      {/* Click ripple effect */}
      {clickEffect && (
        <motion.div
          className="fixed pointer-events-none z-[999996]"
          style={{
            left: clickEffect.x,
            top: clickEffect.y,
            width: 0,
            height: 0,
          }}
          initial={{ width: 0, height: 0, opacity: 0.6 }}
          animate={{
            width: 60,
            height: 60,
            opacity: 0,
            marginLeft: -30,
            marginTop: -30,
          }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        >
          <div
            className="w-full h-full rounded-full"
            style={{
              border: '1px solid rgba(96, 165, 250, 0.6)',
              background: 'rgba(96, 165, 250, 0.1)',
            }}
          />
        </motion.div>
      )}
    </>
  );
}