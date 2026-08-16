'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import {
  Sparkles,
  Brain,
  Target,
  Heart,
  User,
  TrendingUp,
  Play,
} from 'lucide-react';

const flowStages = [
  {
    id: 'moment',
    label: 'Current Moment',
    icon: Sparkles,
    description: 'Sensory input, context, environment',
    color: '#60A5FA',
  },
  {
    id: 'context',
    label: 'Context',
    icon: Brain,
    description: 'Situational understanding',
    color: '#A78BFA',
  },
  {
    id: 'memory',
    label: 'Memory',
    icon: TrendingUp,
    description: 'Relevant history & patterns',
    color: '#22D3EE',
  },
  {
    id: 'goals',
    label: 'Goals',
    icon: Target,
    description: 'User objectives & needs',
    color: '#34D399',
  },
  {
    id: 'emotion',
    label: 'Emotion',
    icon: Heart,
    description: 'Tone & emotional state',
    color: '#F472B6',
  },
  {
    id: 'personality',
    label: 'Personality',
    icon: User,
    description: 'Adaptive response style',
    color: '#FB923C',
  },
  {
    id: 'action',
    label: 'Action',
    icon: Play,
    description: 'Thoughtful response or assistance',
    color: '#60A5FA',
  },
];

export function InternalWorld() {
  const sectionRef = useRef<HTMLElement>(null);
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' });
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    const interval = setInterval(() => {
      setActiveStage((prev) => (prev + 1) % flowStages.length);
    }, 2500);
    return () => clearInterval(interval);
  }, [isInView]);

  return (
    <section ref={sectionRef} className="relative py-32 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-purple-500/3 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] rounded-full bg-blue-500/3 blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-20"
        >
          <SectionHeading
            label="Inside AVORA"
            title="The intelligence within"
            description="A living system that processes context, emotion, memory, and meaning — all to become more helpful with every interaction."
          />
        </motion.div>

        {/* Flow visualization */}
        <div className="relative max-w-5xl mx-auto">
          {/* Connection line */}
          <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-blue-500/20 via-purple-500/20 to-cyan-500/20 -translate-x-1/2" />

          <div className="space-y-6 lg:space-y-8">
            {flowStages.map((stage, index) => {
              const Icon = stage.icon;
              const isActive = activeStage === index;
              const isLeft = index % 2 === 0;

              return (
                <motion.div
                  key={stage.id}
                  initial={{ opacity: 0, x: isLeft ? -30 : 30 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: '-50px' }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className={`relative flex items-center gap-6 lg:gap-12 ${
                    isLeft ? 'lg:flex-row' : 'lg:flex-row-reverse'
                  } flex-col`}
                >
                  {/* Content card */}
                  <motion.div
                    className={`flex-1 w-full ${isLeft ? 'lg:text-right' : 'lg:text-left'}`}
                    whileHover={{ y: -4 }}
                  >
                    <div
                      className={`relative px-6 py-5 rounded-2xl border transition-all duration-500 ${
                        isActive
                          ? 'bg-white/[0.06] border-white/[0.15] shadow-[0_0_30px_rgba(96,165,250,0.08)]'
                          : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04]'
                      }`}
                    >
                      <div className={`flex items-start gap-4 ${isLeft ? 'lg:flex-row-reverse' : ''}`}>
                        <motion.div
                          className="w-10 h-10 rounded-lg flex items-center justify-center border border-white/[0.08] shrink-0"
                          style={{ backgroundColor: `${stage.color}15` }}
                          whileHover={{ scale: 1.1, rotate: 5 }}
                        >
                          <Icon size={18} style={{ color: stage.color }} />
                        </motion.div>
                        <div className="flex-1 min-w-0">
                          <span
                            className="text-[10px] font-medium tracking-wider uppercase block mb-1"
                            style={{ color: stage.color }}
                          >
                            {stage.label}
                          </span>
                          <p className="text-sm text-gray-400 leading-relaxed">
                            {stage.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  </motion.div>

                  {/* Spacer */}
                  <div className="hidden lg:block flex-1" />
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Active stage highlight */}
        <motion.div
          className="mt-20 max-w-3xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <div className="relative rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-8 overflow-hidden">
            {/* Animated glow */}
            <motion.div
              className="absolute inset-0 opacity-40"
              style={{
                background: `radial-gradient(circle at 50% 50%, ${flowStages[activeStage]?.color}15 0%, transparent 60%)`,
              }}
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 3, repeat: Infinity }}
            />

            <div className="relative z-10 flex items-center gap-6">
              <motion.div
                className="w-16 h-16 rounded-2xl flex items-center justify-center border border-white/[0.08] shrink-0"
                style={{ backgroundColor: `${flowStages[activeStage]?.color}15` }}
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 4, repeat: Infinity }}
              >
                {(() => {
                  const Icon = flowStages[activeStage]?.icon;
                  return Icon ? (
                    <Icon size={28} style={{ color: flowStages[activeStage]?.color }} />
                  ) : null;
                })()}
              </motion.div>

              <div>
                <motion.span
                  className="text-[10px] font-medium tracking-[0.2em] uppercase block mb-2"
                  style={{ color: flowStages[activeStage]?.color }}
                  key={`label-${activeStage}`}
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  {flowStages[activeStage]?.label}
                </motion.span>
                <motion.p
                  className="text-sm text-gray-400 leading-relaxed"
                  key={`desc-${activeStage}`}
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  {flowStages[activeStage]?.description}
                </motion.p>
              </div>
            </div>

            {/* Progress indicator */}
            <div className="relative z-10 mt-8 flex items-center gap-2">
              {flowStages.map((_, idx) => (
                <motion.div
                  key={idx}
                  className="h-1 flex-1 rounded-full overflow-hidden bg-white/[0.06]"
                >
                  {idx <= activeStage && (
                    <motion.div
                      className="h-full rounded-full"
                      style={{ backgroundColor: flowStages[activeStage]?.color }}
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      transition={{ duration: 0.5 }}
                    />
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export default InternalWorld;