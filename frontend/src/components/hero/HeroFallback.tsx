'use client';

interface HeroFallbackProps {
  quality?: 'high' | 'medium' | 'low';
}

export function HeroFallback({ quality = 'medium' }: HeroFallbackProps) {
  return (
    <div
      className="absolute inset-0 flex items-center justify-center overflow-hidden"
      aria-hidden="true"
    >
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-radial from-blue-500/5 via-purple-500/3 to-transparent animate-pulse" />

      {/* AVORA Core SVG Fallback - lightweight, no WebGL required */}
      <div className="relative w-[280px] h-[280px] sm:w-[360px] sm:h-[360px] md:w-[440px] md:h-[440px]">
        <svg
          viewBox="0 0 200 200"
          className="w-full h-full overflow-visible"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#60A5FA" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#A78BFA" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#60A5FA" stopOpacity="0" />
            </radialGradient>
            <linearGradient id="starGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#60A5FA" />
              <stop offset="100%" stopColor="#A78BFA" />
            </linearGradient>
          </defs>

          {/* Outer rings - CSS/SVG animation, no WebGL needed */}
          {[72, 85, 98].map((r, i) => (
            <circle
              key={i}
              cx="100"
              cy="100"
              r={r}
              fill="none"
              stroke="url(#starGradient)"
              strokeWidth="0.4"
              opacity={0.15 * (quality === 'low' ? 0.5 : 1)}
              strokeDasharray="8 12"
            >
              <animateTransform
                attributeName="transform"
                type="rotate"
                from={i % 2 === 0 ? '0 100 100' : '360 100 100'}
                to={i % 2 === 0 ? '360 100 100' : '0 100 100'}
                dur={`${20 + i * 5}s`}
                repeatCount="indefinite"
              />
            </circle>
          ))}

          {/* Core glow */}
          <circle
            cx="100"
            cy="100"
            r="70"
            fill="url(#coreGlow)"
            opacity={0.3 * (quality === 'low' ? 0.5 : 1)}
          >
            <animate
              attributeName="opacity"
              values="0.2;0.4;0.2"
              dur="4s"
              repeatCount="indefinite"
            />
          </circle>

          {/* Inner core */}
          <circle
            cx="100"
            cy="100"
            r="45"
            fill="none"
            stroke="url(#starGradient)"
            strokeWidth="0.5"
            opacity={0.3}
          >
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="0 100 100"
              to="360 100 100"
              dur="15s"
              repeatCount="indefinite"
            />
          </circle>

          {/* Orbital particles */}
          {[0, 1, 2, 3, 4].map((i) => {
            const angle = (i * 72) * (Math.PI / 180);
            const radius = 50;
            const x = 100 + Math.cos(angle) * radius;
            const y = 100 + Math.sin(angle) * radius;
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r="1.5"
                fill="url(#starGradient)"
                opacity={0.6 * (quality === 'low' ? 0.5 : 1)}
              >
                <animateTransform
                  attributeName="transform"
                  type="rotate"
                  from={`${i * 72} 100 100`}
                  to={`${360 + i * 72} 100 100`}
                  dur={`${15 + i * 2}s`}
                  repeatCount="indefinite"
                />
              </circle>
            );
          })}

          {/* Center icon */}
          <g transform="translate(100, 100)">
            <line x1="0" y1="-18" x2="0" y2="18" stroke="url(#starGradient)" strokeWidth="2" strokeLinecap="round" fill="none" />
            <line x1="-14" y1="-10" x2="14" y2="10" stroke="url(#starGradient)" strokeWidth="2" strokeLinecap="round" fill="none" />
            <line x1="-14" y1="10" x2="14" y2="-10" stroke="url(#starGradient)" strokeWidth="2" strokeLinecap="round" fill="none" />
            <circle cx="0" cy="0" r="2.5" fill="url(#starGradient)" />
          </g>
        </svg>
      </div>
    </div>
  );
}

export default HeroFallback;