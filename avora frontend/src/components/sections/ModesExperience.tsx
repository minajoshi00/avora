'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';
import { Code, GraduationCap, Gamepad2, LayoutDashboard, Check } from 'lucide-react';

const modes = [
  {
    id: 'coding',
    icon: Code,
    label: 'CODING',
    title: 'Developer Mode',
    color: '#38BDF8',
    description: 'AVORA understands code architecture, debugs errors, and helps you build faster.',
    abilities: [
      'Multi-language code generation',
      'Real-time debugging assistance',
      'Architecture and design patterns',
      'Code review and optimization',
      'Documentation generation',
    ],
    example: 'Write a React hook that manages WebSocket connections with auto-reconnect logic.',
  },
  {
    id: 'student',
    icon: GraduationCap,
    label: 'STUDENT',
    title: 'Learning Mode',
    color: '#A78BFA',
    description: 'AVORA adapts to your learning style and helps you master any subject.',
    abilities: [
      'Personalized tutoring',
      'Concept explanation at any level',
      'Practice problem generation',
      'Study plan creation',
      'Progress tracking',
    ],
    example: 'Explain quantum entanglement like I\'m 12 years old, then give me practice questions.',
  },
  {
    id: 'gamer',
    icon: Gamepad2,
    label: 'GAMER',
    title: 'Gaming Mode',
    color: '#F472B6',
    description: 'AVORA enhances your gaming experience with real-time intelligence.',
    abilities: [
      'Game strategy analysis',
      'Real-time tips and guidance',
      'Lore and world-building',
      'Build optimization',
      'Game mechanic explanations',
    ],
    example: 'What\'s the optimal build order for a fast expansion strategy in this RTS game?',
  },
  {
    id: 'productivity',
    icon: LayoutDashboard,
    label: 'PRODUCTIVITY',
    title: 'Focus Mode',
    color: '#34D399',
    description: 'AVORA streamlines your workflow and automates repetitive tasks.',
    abilities: [
      'Task automation',
      'Email and message drafting',
      'Meeting summarization',
      'Project planning',
      'Data analysis and reporting',
    ],
    example: 'Summarize my meeting notes and create an action plan with deadlines.',
  },
];

export function ModesExperience() {
  const [activeMode, setActiveMode] = useState<string>('coding');

  const currentMode = modes.find((m) => m.id === activeMode) || modes[0];

  return (
    <section id="modes" className="relative py-32">
      <div className="max-w-7xl mx-auto px-6">
        <SectionHeading
          label="Modes"
          title="Intelligence that adapts"
          description="AVORA transforms its capabilities to match your context — coding, learning, gaming, or working."
        />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-16"
        >
          {/* Mode selector */}
          <div className="flex justify-center gap-2 mb-12 flex-wrap">
            {modes.map((mode) => {
              const isActive = activeMode === mode.id;
              return (
                <motion.button
                  key={mode.id}
                  onClick={() => setActiveMode(mode.id)}
                  className={`relative flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-medium border transition-all duration-300 ${
                    isActive
                      ? 'text-white border-white/[0.15]'
                      : 'text-gray-400 border-white/[0.06] hover:text-gray-200 hover:border-white/[0.1]'
                  }`}
                  style={{
                    backgroundColor: isActive ? `${mode.color}15` : 'transparent',
                  }}
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <mode.icon size={16} style={{ color: isActive ? mode.color : undefined }} />
                  {mode.label}
                </motion.button>
              );
            })}
          </div>

          {/* Mode content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentMode.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="max-w-5xl mx-auto"
            >
              <div className="grid lg:grid-cols-2 gap-8">
                {/* Left: Mode info */}
                <div className="space-y-6">
                  <div className="flex items-center gap-4">
                    <motion.div
                      className="w-14 h-14 rounded-2xl flex items-center justify-center border"
                      style={{
                        backgroundColor: `${currentMode.color}15`,
                        borderColor: `${currentMode.color}30`,
                      }}
                      animate={{ scale: [1, 1.05, 1] }}
                      transition={{ duration: 3, repeat: Infinity }}
                    >
                      <currentMode.icon size={28} style={{ color: currentMode.color }} />
                    </motion.div>
                    <div>
                      <span
                        className="text-xs font-bold tracking-[0.2em] uppercase"
                        style={{ color: currentMode.color }}
                      >
                        {currentMode.label}
                      </span>
                      <h3 className="text-2xl font-bold text-white">{currentMode.title}</h3>
                    </div>
                  </div>

                  <p className="text-gray-400 leading-relaxed">
                    {currentMode.description}
                  </p>

                  <div className="space-y-2.5">
                    {currentMode.abilities.map((ability) => (
                      <div key={ability} className="flex items-center gap-3 text-sm text-gray-300">
                        <div
                          className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
                          style={{ backgroundColor: `${currentMode.color}20` }}
                        >
                          <Check size={10} style={{ color: currentMode.color }} />
                        </div>
                        {ability}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right: Example interaction */}
                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <InteractiveAvoraCore state="focused" size={20} />
                    <span className="text-xs font-medium text-gray-400">Example interaction</span>
                  </div>
                  <div className="flex justify-end mb-4">
                    <div className="max-w-[85%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/20 text-sm text-white">
                      {currentMode.example}
                    </div>
                  </div>
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="flex justify-start"
                  >
                    <div
                      className="max-w-[85%] px-4 py-3 rounded-2xl rounded-tl-sm border text-sm"
                      style={{
                        backgroundColor: `${currentMode.color}10`,
                        borderColor: `${currentMode.color}20`,
                        color: currentMode.color,
                      }}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <div
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ backgroundColor: currentMode.color }}
                        />
                        <span className="text-xs font-medium" style={{ color: currentMode.color }}>
                          AVORA
                        </span>
                      </div>
                      <p className="text-gray-300">
                        I've switched to{' '}
                        <span style={{ color: currentMode.color }}>
                          {currentMode.title}
                        </span>
                        . I'm ready to help you with that.
                      </p>
                    </div>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>
        </motion.div>
      </div>
    </section>
  );
}

export default ModesExperience;