import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

interface AvoraSceneProps {
  reducedMotion: boolean;
  quality: 'high' | 'medium' | 'low';
  className?: string;
  onFail?: () => void;
  /** 0→1 cinematic intro progress. 1 = fully revealed interactive state. */
  introProgress?: number;
  /** 0→1 scroll-driven progress for continuous interaction. */
  scrollProgress?: number;
}

/**
 * Minimalist 3D WebGL scene for the AVORA hero.
 *
 * A restrained, cinematic scene that supports the message without competing.
 * Features a subtle glass-like core, minimal particle field, and gentle lighting.
 * The camera has gentle movement and mild mouse parallax.
 * Quality tiers reduce particle counts and complexity for performance.
 *
 * The scene is fully self-contained: it creates, manages and disposes all
 * Three.js resources. If WebGL is unavailable, it renders nothing and the
 * parent is expected to show a fallback.
 */
export function AvoraScene({ reducedMotion, quality, className = '', onFail, introProgress = 1, scrollProgress = 0 }: AvoraSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const introProgressRef = useRef(introProgress);
  const scrollProgressRef = useRef(scrollProgress);
  const [failed, setFailed] = useState(false);

  // Keep the refs in sync so the animation loop always reads the latest value.
  useEffect(() => {
    introProgressRef.current = introProgress;
  }, [introProgress]);
  useEffect(() => {
    scrollProgressRef.current = scrollProgress;
  }, [scrollProgress]);

  useEffect(() => {
    introProgressRef.current = introProgress;
  }, [introProgress]);

  const isLow = quality === 'low';
  const isMedium = quality === 'medium';

  // Adaptive particle count based on quality - significantly reduced
  const particleCount = Math.max(30, Math.min(80, 200));

  // Reduced pixel ratio for performance, especially on mobile
  const baseDpr = window.devicePixelRatio || 1;
  const dpr = isLow
    ? Math.min(baseDpr, 1)
    : isMedium
      ? Math.min(baseDpr, 1.3)
      : Math.min(baseDpr, 1.5);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: isLow,
        alpha: true,
        powerPreference: 'high-performance',
      });
      const gl = renderer.getContext();
      if (!gl || typeof gl.getParameter !== 'function') {
        setFailed(true);
        onFail?.();
        return;
      }
    } catch {
      setFailed(true);
      onFail?.();
      return;
    }

    renderer.setPixelRatio(dpr);
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setClearColor(0x0a0a0f, 0);
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0a0a0f, 0.035);

    const camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    camera.position.set(0, 0, 8);

    // Reduced lighting - cinematic but subtle
    const ambient = new THREE.AmbientLight(0x1a1a2e, 0.4);
    scene.add(ambient);

    const keyLight = new THREE.DirectionalLight(0x60a5fa, 0.8);
    keyLight.position.set(4, 5, 6);
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0xa78bfa, 0.5);
    rimLight.position.set(-3, -2, -3);
    scene.add(rimLight);

    // AVORA Core - sophisticated AI energy core
    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Premium outer shell - subtle iridescent energy field
    const shellGeo = new THREE.IcosahedronGeometry(1.8, 4);
    const shellMat = new THREE.MeshPhysicalMaterial({
      color: 0xf0c3d1, // Soft pink/purple
      transparent: true,
      opacity: 0.12,
      roughness: 0.15,
      metalness: 0.95,
      emissive: 0xf0c3d1,
      emissiveIntensity: 0.3,
      clearcoat: 1.0,
      clearcoatRoughness: 0.2,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const shell = new THREE.Mesh(shellGeo, shellMat);
    scene.add(shell);

    // Inner core with intelligent energy flow
    const innerGeo = new THREE.SphereGeometry(0.9, 64, 64);
    const innerMat = new THREE.MeshPhysicalMaterial({
      color: 0x7c9bff, // Premium blue
      transparent: true,
      opacity: 0.45,
      emissive: 0x7c9bff,
      emissiveIntensity: 0.6,
      roughness: 0.1,
      metalness: 0.98,
      clearcoat: 0.8,
      depthWrite: false,
      transmission: 0.1,
    });
    const inner = new THREE.Mesh(innerGeo, innerMat);
    scene.add(inner);

    // Energy rings - orbital intelligence indicators
    const ringCount = 3;
    for (let i = 0; i < ringCount; i++) {
      const ringGeo = new THREE.RingGeometry(1.2 + i * 0.8, 1.4 + i * 0.8, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: i === 0 ? 0xf0c3d1 : 0x7c9bff,
        transparent: true,
        opacity: i === 0 ? 0.25 : 0.15,
        side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.z = (Math.PI * 2 / ringCount) * i;
      ring.rotation.x = Math.PI / 2;
      scene.add(ring);

      // Animate rings
      const animateRing = (ring: THREE.Mesh) => {
        const animate = () => {
          if (ring && ring.parent) {
            ring.rotation.z += 0.002 * (i + 1);
            requestAnimationFrame(() => animateRing(ring));
          }
        };
        animate();
      };
      animateRing(ring);
    }

    // Particle field - reduced and simplified
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const palette = [
      new THREE.Color(isLow ? 0x60a5fa : 0x60a5fa),
      new THREE.Color(isLow ? 0xa78bfa : 0xa78bfa),
    ];

    for (let i = 0; i < particleCount; i++) {
      const radius = 3 + Math.random() * 4;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta) * 0.5;
      positions[i * 3 + 2] = radius * Math.cos(phi);
      colors[i * 3] = palette[0].r;
      colors[i * 3 + 1] = palette[0].g;
      colors[i * 3 + 2] = palette[0].b;
    }

    const particleGeo = new THREE.BufferGeometry();
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMat = new THREE.PointsMaterial({
      size: isLow ? 0.15 : isMedium ? 0.25 : 0.35,
      transparent: true,
      opacity: isLow ? 0.15 : isMedium ? 0.25 : 0.35,
      vertexColors: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true,
    });

    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // Mouse interaction (reduced intensity)
    const mouse = { x: 0, y: 0 };
    const target = { x: 0, y: 0 };

    const handleMouseMove = (e: MouseEvent) => {
      target.x = (e.clientX / window.innerWidth - 0.5) * 1;
      target.y = (e.clientY / window.innerHeight - 0.5) * 1;
    };
    const handleTouchMove = (e: TouchEvent) => {
      const t = e.touches[0];
      if (!t) return;
      target.x = (t.clientX / window.innerWidth - 0.5) * 1;
      target.y = (t.clientY / window.innerHeight - 0.5) * 1;
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('touchmove', handleTouchMove, { passive: true });

    // Resize
    const handleResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (w === 0 || h === 0) return;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Animation loop
    const clock = new THREE.Clock();
    let rafId = 0;
    let running = true;

    const animate = () => {
      if (!running) return;
      const elapsed = clock.getElapsedTime();

      // Smooth mouse parallax - reduced intensity
      mouse.x += (target.x - mouse.x) * 0.02;
      mouse.y += (target.y - mouse.y) * 0.02;

      // Intro progress-based camera movement
      const progress = introProgressRef.current;
      const parallaxStrength = progress;
      const introZ = 10 - progress * 3;
      camera.position.z = introZ;

      // Core subtle rotation
      const coreScale = progress < 0.15 ? 0 : Math.min(1, (progress - 0.15) / 0.6);
      coreGroup.rotation.y = elapsed * 0.04 * parallaxStrength;
      coreGroup.rotation.x = Math.sin(elapsed * 0.1) * 0.04 * parallaxStrength;
      coreGroup.scale.setScalar(Math.max(0.001, coreScale));

      // Particle orbital drift
      particles.rotation.y += 0.002;

      // Light movement
      keyLight.position.x = 3 + Math.sin(elapsed * 0.5) * 0.5;
      keyLight.position.y = 4 + Math.cos(elapsed * 0.3) * 0.3;
      rimLight.position.x = -3 + Math.cos(elapsed * 0.4) * 0.3;

      renderer.render(scene, camera);
      rafId = requestAnimationFrame(animate);
    };

    if (reducedMotion) {
      coreGroup.rotation.y = 0.2;
      coreGroup.position.y = 0;
      shellMat.opacity = 0.1;
      renderer.render(scene, camera);
    } else {
      animate();
    }

    // Pause when tab hidden
    const handleVisibility = () => {
      if (document.hidden) {
        running = false;
        cancelAnimationFrame(rafId);
      } else {
        running = true;
        clock.getDelta();
        animate();
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);

    // Cleanup
    return () => {
      running = false;
      cancelAnimationFrame(rafId);
      document.removeEventListener('visibilitychange', handleVisibility);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('resize', handleResize);

      shellGeo.dispose();
      shellMat.dispose();
      inner.geometry.dispose();
      inner.material.dispose();
      particleGeo.dispose();
      particleMat.dispose();

      scene.clear();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [reducedMotion, quality, onFail]);

  if (failed) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className={`hero-scene absolute inset-0 overflow-hidden pointer-events-none ${className}`}
      aria-hidden="true"
    />
  );
}

export default AvoraScene;