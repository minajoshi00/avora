'use client';
import { useEffect, useRef } from 'react';

/**
 * Lightweight cinematic hero canvas
 * - Slow drifting particles + soft orb drift + faint connecting lines
 * - Cursor subtly attracts particles (max ~12px offset, lerped)
 * - No WebGL, pure 2D canvas, ~30 particles desktop / 14 mobile
 * - Respects prefers-reduced-motion → static fallback
 * - Fully passive: pointer-events:none, z behind hero content
 */
export function HeroCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number | null>(null);
  const mouseRef = useRef({ x: 0, y: 0, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    // Mobile check for particle density
    const isMobile = window.innerWidth < 768;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);

    let width = 0;
    let height = 0;
    let particles: Array<{
      x: number; y: number; vx: number; vy: number; r: number; baseR: number; hue: number; phase: number;
    }> = [];
    let orbs = [
      { x: 0.22, y: 0.28, r: 0.42, hue: 220, alpha: 0.14, driftX: 0.00018, driftY: 0.00012, phase: 0 },
      { x: 0.78, y: 0.72, r: 0.48, hue: 270, alpha: 0.12, driftX: -0.00014, driftY: -0.00010, phase: Math.PI },
      { x: 0.62, y: 0.38, r: 0.28, hue: 185, alpha: 0.08, driftX: -0.00009, driftY: 0.00011, phase: Math.PI * 0.6 },
    ];

    const count = prefersReduced ? 0 : isMobile ? 14 : 28;
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const initParticles = () => {
      particles = [];
      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = 0.12 + Math.random() * 0.22; // slow
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          r: 1.1 + Math.random() * 1.6,
          baseR: 1.1 + Math.random() * 1.6,
          hue: 210 + Math.random() * 55, // blue to purple
          phase: Math.random() * Math.PI * 2,
        });
      }
    };

    resize();
    initParticles();

    const onResize = () => {
      resize();
      initParticles();
    };
    window.addEventListener('resize', onResize, { passive: true });

    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current.x = e.clientX - rect.left;
      mouseRef.current.y = e.clientY - rect.top;
      mouseRef.current.active = true;
    };
    const onMouseLeave = () => { mouseRef.current.active = false; };
    window.addEventListener('mousemove', onMouseMove, { passive: true });
    window.addEventListener('mouseleave', onMouseLeave);

    if (prefersReduced) {
      // Static fallback: paint soft gradients once
      ctx.clearRect(0, 0, width, height);
      // base vignette already from CSS, just add 2 static glows
      const g1 = ctx.createRadialGradient(width * 0.28, height * 0.32, 0, width * 0.28, height * 0.32, width * 0.45);
      g1.addColorStop(0, 'rgba(96,165,250,0.14)');
      g1.addColorStop(1, 'rgba(96,165,250,0)');
      ctx.fillStyle = g1;
      ctx.fillRect(0, 0, width, height);
      const g2 = ctx.createRadialGradient(width * 0.78, height * 0.68, 0, width * 0.78, height * 0.68, width * 0.5);
      g2.addColorStop(0, 'rgba(167,139,250,0.12)');
      g2.addColorStop(1, 'rgba(167,139,250,0)');
      ctx.fillStyle = g2;
      ctx.fillRect(0, 0, width, height);
      return () => {
        window.removeEventListener('resize', onResize);
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseleave', onMouseLeave);
      };
    }

    let t = 0;
    const draw = () => {
      t += 0.0016; // ~ 60fps gentle
      ctx.clearRect(0, 0, width, height);

      // --- soft orbs (large blurred radial gradients) ---
      orbs.forEach((orb) => {
        // slow drift
        orb.x += orb.driftX + Math.sin(t * 0.6 + orb.phase) * 0.00005;
        orb.y += orb.driftY + Math.cos(t * 0.5 + orb.phase) * 0.00005;
        // keep in bounds
        if (orb.x < 0.05) orb.x = 0.05;
        if (orb.x > 0.95) orb.x = 0.95;
        if (orb.y < 0.05) orb.y = 0.05;
        if (orb.y > 0.95) orb.y = 0.95;

        const cx = orb.x * width;
        const cy = orb.y * height;
        const rad = Math.min(width, height) * orb.r;
        // cursor parallax for orbs (very subtle)
        let shiftX = 0, shiftY = 0;
        if (mouseRef.current.active) {
          shiftX = (mouseRef.current.x - width / 2) * 0.015;
          shiftY = (mouseRef.current.y - height / 2) * 0.012;
          if (isMobile) { shiftX *= 0.5; shiftY *= 0.5; }
        }

        const grad = ctx.createRadialGradient(cx + shiftX, cy + shiftY, 0, cx + shiftX, cy + shiftY, rad);
        const alpha = orb.alpha * (0.92 + Math.sin(t * 0.7 + orb.phase) * 0.08);
        if (orb.hue === 220) {
          grad.addColorStop(0, `rgba(96,165,250,${alpha})`);
          grad.addColorStop(0.55, `rgba(96,165,250,${alpha * 0.35})`);
          grad.addColorStop(1, 'rgba(96,165,250,0)');
        } else if (orb.hue === 270) {
          grad.addColorStop(0, `rgba(167,139,250,${alpha})`);
          grad.addColorStop(1, 'rgba(167,139,250,0)');
        } else {
          grad.addColorStop(0, `rgba(34,211,238,${alpha})`);
          grad.addColorStop(1, 'rgba(34,211,238,0)');
        }
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(cx + shiftX, cy + shiftY, rad, 0, Math.PI * 2);
        ctx.fill();
      });

      // --- particles ---
      const mouseX = mouseRef.current.active ? mouseRef.current.x : width / 2;
      const mouseY = mouseRef.current.active ? mouseRef.current.y : height / 2;

      particles.forEach((p) => {
        // drift
        p.x += p.vx;
        p.y += p.vy;
        // wrap
        if (p.x < -10) p.x = width + 10;
        if (p.x > width + 10) p.x = -10;
        if (p.y < -10) p.y = height + 10;
        if (p.y > height + 10) p.y = -10;

        // subtle cursor influence (lerp, max 10-14px)
        let dx = mouseX - p.x;
        let dy = mouseY - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const influence = isMobile ? 110 : 160;
        let ox = 0, oy = 0;
        if (mouseRef.current.active && dist < influence) {
          const pull = (1 - dist / influence) * 0.018; // gentle
          ox = dx * pull * 10;
          oy = dy * pull * 10;
          // clamp
          const max = isMobile ? 8 : 12;
          ox = Math.max(-max, Math.min(max, ox));
          oy = Math.max(-max, Math.min(max, oy));
        }

        // twinkle
        const tw = 0.55 + Math.sin(t * 3 + p.phase) * 0.30 + Math.sin(t * 1.7 + p.phase * 1.3) * 0.15;
        const alpha = Math.max(0.15, Math.min(0.95, tw));

        // glow dot
        const grd = ctx.createRadialGradient(p.x + ox, p.y + oy, 0, p.x + ox, p.y + oy, p.r * 4);
        const col = `hsla(${p.hue}, 92%, 72%, `;
        grd.addColorStop(0, col + alpha * 0.9 + ')');
        grd.addColorStop(0.35, col + alpha * 0.35 + ')');
        grd.addColorStop(1, col + '0)');
        ctx.fillStyle = grd;
        ctx.beginPath();
        ctx.arc(p.x + ox, p.y + oy, p.r * 4, 0, Math.PI * 2);
        ctx.fill();

        // core
        ctx.fillStyle = `hsla(${p.hue}, 95%, 78%, ${alpha})`;
        ctx.shadowColor = `hsla(${p.hue}, 90%, 70%, ${alpha * 0.6})`;
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(p.x + ox, p.y + oy, p.r, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      // --- faint connecting lines between close particles ---
      if (!isMobile) {
        ctx.lineWidth = 0.55;
        for (let i = 0; i < particles.length; i++) {
          for (let j = i + 1; j < particles.length; j++) {
            const a = particles[i], b = particles[j];
            const dx = a.x - b.x;
            const dy = a.y - b.y;
            const d = Math.sqrt(dx * dx + dy * dy);
            const thresh = 110;
            if (d < thresh) {
              const opa = (1 - d / thresh) * 0.07; // very subtle
              ctx.strokeStyle = `rgba(148,163,184,${opa})`;
              ctx.beginPath();
              ctx.moveTo(a.x, a.y);
              ctx.lineTo(b.x, b.y);
              ctx.stroke();
            }
          }
        }
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', onResize);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseleave', onMouseLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ display: 'block' }}
    />
  );
}
