'use client';

import { useEffect, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';
import { useVisualMode } from '../ui/VisualModeProvider';

type CursorState = 'normal' | 'interactive' | 'button' | 'card' | 'click' | 'loading' | 'hidden';

export function CustomCursor() {
  const [state, setState] = useState<CursorState>('normal');
  const [isVisible, setIsVisible] = useState(false);
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const [clickEffect, setClickEffect] = useState<{ x: number; y: number } | null>(null);
  const { config } = useVisualMode();

  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);
  const ringX = useSpring(cursorX, { stiffness: 150, damping: 15, mass: 0.1 });
  const ringY = useSpring(cursorY, { stiffness: 150, damping: 15, mass: 0.1 });
  const trailX = useSpring(cursorX, { stiffness: 80, damping: 12, mass: 0.05 });
  const trailY = useSpring(cursorY, { stiffness: 80, damping: 12, mass: 0.05 });

  useEffect(() => {
    const checkTouch = () => {
      const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      setIsTouchDevice(hasTouch);
    };
    checkTouch();

    let prefersReducedMotionVal = false;
    try {
      prefersReducedMotionVal = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch {
      prefersReducedMotionVal = false;
    }

    if (prefersReducedMotionVal || isTouchDevice) {
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
      const isCard =
        !!target.closest('[role="button"]') ||
        target.classList.contains('glass-panel') ||
        !!target.closest('.group');
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
  }, [isVisible, isTouchDevice, cursorX, cursorY, config]);

  if (!isVisible || isTouchDevice) return null;

  // Scale sizes and glow by mode config
  const glowScale = config.glowIntensity;

  const getCoreSize = (): number => {
    switch (state) {
      case 'button':
        return 8;
      case 'card':
        return 6;
      case 'click':
        return 4;
      case 'interactive':
        return 6;
      default:
        return 5;
    }
  };

  const getRingSize = (): number => {
    let base: number;
    switch (state) {
      case 'button':
        base = 50;
        break;
      case 'card':
        base = 40;
        break;
      case 'click':
        base = 60;
        break;
      case 'interactive':
        base = 35;
        break;
      default:
        base = 30;
        break;
    }
    // Reduce ring size in calm mode
    return base * (0.7 + 0.3 * glowScale);
  };

  const getRingBorderColor = (): string => {
    switch (state) {
      case 'button':
        return `rgba(96, 165, 250, ${0.9 * glowScale})`;
      case 'card':
        return `rgba(167, 139, 250, ${0.7 * glowScale})`;
      case 'click':
        return `rgba(96, 165, 250, ${0.5 * glowScale})`;
      case 'interactive':
        return `rgba(34, 211, 238, ${0.7 * glowScale})`;
      default:
        return `rgba(96, 165, 250, ${0.4 * glowScale})`;
    }
  };

  const getGlowIntensity = (): string => {
    let multiplier: number;
    switch (state) {
      case 'button':
        multiplier = 0.8;
        break;
      case 'card':
        multiplier = 0.6;
        break;
      case 'click':
        multiplier = 0.9;
        break;
      case 'interactive':
        multiplier = 0.5;
        break;
      default:
        multiplier = 0.4;
        break;
    }
    // Scale by mode config
    const s = multiplier * glowScale;
    return `0 0 ${20 * s}px rgba(96, 165, 250, ${s}), 0 0 ${40 * s}px rgba(96, 165, 250, ${s * 0.5})`;
  };

  const coreSize = getCoreSize();
  const ringSize = getRingSize();

  // Trail ring is always subtle
  const trailSize = ringSize * 1.5;

  return (
    <>
      {/* Trail ring (subtle) */}
      <motion.div
        className="fixed top-0 left-0 pointer-events-none z-[999997]"
        style={{
          x: trailX,
          y: trailY,
          width: trailSize,
          height: trailSize,
          marginLeft: -trailSize / 2,
          marginTop: -trailSize / 2,
        }}
      >
        <div
          className="w-full h-full rounded-full"
          style={{
            border: `1px solid rgba(96, 165, 250, ${0.1 * glowScale})`,
            background: `rgba(96, 165, 250, ${0.02 * glowScale})`,
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
            background:
              state === 'button' || state === 'card'
                ? `rgba(96, 165, 250, ${0.06 * glowScale})`
                : 'transparent',
            backdropFilter: state === 'button' ? `blur(${8 * glowScale}px)` : 'none',
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

      {/* Click ripple effect — subdued in calm mode */}
      {clickEffect && (
        <motion.div
          className="fixed pointer-events-none z-[999996]"
          style={{
            left: clickEffect.x,
            top: clickEffect.y,
            width: 0,
            height: 0,
          }}
          initial={{ width: 0, height: 0, opacity: 0.6 * glowScale }}
          animate={{
            width: 60 * (0.7 + 0.3 * glowScale),
            height: 60 * (0.7 + 0.3 * glowScale),
            opacity: 0,
            marginLeft: -30 * (0.7 + 0.3 * glowScale),
            marginTop: -30 * (0.7 + 0.3 * glowScale),
          }}
          transition={{ duration: 0.3 * (1 / Math.max(0.5, config.transitionSpeed)), ease: 'easeOut' }}
        >
          <div
            className="w-full h-full rounded-full"
            style={{
              border: `1px solid rgba(96, 165, 250, ${0.6 * glowScale})`,
              background: `rgba(96, 165, 250, ${0.1 * glowScale})`,
            }}
          />
        </motion.div>
      )}
    </>
  );
}
