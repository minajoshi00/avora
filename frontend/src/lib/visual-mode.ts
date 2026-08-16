/**
 * AVORA Visual Mode System
 *
 * Centralized configuration controlling visual intensity for Cinematic vs Calm modes.
 * Cinematic = full WOW experience. Calm = reduced intensity (~40-50%).
 *
 * The mode is persisted to localStorage and respects prefers-reduced-motion.
 */

export type VisualMode = 'cinematic' | 'calm';

export interface VisualConfig {
  /** Particle density multiplier (0-1) */
  particleDensity: number;
  /** Particle opacity multiplier (0-1) */
  particleOpacity: number;
  /** Particle movement speed multiplier */
  particleSpeed: number;
  /** Glow / bloom intensity multiplier (0-1) */
  glowIntensity: number;
  /** Bloom strength multiplier (0-1) */
  bloomStrength: number;
  /** Camera/mouse parallax intensity (0-1) */
  parallaxIntensity: number;
  /** Mouse interaction sensitivity (0-1) */
  mouseSensitivity: number;
  /** Animation speed multiplier (0-1) */
  animationSpeed: number;
  /** Background movement intensity (0-1) */
  backgroundMovement: number;
  /** Lighting intensity multiplier (0-1) */
  lightingIntensity: number;
  /** Shooting star frequency (0-1) */
  shootingStarFrequency: number;
  /** Neural node count multiplier (0-1) */
  neuralDensity: number;
  /** Blur strength multiplier (0-1) */
  blurStrength: number;
  /** Overall transition duration multiplier */
  transitionSpeed: number;
}

const CINEMATIC_CONFIG: VisualConfig = {
  particleDensity: 1.0,
  particleOpacity: 1.0,
  particleSpeed: 1.0,
  glowIntensity: 1.0,
  bloomStrength: 1.0,
  parallaxIntensity: 1.0,
  mouseSensitivity: 1.0,
  animationSpeed: 1.0,
  backgroundMovement: 1.0,
  lightingIntensity: 1.0,
  shootingStarFrequency: 1.0,
  neuralDensity: 1.0,
  blurStrength: 1.0,
  transitionSpeed: 1.0,
};

const CALM_CONFIG: VisualConfig = {
  particleDensity: 0.4,
  particleOpacity: 0.5,
  particleSpeed: 0.4,
  glowIntensity: 0.45,
  bloomStrength: 0.4,
  parallaxIntensity: 0.3,
  mouseSensitivity: 0.35,
  animationSpeed: 0.5,
  backgroundMovement: 0.3,
  lightingIntensity: 0.6,
  shootingStarFrequency: 0.2,
  neuralDensity: 0.4,
  blurStrength: 0.4,
  transitionSpeed: 1.5,
};

const STORAGE_KEY = 'avora_visual_mode';

export const VISUAL_MODES = {
  cinematic: CINEMATIC_CONFIG,
  calm: CALM_CONFIG,
} as const;

/**
 * Get the visual config for a given mode.
 */
export function getVisualConfig(mode: VisualMode): VisualConfig {
  return VISUAL_MODES[mode];
}

/**
 * Check if the user has requested reduced motion at the OS level.
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch {
    return false;
  }
}

/**
 * Resolve the effective visual mode, considering:
 * 1. Explicitly stored preference
 * 2. OS reduced-motion preference (defaults to calm)
 */
export function getStoredVisualMode(): VisualMode {
  if (typeof window === 'undefined') return 'cinematic';
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'cinematic' || stored === 'calm') {
      return stored;
    }
  } catch {
    // ignore
  }
  // If reduced motion is preferred, default to calm
  if (prefersReducedMotion()) {
    return 'calm';
  }
  return 'cinematic';
}

/**
 * Persist the visual mode preference.
 */
export function setStoredVisualMode(mode: VisualMode): void {
  try {
    localStorage.setItem(STORAGE_KEY, mode);
  } catch {
    // ignore
  }
}

/**
 * Resolve a numeric value scaled by the visual mode config.
 * e.g. scaled(1200, 'particleDensity') → 1200 in cinematic, 480 in calm
 */
export function scaled(
  baseValue: number,
  config: VisualConfig,
  key: 'particleDensity' | 'particleOpacity' | 'particleSpeed' | 'glowIntensity'
): number {
  return baseValue * config[key];
}
