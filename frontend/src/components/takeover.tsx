'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';

const takeoverDialogue = [
  {
    step: 0,
    text: "Alright... you're letting me take over?",
  },
  {
    step: 1,
    text: "Don't click anything. I've got you.",
  },
  {
    step: 2,
    text: "This is what you're looking at — not just another AI chatbot.",
  },
  {
    step: 3,
    text: "And here's where I understand context, intent, and what you're actually trying to accomplish.",
  },
  {
    step: 4,
    text: "Here's the ecosystem I connect with around you.",
  },
  {
    step: 5,
    text: "These are the modes I can adapt to — coding, learning, gaming, productivity.",
  },
  {
    step: 6,
    text: "And these are the people who built me.",
  },
  {
    step: 7,
    text: "And finally... this is where you get me.",
  },
];

const steps = [
  { id: 'hero', label: 'Hero' },
  { id: 'intelligence', label: 'Intelligence' },
  { id: 'ecosystem', label: 'Ecosystem' },
  { id: 'modes', label: 'Modes' },
  { id: 'developer', label: 'Developer' },
  { id: 'download', label: 'Download' },
];

export function TakeOver() {
  const [active, setActive] = useState(false);
  const [step, setStep] = useState(0);
  const [showDialogue, setShowDialogue] = useState(false);
  const [exiting, setExiting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  const scrollRef = useRef<number | null>(null);
  const timeoutRef = useRef<number | null>(null);

  const handleExit = useCallback(() => {
    setExiting(true);
    setActive(false);
    setStep(0);
    setShowDialogue(false);
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    document.removeEventListener('scroll', handleUserScroll);
    setTimeout(() => {
      setExiting(false);
    }, 300);
  }, []);

  useEffect(() => {
    if (active) {
      document.body.style.scrollBehavior = 'auto';
    } else {
      document.body.style.scrollBehavior = '';
      document.removeEventListener('scroll', handleUserScroll);
    }
  }, [active]);

  const handleUserScroll = useCallback(() => {
    setIsPaused(true);
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (active) {
      document.addEventListener('scroll', handleUserScroll, { passive: true });
    } else {
      document.removeEventListener('scroll', handleUserScroll);
    }
    return () => document.removeEventListener('scroll', handleUserScroll);
  }, [active]);

  const navigateToStep = useCallback((targetStep: number) => {
    setStep(targetStep);
    setShowDialogue(true);

    const targetInfo = steps[targetStep];
    const targetId = targetInfo ? targetInfo.id : null;
    const targetElement = targetId ? document.getElementById(targetId) : null;

    if (targetElement) {
      document.body.style.scrollBehavior = 'auto';
      const targetPosition = targetElement.offsetTop - 72;
      scrollRef.current = window.setTimeout(() => {
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth',
        });
        document.body.style.scrollBehavior = 'auto';
        scrollRef.current = null;
      }, 100);
    }
  }, []);

  const handleResume = useCallback(() => {
    setIsPaused(false);
    if (step < steps.length - 1) {
      timeoutRef.current = window.setTimeout(() => {
        setShowDialogue(false);
        navigateToStep(step + 1);
      }, 100);
    }
  }, [step, navigateToStep]);

  const startTakeover = useCallback(() => {
    setActive(true);
    setStep(0);
    setShowDialogue(true);
    setExiting(false);
    document.body.style.scrollBehavior = 'auto';
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (scrollRef.current !== null) {
      window.clearTimeout(scrollRef.current);
      scrollRef.current = null;
    }
    document.removeEventListener('scroll', handleUserScroll);
  }, []);

  const nextStep = useCallback(() => {
    if (step < steps.length - 1) {
      setStep(prev => prev + 1);
      setShowDialogue(true);
    } else {
      setActive(false);
      setExiting(true);
    }
  }, []);

  const prevStep = useCallback(() => {
    setStep(prev => Math.max(0, prev - 1));
    setShowDialogue(true);
  }, []);

  useEffect(() => {
    if (active && step < steps.length && showDialogue) {
      timeoutRef.current = window.setTimeout(() => {
        setShowDialogue(false);

        if (step < steps.length - 1) {
          navigateToStep(step + 1);
        } else {
          setActive(false);
          setExiting(true);
        }
      }, 2000);
      return () => {
        if (timeoutRef.current !== null) {
          window.clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }
      };
    }
  }, [active, step, showDialogue, navigateToStep]);

  // Button render - always show the Take Over button when not in experience
  const buttonLabel = active ? 'EXITING' : '❈ LET AVORA TAKE OVER';

  if (!active || exiting) {
    return (
      <motion.button
        className="fixed bottom-6 right-6 z-50 p-3 rounded-full glass-panel border border-white/[0.08] bg-white/[0.03] backdrop-blur-xl hover:border-white/[0.15] transition-all cursor-pointer"
        onClick={startTakeover}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        aria-label="Let AVORA Take Over"
      >
        {buttonLabel}
      </motion.button>
    );
  }

  // Takeover experience is active - show guided experience overlay
  const isLastStep = step >= steps.length - 1;

  return (
    <div className="fixed inset-0 z-50 pointer-events-auto">
      {/* Semi-transparent overlay */}
      <motion.div
        className="fixed inset-0 bg-black/70 pointer-events-none"
        initial={{ opacity: 0}}
        animate={{ opacity: 1}}
        exit={{ opacity: 0}}
        transition={{duration: 0.3}}
      />

      {/* Guided experience panel */}
      <div className="relative z-10 max-w-4xl mx-auto p-6 md:p-12 text-white">
        {/* Progress */}
        <div className="mb-4 h-1 rounded-full bg-white/[0.06] overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 transition-all duration-300"
            style={{width: `${((step + 1) / steps.length) * 100}%`}}
          />
        </div>

        <div className="mb-4 text-sm text-gray-400 uppercase tracking-wider">
          Step {step + 1} of {steps.length}
        </div>

        {/* Dialogue */}
        {showDialogue && step < takeoverDialogue.length && (
          <motion.p
            initial={{opacity: 0, y: 20}}
            animate={{opacity: 1, y: 0}}
            transition={{duration: 0.5, ease: [0.16, 1, 0.3, 1]}}
            className="mb-4 text-lg leading-relaxed"
          >
            <p>{takeoverDialogue[step].text}</p>
          </motion.p>
        )}

        {/* Pause indicator */}
        {isPaused && (
          <div className="mb-4 text-center text-white/80 text-sm uppercase tracking-wider">
            <p>Take Over paused</p>
            <button
              className="mt-2 rounded-xl bg-white/[0.02] border border-white/[0.06] px-4 py-2 text-sm hover:text-white hover:border-white/[0.15] transition-all"
              onClick={handleResume}
            >
              Resume
            </button>
          </div>
        )}

        {/* Navigation controls */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-white/[0.04]">
          {step > 0 && !showDialogue && (
            <motion.button
              whileHover={{scale: 1.05, y: -2}}
              whileTap={{scale: 0.95}}
              className="flex-1 py-2 rounded-xl bg-white/[0.02] border border-white/[0.06] text-sm text-gray-400 hover:text-white transition-all"
              onClick={prevStep}
            >
              ⎪ Previous
            </motion.button>
          )}

          {isLastStep && !showDialogue && (
            <motion.button
              whileHover={{scale: 1.05, y: -2}}
              whileTap={{scale: 0.95}}
              className="flex-1 py-2 rounded-xl bg-white/[0.02] border border-white/[0.06] text-sm text-gray-400 hover:text-white transition-all"
              onClick={handleExit}
            >
              Exit AVORA
            </motion.button>
          )}

          {showDialogue && (
            <motion.button
              whileHover={{scale: 1.05, y: -2}}
              whileTap={{scale: 0.95}}
              className="flex-1 py-2 rounded-xl bg-white/[0.02] border border-white/[0.06] text-sm text-gray-400 hover:text-white transition-all"
              onClick={() => setShowDialogue(false)}
            >
              Skip
            </motion.button>
          )}

          {(!showDialogue && !isLastStep) && (
            <motion.button
              whileHover={{scale: 1.05, y: -2}}
              whileTap={{scale: 0.95}}
              className="flex-1 py-2 rounded-xl bg-white/[0.02] border border-white/[0.06] text-sm text-gray-400 hover:text-white transition-all"
              onClick={nextStep}
            >
              Next →
            </motion.button>
          )}
        </div>

        {/* Step indicators */}
        <div className="mt-4 text-xs text-gray-400 uppercase tracking-wider">
          {steps.map((s, i) => (
            <span
              key={s.id}
              className={`mr-1 px-1 py-0.5 rounded text-[0.85px] ${i <= step ? 'text-white bg-blue-500/20' : 'text-gray-400/50'}`}
            >
              {s.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TakeOver;