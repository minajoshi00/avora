'use client';

import { useEffect, useRef, useState } from 'react';

type SoundType = 'hover' | 'click' | 'typing' | 'ambient';

export function useSound() {
  const [enabled, setEnabled] = useState(true);
  const [mounted, setMounted] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    setMounted(true);
    try {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    } catch (_error) {
      console.warn('Web Audio API not supported');
    }
    return () => {
      audioContextRef.current?.close();
    };
  }, []);

  const playTone = (frequency: number, type: OscillatorType, duration: number, volume = 0.02) => {
    if (!enabled || !audioContextRef.current) return;
    
    const ctx = audioContextRef.current;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = type;
    osc.frequency.setValueAtTime(frequency, ctx.currentTime);
    
    gain.gain.setValueAtTime(volume, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start();
    osc.stop(ctx.currentTime + duration);
  };

  const play = (type: SoundType) => {
    if (!enabled) return;
    
    switch (type) {
      case 'hover':
        playTone(800, 'sine', 0.08, 0.015);
        break;
      case 'click':
        playTone(600, 'sine', 0.1, 0.02);
        setTimeout(() => playTone(900, 'sine', 0.08, 0.015), 50);
        break;
      case 'typing':
        playTone(1200 + Math.random() * 400, 'sine', 0.05, 0.008);
        break;
      case 'ambient':
        // Subtle low drone
        playTone(60, 'sine', 0.5, 0.005);
        break;
    }
  };

  const toggle = () => setEnabled(prev => !prev);

  if (!mounted) return { play, enabled: true, toggle: () => {} };

  return { play, enabled, toggle };
}