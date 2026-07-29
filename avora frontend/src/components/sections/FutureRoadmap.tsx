'use client';

import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import {
  Mic,
  Eye,
  Monitor,
  Gamepad2,
  Code,
  GraduationCap,
  Database,
  WifiOff,
  Workflow,
  Heart,
} from 'lucide-react';

const roadmapItems = [
  {
    icon: Mic,
    label: 'Voice Intelligence',
    description: 'Natural voice conversations with emotion recognition and context awareness.',
    date: 'Q3 2026',
    color: '#22D3EE',
    status: 'in-progress',
  },
  {
    icon: Eye,
    label: 'Vision Intelligence',
    description: 'Real-time visual understanding, object recognition, and scene analysis.',
    date: 'Q3 2026',
    color: '#F472B6',
    status: 'in-progress',
  },
  {
    icon: Monitor,
    label: 'Computer Control',
    description: 'Natural language control of your desktop applications and workflows.',
    date: 'Q4 2026',
    color: '#60A5FA',
    status: 'planned',
  },
  {
    icon: Gamepad2,
    label: 'Gaming AI',
    description: 'Real-time game assistance, strategy analysis, and immersive companions.',
    date: 'Q4 2026',
    color: '#FB923C',
    status: 'planned',
  },
  {
    icon: Code,
    label: 'Coding Intelligence',
    description: 'Full IDE integration with intelligent code generation and debugging.',
    date: 'Q1 2027',
    color: '#38BDF8',
    status: 'planned',
  },
  {
    icon: GraduationCap,
    label: 'Student Intelligence',
    description: 'Personalized learning paths with adaptive teaching strategies.',
    date: 'Q1 2027',
    color: '#A78BFA',
    status: 'planned',
  },
  {
    icon: Database,
    label: 'Advanced Memory',
    description: 'Lifelong learning with perfect recall across all contexts.',
    date: 'Q1 2027',
    color: '#34D399',
    status: 'planned',
  },
  {
    icon: WifiOff,
    label: 'Full Offline AI',
    description: 'Complete local intelligence with no cloud dependency.',
    date: 'Q2 2027',
    color: '#F472B6',
    status: 'planned',
  },
  {
    icon: Workflow,
    label: 'Autonomous Workflows',
    description: 'Self-executing multi-step tasks with intelligent decision-making.',
    date: 'Q2 2027',
    color: '#60A5FA',
    status: 'planned',
  },
  {
    icon: Heart,
    label: 'Companion Evolution',
    description: 'Deep personalization with emotional intelligence and adaptive personality.',
    date: 'Q3 2027',
    color: '#FB923C',
    status: 'planned',
  },
];

export function FutureRoadmap() {
  const sectionRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start end', 'end start'],
  });

  const progressWidth = useTransform(scrollYProgress, [0, 1], ['0%', '100%']);

  return (
    <section
      ref={sectionRef}
      id="roadmap"
      className="relative py-32 overflow-hidden"
    >
      <div className="max-w-6xl mx-auto px-6">
        <SectionHeading
          label="The Future"
          title="What's coming"
          description="AVORA is constantly evolving. Here's what we're building next."
        />

        {/* Progress bar */}
        <div className="sticky top-24 z-10 mb-16">
          <div className="h-0.5 bg-white/[0.06] rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
              style={{ width: progressWidth }}
            />
          </div>
        </div>

        <div className="space-y-8">
          {roadmapItems.map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{
                duration: 0.7,
                delay: index * 0.08,
                ease: [0.16, 1, 0.3, 1],
              }}
              className="group"
            >
              <div className="relative flex items-start gap-6 p-5 rounded-2xl border border-white/[0.04] hover:border-white/[0.1] bg-white/[0.01] hover:bg-white/[0.03] transition-all duration-500">
                {/* Timeline dot */}
                <div className="relative flex-shrink-0 mt-1">
                  <div
                    className="w-3 h-3 rounded-full border-2"
                    style={{
                      borderColor: item.color,
                      backgroundColor: item.status === 'in-progress' ? item.color : 'transparent',
                    }}
                  >
                    {item.status === 'in-progress' && (
                      <motion.div
                        className="w-full h-full rounded-full"
                        style={{ backgroundColor: item.color }}
                        animate={{ scale: [1, 1.5, 1], opacity: [0.6, 0, 0.6] }}
                        transition={{ duration: 2, repeat: Infinity }}
                      />
                    )}
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2 flex-wrap">
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: `${item.color}15` }}
                    >
                      <item.icon size={16} style={{ color: item.color }} />
                    </div>
                    <h3 className="text-base font-semibold text-white group-hover:text-blue-200 transition-colors">
                      {item.label}
                    </h3>
                    <span className="text-xs text-gray-500">{item.date}</span>
                    <span
                      className={`text-[10px] font-medium uppercase tracking-wider px-2 py-0.5 rounded-full ${
                        item.status === 'in-progress'
                          ? 'text-emerald-400 bg-emerald-500/10'
                          : 'text-gray-500 bg-white/[0.05]'
                      }`}
                    >
                      {item.status === 'in-progress' ? 'In Progress' : 'Planned'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 leading-relaxed">
                    {item.description}
                  </p>
                </div>

                {/* Arrow */}
                <div
                  className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{ backgroundColor: `${item.color}10` }}
                >
                  <motion.div
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ backgroundColor: item.color }}
                    animate={{ x: [0, 3, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default FutureRoadmap;