'use client';

import { useEffect, useRef } from 'react';
import { useVisualMode } from './VisualModeProvider';

interface Star {
  x: number;
  y: number;
  z: number;
  ox: number;
  oy: number;
  size: number;
  alpha: number;
  color: string;
}

interface ShootingStar {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  size: number;
  color: string;
}

interface NeuralNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  pulsePhase: number;
  connections: number[];
  frequency: number;
}

interface DataParticle {
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  alpha: number;
  speed: number;
  size: number;
  life: number;
}

export function InteractiveBackground({ quality = 'high' }: { quality: 'high' | 'medium' | 'low' } = { quality: 'high' }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0, rx: 0, ry: 0 });
  const starsRef = useRef<Star[]>([]);
  const shootingStarsRef = useRef<ShootingStar[]>([]);
  const neuralNodesRef = useRef<NeuralNode[]>([]);
  const dataParticlesRef = useRef<DataParticle[]>([]);
  const rafRef = useRef<number | undefined>(undefined);
  const timeRef = useRef(0);
  const cursorProximityRef = useRef(0);
  const { config, reducedMotion } = useVisualMode();

  // Quality-tier scaling factors — keep the scene visible but performant
  const isLow = quality === 'low';
  const isMedium = quality === 'medium';

  // Adaptive counts based on quality
  const starCount = isLow ? 150 : isMedium ? 400 : 800;
  const neuralNodeCount = isLow ? 5 : isMedium ? 8 : 15;
  const dataParticleCount = isLow ? 2 : isMedium ? 4 : 8;
  const shootingStarFrequency = isLow ? 0.8 : isMedium ? 0.5 : 0.3;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const colors = [
      [96, 165, 250, 0.3],
      [167, 139, 250, 0.2],
      [34, 211, 238, 0.2],
      [244, 114, 182, 0.15],
      [255, 255, 255, 0.1],
    ];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    const initStars = () => {
      // Scale star count by quality tier (low < calm < cinematic)
      const count = starCount;
      starsRef.current = Array.from({ length: count }, () => {
        const x = (Math.random() - 0.5) * canvas.width * 2;
        const y = (Math.random() - 0.5) * canvas.height * 2;
        const z = Math.random() * 2000 + 200;
        const color = colors[Math.floor(Math.random() * colors.length)];
        const [r, g, b, baseAlpha] = color;
        return {
          x,
          y,
          z,
          ox: x,
          oy: y,
          size: Math.random() * 1.2 + 0.15,
          alpha: baseAlpha * config.particleOpacity,
          color: `${r}, ${g}, ${b}`,
        };
      });
    };

    const initNeuralNodes = () => {
      // Scale node count by quality tier (low < calm < cinematic)
      const nodeCount = neuralNodeCount;
      const nodes: NeuralNode[] = [];
      for (let i = 0; i < nodeCount; i++) {
        // Scale movement speed by mode config
        const speedScale = 0.12 * config.particleSpeed;
        nodes.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * speedScale,
          vy: (Math.random() - 0.5) * speedScale,
          pulsePhase: Math.random() * Math.PI * 2,
          connections: [],
          frequency: 0.4 + Math.random() * 0.8,
        });
      }
      // Build connection graph (each node connects to 2-4 nearby nodes)
      for (let i = 0; i < nodes.length; i++) {
        const connCount = 2 + Math.floor(Math.random() * 3);
        const distances = nodes
          .map((n, idx) => ({ idx, dist: Math.hypot(n.x - nodes[i].x, n.y - nodes[i].y) }))
          .filter((d) => d.idx !== i)
          .sort((a, b) => a.dist - b.dist);
        for (let j = 0; j < Math.min(connCount, distances.length); j++) {
          nodes[i].connections.push(distances[j].idx);
        }
      }
      neuralNodesRef.current = nodes;
    };

    const spawnShootingStar = () => {
      // Scale shooting star frequency by quality tier and mode config
      if (Math.random() > shootingStarFrequency) return;
      if (shootingStarsRef.current.length < 3) {
        const startX = (Math.random() - 0.5) * canvas.width * 0.8;
        const startY = (Math.random() - 0.5) * canvas.height * 0.4;
        const angle = Math.PI / 4 + (Math.random() - 0.5) * 0.5;
        const speed = 8 + Math.random() * 6;
        const color = colors[Math.floor(Math.random() * 3)];

        shootingStarsRef.current.push({
          x: startX,
          y: startY,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 0,
          maxLife: 60 + Math.random() * 40,
          size: 1.5 + Math.random() * 1,
          color: color.join(','),
        });
      }
    };

    const spawnDataParticle = () => {
      const maxCount = dataParticleCount;
      if (dataParticlesRef.current.length < maxCount && neuralNodesRef.current.length > 0) {
        const source = neuralNodesRef.current[Math.floor(Math.random() * neuralNodesRef.current.length)];
        const target = neuralNodesRef.current[Math.floor(Math.random() * neuralNodesRef.current.length)];
        if (source && target) {
          // Scale particle speed by mode config
          const speedScale = 0.01 + Math.random() * 0.02;
          dataParticlesRef.current.push({
            x: source.x,
            y: source.y,
            targetX: target.x,
            targetY: target.y,
            alpha: 1,
            speed: speedScale * config.particleSpeed,
            size: 1 + Math.random() * 1.5,
            life: 0,
          });
        }
      }
    };

    const draw = () => {
      // Scale time advancement by mode config
      timeRef.current += 0.01 * config.animationSpeed;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;

      const sensitivity = config.mouseSensitivity;
      const mx = mouseRef.current.rx * 0.08 * sensitivity;
      const my = mouseRef.current.ry * 0.08 * sensitivity;

      const focal = 600;

      // Update neural nodes
      const nodes = neuralNodesRef.current;
      for (const node of nodes) {
        node.x += node.vx + mx * 0.002;
        node.y += node.vy + my * 0.002;
        node.pulsePhase += 0.018 * node.frequency * config.animationSpeed;

        // Wrap around
        if (node.x < -50) node.x = canvas.width + 50;
        if (node.x > canvas.width + 50) node.x = -50;
        if (node.y < -50) node.y = canvas.height + 50;
        if (node.y > canvas.height + 50) node.y = -50;
      }

      // Draw neural connections
      for (const node of nodes) {
        for (const connIdx of node.connections) {
          const target = nodes[connIdx];
          if (!target) continue;
          const dist = Math.hypot(target.x - node.x, target.y - node.y);
          if (dist > 350) continue;

          const pulse = Math.sin(node.pulsePhase) * 0.5 + 0.5;
          const cursorDist = Math.hypot(
            (node.x + target.x) / 2 - mouseRef.current.x,
            (node.y + target.y) / 2 - mouseRef.current.y
          );
          const cursorInfluence = Math.max(0, 1 - cursorDist / 400) * sensitivity;
          // Scale alpha by mode config for glow intensity
          const alpha = (0.04 + pulse * 0.04 + cursorInfluence * 0.12) * config.glowIntensity;

          ctx.beginPath();
          ctx.moveTo(node.x, node.y);
          ctx.lineTo(target.x, target.y);
          const gradient = ctx.createLinearGradient(node.x, node.y, target.x, target.y);
          gradient.addColorStop(0, `rgba(96, 165, 250, ${alpha})`);
          gradient.addColorStop(1, `rgba(167, 139, 250, ${alpha})`);
          ctx.strokeStyle = gradient;
          ctx.lineWidth = 0.6 + pulse * 0.6 + cursorInfluence * 0.4;
          ctx.stroke();

          // Energy pulse along connection
          const energyPos = (timeRef.current * 0.25 * node.frequency) % 1;
          const ex = node.x + (target.x - node.x) * energyPos;
          const ey = node.y + (target.y - node.y) * energyPos;
          const energyAlpha = (0.3 + pulse * 0.4) * (1 + cursorInfluence) * config.particleOpacity;
          ctx.beginPath();
          ctx.arc(ex, ey, 1.2 + pulse + cursorInfluence * 1.5, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(167, 139, 250, ${Math.min(1, energyAlpha)})`;
          ctx.fill();
        }
      }

      // Draw neural nodes
      for (const node of nodes) {
        const pulse = Math.sin(node.pulsePhase) * 0.5 + 0.5;
        const mouseDistToNode = Math.hypot(node.x - mouseRef.current.x, node.y - mouseRef.current.y);
        const cursorInfluence = Math.max(0, 1 - mouseDistToNode / 300) * sensitivity;
        const alpha = (0.3 + pulse * 0.3 + cursorInfluence * 0.4) * config.particleOpacity;
        const nodeSize = 1.8 + pulse + cursorInfluence * 2;

        ctx.beginPath();
        ctx.arc(node.x, node.y, nodeSize, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(96, 165, 250, ${alpha})`;
        ctx.fill();

        // Circular glow only — no square blocks
        const glowAlpha = alpha * 0.3 * config.glowIntensity;
        const glowSize = 1.5 + pulse * 3 + cursorInfluence * 2;
        const grad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, glowSize);
        grad.addColorStop(0, `rgba(96, 165, 250, ${glowAlpha})`);
        grad.addColorStop(1, 'rgba(96, 165, 250, 0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(node.x, node.y, glowSize, 0, Math.PI * 2);
        ctx.fill();
      }

      // Draw data particles
      dataParticlesRef.current = dataParticlesRef.current.filter((p) => {
        p.life += p.speed;
        if (p.life > 1) return false;

        const x = p.x + (p.targetX - p.x) * p.life;
        const y = p.y + (p.targetY - p.y) * p.life;
        const alpha = p.life < 0.1 ? p.life * 10 : p.life > 0.9 ? (1 - p.life) * 10 : 1;

        ctx.beginPath();
        ctx.arc(x, y, p.size * (1 + cursorProximityRef.current * 0.3), 0, Math.PI * 2);
        ctx.fillStyle = `rgba(167, 139, 250, ${alpha * 0.7 * config.particleOpacity})`;
        ctx.fill();

        // Trail
        const trailAlpha = alpha * 0.25 * config.particleOpacity;
        ctx.beginPath();
        ctx.arc(x, y, p.size * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(96, 165, 250, ${trailAlpha})`;
        ctx.fill();

        return true;
      });

      // Project and draw stars
      const projected = starsRef.current.map((star) => {
        const depth = Math.max(star.z, 1);
        const scale = focal / depth;
        const parallaxScale = config.parallaxIntensity;
        const px = cx + (star.ox + mx * depth * 0.002 * parallaxScale) * scale;
        const py = cy + (star.oy + my * depth * 0.002 * parallaxScale) * scale;
        const size = star.size * scale * 0.6;
        const alpha = star.alpha * Math.min(1, scale * 1.2);
        return { ...star, px, py, size, alpha };
      });

      cursorProximityRef.current = Math.min(
        1,
        Math.hypot(mouseRef.current.x - cx, mouseRef.current.y - cy) / (canvas.width * 0.4)
      );

      projected.sort((a, b) => b.z - a.z);

      for (const star of projected) {
        ctx.beginPath();
        ctx.arc(star.px, star.py, star.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${star.color}, ${star.alpha})`;
        ctx.fill();

        // Subtle twinkle on brighter stars
        if (star.size > 0.8) {
          const twinkle = Math.sin(timeRef.current * 2 + star.ox) * 0.15 + 0.85;
          ctx.beginPath();
          ctx.arc(star.px, star.py, star.size * 0.5, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255, 255, 255, ${star.alpha * 0.3 * twinkle})`;
          ctx.fill();
        }
      }

      // Nebula glow layers — intensity scales with mode
      const glowMult = config.glowIntensity;
      const grad = ctx.createRadialGradient(cx + mx * 40, cy + my * 40, 0, cx, cy, canvas.width * 0.7);
      grad.addColorStop(0, `rgba(96, 165, 250, ${0.06 * glowMult})`);
      grad.addColorStop(0.5, `rgba(167, 139, 250, ${0.03 * glowMult})`);
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Shooting stars
      shootingStarsRef.current = shootingStarsRef.current.filter((s) => {
        s.life++;
        s.x += s.vx;
        s.y += s.vy;

        if (s.life > s.maxLife) return false;

        const progress = s.life / s.maxLife;
        const alpha = progress < 0.5 ? progress * 2 : (1 - progress) * 2;
        const tailLength = 30 + s.life * 2;

        const velMag = Math.sqrt(s.vx * s.vx + s.vy * s.vy);
        const tailX = s.x - (s.vx / velMag) * tailLength;
        const tailY = s.y - (s.vy / velMag) * tailLength;

        const tailGrad = ctx.createLinearGradient(s.x, s.y, tailX, tailY);
        tailGrad.addColorStop(0, `rgba(${s.color}, ${alpha})`);
        tailGrad.addColorStop(1, `rgba(${s.color}, 0)`);

        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(tailX, tailY);
        ctx.strokeStyle = tailGrad;
        ctx.lineWidth = s.size;
        ctx.lineCap = 'round';
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(s.x, s.y, s.size * 2, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${s.color}, ${alpha * 0.8})`;
        ctx.fill();

        return true;
      });

      rafRef.current = requestAnimationFrame(draw);
    };

const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY, rx: e.clientX / window.innerWidth * config.mouseSensitivity, ry: e.clientY / window.innerHeight * config.mouseSensitivity };
    };

    const handleTouchMove = (e: TouchEvent) => {
      const t = e.touches[0];
      if (!t) return;
      mouseRef.current = { x: t.clientX, y: t.clientY, rx: t.clientX / window.innerWidth * config.mouseSensitivity, ry: t.clientY / window.innerHeight * config.mouseSensitivity };
    };

    // Hide cursor when inactive
    let cursorTimeout: number;
    const resetCursorTimeout = () => {
      canvas.style.opacity = '1';
      clearTimeout(cursorTimeout);
      cursorTimeout = window.setTimeout(() => {
        canvas.style.opacity = '0.85';
      }, 2000);
    };
    window.addEventListener('mousemove', resetCursorTimeout);
    window.addEventListener('touchmove', resetCursorTimeout);

    resize();
    initStars();
    initNeuralNodes();
    draw();

    // Scale shooting star interval by quality and mode config
    const shootingIntervalMs = 4000 / Math.max(0.2, shootingStarFrequency);
    const shootingInterval = setInterval(spawnShootingStar, shootingIntervalMs);
    const dataParticleIntervalMs = 500 / Math.max(0.3, config.particleSpeed);
    const dataParticleInterval = setInterval(spawnDataParticle, dataParticleIntervalMs);
    const neuralUpdateInterval = setInterval(() => {
      // Occasionally spawn new data particles
    }, 200);

    window.addEventListener('resize', () => {
      resize();
      initStars();
      initNeuralNodes();
    });

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('touchmove', handleTouchMove, { passive: true });

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      clearInterval(shootingInterval);
      clearInterval(dataParticleInterval);
      clearInterval(neuralUpdateInterval);
      clearTimeout(cursorTimeout);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('mousemove', resetCursorTimeout);
      window.removeEventListener('touchmove', resetCursorTimeout);
    };
  }, [config, reducedMotion]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
}
