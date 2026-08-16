'use client';

import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  size: number;
  alpha: number;
  baseAlpha: number;
  color: string;
  twinkleSpeed: number;
  twinkleOffset: number;
}

export function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0 });
  const timeRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: Particle[] = [];

    const colors = [
      '96, 165, 250',   // blue
      '167, 139, 250',  // purple
      '34, 211, 238',   // cyan
      '244, 114, 182',  // pink
      '255, 255, 255',  // white stars
    ];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    const initParticles = () => {
      const count = Math.min(Math.floor((window.innerWidth * window.innerHeight) / 12000), 180);
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        z: Math.random() * 1000,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        vz: (Math.random() - 0.5) * 2,
        size: Math.random() * 2 + 0.5,
        alpha: Math.random() * 0.6 + 0.2,
        baseAlpha: Math.random() * 0.6 + 0.2,
        color: colors[Math.floor(Math.random() * colors.length)],
        twinkleSpeed: Math.random() * 2 + 1,
        twinkleOffset: Math.random() * Math.PI * 2,
      }));
    };

    const draw = () => {
      timeRef.current += 0.016;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const mouseX = mouseRef.current.x;
      const mouseY = mouseRef.current.y;
      const time = timeRef.current;

      // Draw nebula background
      const nebulaGradient = ctx.createRadialGradient(
        canvas.width * 0.3, canvas.height * 0.3, 0,
        canvas.width * 0.3, canvas.height * 0.3, canvas.width * 0.8
      );
      nebulaGradient.addColorStop(0, 'rgba(96, 165, 250, 0.03)');
      nebulaGradient.addColorStop(0.5, 'rgba(167, 139, 250, 0.02)');
      nebulaGradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = nebulaGradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const nebulaGradient2 = ctx.createRadialGradient(
        canvas.width * 0.7, canvas.height * 0.7, 0,
        canvas.width * 0.7, canvas.height * 0.7, canvas.width * 0.6
      );
      nebulaGradient2.addColorStop(0, 'rgba(34, 211, 238, 0.02)');
      nebulaGradient2.addColorStop(0.5, 'rgba(244, 114, 182, 0.015)');
      nebulaGradient2.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = nebulaGradient2;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p, i) => {
        // Twinkle effect
        const twinkle = Math.sin(time * p.twinkleSpeed + p.twinkleOffset) * 0.3 + 0.7;
        p.alpha = p.baseAlpha * twinkle;

        // Mouse interaction
        const dx = mouseX - p.x;
        const dy = mouseY - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 200) {
          const force = (200 - dist) / 200;
          p.vx += dx * force * 0.00015;
          p.vy += dy * force * 0.00015;
          p.alpha = Math.min(p.baseAlpha + 0.3, 0.8);
        } else {
          p.alpha = Math.max(p.baseAlpha, p.alpha * 0.995);
        }

        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.99;
        p.vy *= 0.99;

        // Wrap around
        if (p.x < -10) p.x = canvas.width + 10;
        if (p.x > canvas.width + 10) p.x = -10;
        if (p.y < -10) p.y = canvas.height + 10;
        if (p.y > canvas.height + 10) p.y = -10;

        // Depth-based size and opacity
        const depth = (p.z + 1000) / 2000;
        const displaySize = p.size * (0.5 + depth * 0.5);
        const displayAlpha = p.alpha * (0.5 + depth * 0.5);

        ctx.beginPath();
        ctx.arc(p.x, p.y, displaySize, 0, Math.PI * 2);

        const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, displaySize * 4);
        gradient.addColorStop(0, `rgba(${p.color}, ${displayAlpha})`);
        gradient.addColorStop(0.5, `rgba(${p.color}, ${displayAlpha * 0.3})`);
        gradient.addColorStop(1, `rgba(${p.color}, 0)`);

        ctx.fillStyle = gradient;
        ctx.fill();

        // Draw connections between nearby particles
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx2 = p.x - p2.x;
          const dy2 = p.y - p2.y;
          const distance = Math.sqrt(dx2 * dx2 + dy2 * dy2);

          if (distance < 100) {
            const opacity = 0.06 * (1 - distance / 100) * depth;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);

            const lineGradient = ctx.createLinearGradient(p.x, p.y, p2.x, p2.y);
            lineGradient.addColorStop(0, `rgba(${p.color}, ${opacity})`);
            lineGradient.addColorStop(1, `rgba(${p2.color}, ${opacity})`);

            ctx.strokeStyle = lineGradient;
            ctx.lineWidth = 0.3;
            ctx.stroke();
          }
        }
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    resize();
    initParticles();
    draw();

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };

    const onResize = () => {
      resize();
      initParticles();
    };

    window.addEventListener('resize', onResize);
    window.addEventListener('mousemove', handleMouseMove, { passive: true });

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', onResize);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
}