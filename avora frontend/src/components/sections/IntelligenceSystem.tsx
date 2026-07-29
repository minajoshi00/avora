'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { Eye, Brain, Cog, Zap, RefreshCw } from 'lucide-react';

const stages = [
  {
    icon: Eye,
    label: 'SEE',
    title: 'Perception',
    description:
      'AVORA perceives the world through vision, voice, text, and data. It sees patterns, reads context, and understands nuance beyond surface-level input.',
    color: '#60A5FA',
    gradient: 'from-blue-500/20 to-cyan-500/10',
  },
  {
    icon: Brain,
    label: 'UNDERSTAND',
    title: 'Comprehension',
    description:
      'Deep semantic understanding goes beyond keywords. AVORA grasps intent, emotion, subtext, and the unspoken meaning behind every interaction.',
    color: '#A78BFA',
    gradient: 'from-purple-500/20 to-pink-500/10',
  },
  {
    icon: Cog,
    label: 'THINK',
    title: 'Reasoning',
    description:
      'Multi-step reasoning with context awareness. AVORA thinks through problems, evaluates possibilities, and arrives at intelligent conclusions.',
    color: '#22D3EE',
    gradient: 'from-cyan-500/20 to-blue-500/10',
  },
  {
    icon: Zap,
    label: 'ACT',
    title: 'Execution',
    description:
      'From generating responses to controlling applications, AVORA acts with precision. Code, create, automate, and execute — all through natural commands.',
    color: '#F472B6',
    gradient: 'from-pink-500/20 to-rose-500/10',
  },
  {
    icon: RefreshCw,
    label: 'LEARN',
    title: 'Evolution',
    description:
      'Every interaction makes AVORA smarter. It learns preferences, adapts to your style, and evolves into a more personalized intelligence over time.',
    color: '#34D399',
    gradient: 'from-emerald-500/20 to-teal-500/10',
  },
];

export function IntelligenceSystem() {
  const sectionRef = useRef<HTMLElement>(null);
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section
      ref={sectionRef}
      id="intelligence"
      className="relative py-32 overflow-hidden"
    >
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-blue-500/3 blur-3xl" />
        <div className="absolute top-0 left-1/4 w-[400px] h-[400px] rounded-full bg-purple-500/3 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] rounded-full bg-cyan-500/3 blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <SectionHeading
            label="How AVORA Thinks"
            title="Intelligence System"
            description="A living cycle of perception, understanding, reasoning, action, and evolution."
          />
        </motion.div>

        <div className="relative mt-16">
          {/* Central connecting line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-blue-500/30 via-purple-500/30 to-emerald-500/30 hidden lg:block" />

          {stages.map((stage, index) => {
            const isLeft = index % 2 === 0;
            return (
              <motion.div
                key={stage.label}
                initial={{ opacity: 0, y: 60 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-80px' }}
                transition={{
                  duration: 0.8,
                  delay: index * 0.15,
                  ease: [0.16, 1, 0.3, 1],
                }}
                className={`relative flex items-center gap-8 mb-16 last:mb-0 ${
                  isLeft ? 'lg:flex-row' : 'lg:flex-row-reverse'
                } flex-col`}
              >
                {/* Node dot on center line */}
                <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 hidden lg:block z-10">
                  <motion.div
                    className="w-5 h-5 rounded-full border-2"
                    style={{ borderColor: stage.color }}
                    animate={{
                      scale: [1, 1.3, 1],
                      boxShadow: [
                        `0 0 0 0 ${stage.color}40`,
                        `0 0 20px 4px ${stage.color}40`,
                        `0 0 0 0 ${stage.color}40`,
                      ],
                    }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      delay: index * 0.5,
                    }}
                  >
                    <div
                      className="w-full h-full rounded-full"
                      style={{ backgroundColor: stage.color, opacity: 0.6 }}
                    />
                  </motion.div>
                </div>

                {/* Content card */}
                <motion.div
                  className={`relative w-full lg:w-[calc(50%-40px)] group ${
                    isLeft ? 'lg:pr-8' : 'lg:pl-8'
                  }`}
                  whileHover={{ y: -4 }}
                  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                >
                  <div
                    className={`relative rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6 lg:p-8 overflow-hidden hover:border-white/[0.15] transition-all duration-500`}
                  >
                    {/* Gradient overlay on hover */}
                    <div
                      className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br ${stage.gradient} rounded-2xl`}
                    />

                    <div className="relative z-10">
                      <div className="flex items-center gap-4 mb-4">
                        {/* Icon */}
                        <motion.div
                          className="w-12 h-12 rounded-xl flex items-center justify-center border border-white/[0.08]"
                          style={{ backgroundColor: `${stage.color}15` }}
                          whileHover={{ scale: 1.1, rotate: 5 }}
                          transition={{ type: 'spring', stiffness: 300, damping: 15 }}
                        >
                          <stage.icon
                            size={22}
                            style={{ color: stage.color }}
                          />
                        </motion.div>

                        <div>
                          <span
                            className="text-xs font-bold tracking-[0.2em] uppercase"
                            style={{ color: stage.color }}
                          >
                            {stage.label}
                          </span>
                          <h3 className="text-lg font-semibold text-white">
                            {stage.title}
                          </h3>
                        </div>
                      </div>

                      <p className="text-sm text-gray-400 leading-relaxed">
                        {stage.description}
                      </p>
                    </div>

                    {/* Connection line to center */}
                    <div
                      className={`absolute top-1/2 -translate-y-1/2 w-8 h-px bg-gradient-to-r ${
                        isLeft
                          ? 'right-0 from-transparent to-white/[0.1]'
                          : 'left-0 from-white/[0.1] to-transparent'
                      } hidden lg:block`}
                    />
                  </div>
                </motion.div>

                {/* Spacer for opposite side */}
                <div className="hidden lg:block lg:w-[calc(50%-40px)]" />
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default IntelligenceSystem;