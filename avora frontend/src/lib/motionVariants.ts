/**
 * AVORA Motion System — reused across entire site
 * Based on Hero benchmark: ease [0.16,1,0.3,1], duration 0.7-0.9, stagger 0.08-0.12
 * All transforms are GPU-friendly (opacity, translate, scale).
 * Respects prefers-reduced-motion via JS check where needed.
 */

export const easePremium = [0.16, 1, 0.3, 1] as const;

// Container that staggers children
export const staggerContainer = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.09,
      delayChildren: 0.12,
    },
  },
};

export const staggerContainerFast = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.08,
    },
  },
};

// Item variants — heading / text / card
export const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: easePremium },
  },
};

export const fadeUpSoft = {
  hidden: { opacity: 0, y: 18, filter: 'blur(6px)' as any },
  show: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)' as any,
    transition: { duration: 0.8, ease: easePremium },
  },
};

export const fadeLeft = {
  hidden: { opacity: 0, x: 18 },
  show: { opacity: 1, x: 0, transition: { duration: 0.65, ease: easePremium } },
};

export const fadeRight = {
  hidden: { opacity: 0, x: -18 },
  show: { opacity: 1, x: 0, transition: { duration: 0.65, ease: easePremium } },
};

export const scaleIn = {
  hidden: { opacity: 0, scale: 0.96 },
  show: { opacity: 1, scale: 1, transition: { duration: 0.6, ease: easePremium } },
};

// Card grid item
export const cardIn = {
  hidden: { opacity: 0, y: 18, scale: 0.98 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.6, ease: easePremium },
  },
};

// Utility to create delay variant
export const withDelay = (variant: any, delay: number) => ({
  hidden: variant.hidden,
  show: { ...variant.show, transition: { ...(variant.show.transition || {}), delay } },
});

// Hover presets (to spread onto motion.div)
export const hoverLift = {
  y: -4,
  scale: 1.01,
  transition: { duration: 0.25, ease: easePremium },
};

export const hoverScale = {
  scale: 1.03,
  transition: { duration: 0.25, ease: easePremium },
};

export const tapScale = { scale: 0.98 };
