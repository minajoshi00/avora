'use client';

import { useState, useEffect, useRef, useId } from 'react';

export type AvoraCoreState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'excited' | 'focused';

interface InteractiveAvoraCoreProps {
  state?: AvoraCoreState;
  size?: number;
  className?: string;
}

export function InteractiveAvoraCore({
  state = 'idle',
  size = 280,
  className = ''
}: InteractiveAvoraCoreProps) {
  const uniqueId = useId();
  const [internalState, setInternalState] = useState<AvoraCoreState>(state);
  const containerRef = useRef<HTMLDivElement>(null);

  const coreGlowId = `core-glow-${uniqueId}`;
  const starGradientId = `star-gradient-${uniqueId}`;
  const glowFilterId = `glow-${uniqueId}`;

  useEffect(() => {
    setInternalState(state);
  }, [state]);

  const config = {
    idle: {
      orbitSpeed: 20,
      pulseSpeed: 3,
      particleOpacity: 0.3,
      glowIntensity: 0.4,
      coreScale: 1,
      ringOpacity: 0.15,
    },
    listening: {
      orbitSpeed: 8,
      pulseSpeed: 1.5,
      particleOpacity: 0.7,
      glowIntensity: 0.7,
      coreScale: 1.05,
      ringOpacity: 0.35,
    },
    thinking: {
      orbitSpeed: 6,
      pulseSpeed: 2,
      particleOpacity: 0.6,
      glowIntensity: 0.6,
      coreScale: 1.02,
      ringOpacity: 0.25,
    },
    speaking: {
      orbitSpeed: 4,
      pulseSpeed: 1,
      particleOpacity: 0.8,
      glowIntensity: 0.8,
      coreScale: 1.08,
      ringOpacity: 0.4,
    },
    excited: {
      orbitSpeed: 3,
      pulseSpeed: 0.8,
      particleOpacity: 1,
      glowIntensity: 1,
      coreScale: 1.12,
      ringOpacity: 0.5,
    },
    focused: {
      orbitSpeed: 12,
      pulseSpeed: 2.5,
      particleOpacity: 0.5,
      glowIntensity: 0.5,
      coreScale: 1.03,
      ringOpacity: 0.2,
    },
  };

  const current = config[internalState];

  return (
    <div
      ref={containerRef}
      className={className}
      style={{ width: size, height: size }}
    >
      <svg
        viewBox="0 0 200 200"
        width={size}
        height={size}
        className="overflow-visible"
      >
        <defs>
          <radialGradient id={coreGlowId} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#60A5FA" stopOpacity={current.glowIntensity} />
            <stop offset="50%" stopColor="#A78BFA" stopOpacity={current.glowIntensity * 0.6} />
            <stop offset="100%" stopColor="#60A5FA" stopOpacity="0" />
          </radialGradient>

          <linearGradient id={starGradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#60A5FA" />
            <stop offset="100%" stopColor="#A78BFA" />
          </linearGradient>

          <filter id={glowFilterId} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Data rings */}
        {[72, 85, 98].map((r, i) => (
          <circle
            key={i}
            cx="100"
            cy="100"
            r={r}
            fill="none"
            stroke={`url(#${starGradientId})`}
            strokeWidth="0.4"
            opacity={current.ringOpacity}
            strokeDasharray="8 12"
          >
            <animateTransform
              attributeName="transform"
              type="rotate"
              from={i % 2 === 0 ? "0 100 100" : "360 100 100"}
              to={i % 2 === 0 ? "360 100 100" : "0 100 100"}
              dur={`${current.orbitSpeed * (1 + i * 0.3)}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))}

        <circle
          cx="100"
          cy="100"
          r="70"
          fill={`url(#${coreGlowId})`}
          opacity={current.glowIntensity * 0.4}
          style={{ transition: `opacity ${current.pulseSpeed}s ease-in-out` }}
        />

        <circle
          cx="100"
          cy="100"
          r="45"
          fill="none"
          stroke={`url(#${starGradientId})`}
          strokeWidth="0.5"
          opacity="0.2"
        >
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="0 100 100"
            to="360 100 100"
            dur={`${current.orbitSpeed}s`}
            repeatCount="indefinite"
          />
        </circle>

        <circle
          cx="100"
          cy="100"
          r="55"
          fill="none"
          stroke={`url(#${starGradientId})`}
          strokeWidth="0.3"
          opacity="0.15"
        >
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="360 100 100"
            to="0 100 100"
            dur={`${current.orbitSpeed * 1.5}s`}
            repeatCount="indefinite"
          />
        </circle>

        {[0, 1, 2, 3, 4].map((i) => {
          const angle = (i * 72) * (Math.PI / 180);
          const radius = 50;
          const x = 100 + Math.cos(angle) * radius;
          const y = 100 + Math.sin(angle) * radius;
          const orbitDuration = current.orbitSpeed + i * 2;

          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r="1.5"
              fill={`url(#${starGradientId})`}
              opacity={current.particleOpacity}
            >
              <animateTransform
                attributeName="transform"
                type="rotate"
                from={`${i * 72} 100 100`}
                to={`${360 + i * 72} 100 100`}
                dur={`${orbitDuration}s`}
                repeatCount="indefinite"
              />
            </circle>
          );
        })}

        <g filter={`url(#${glowFilterId})`} transform={`scale(${current.coreScale}) translate(${100 - 100 / current.coreScale}, ${100 - 100 / current.coreScale})`}>
          <g transform="translate(100, 100)">
            <line x1="0" y1="-18" x2="0" y2="18" stroke={`url(#${starGradientId})`} strokeWidth="2" strokeLinecap="round" fill="none" />
            <line x1="-14" y1="-10" x2="14" y2="10" stroke={`url(#${starGradientId})`} strokeWidth="2" strokeLinecap="round" fill="none" />
            <line x1="-14" y1="10" x2="14" y2="-10" stroke={`url(#${starGradientId})`} strokeWidth="2" strokeLinecap="round" fill="none" />
            <circle cx="0" cy="0" r="2.5" fill={`url(#${starGradientId})`} />
          </g>
        </g>

        {internalState === 'listening' && (
          <circle cx="100" cy="100" r="30" fill="none" stroke="url(#starGradientId)" strokeWidth="0.5" opacity="0.4">
            <animate attributeName="r" values="30;50" dur="2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.4;0" dur="2s" repeatCount="indefinite" />
          </circle>
        )}
      </svg>
    </div>
  );
}

export default InteractiveAvoraCore;