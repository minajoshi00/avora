'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';
import {
  User,
  Eye,
  Zap,
  PartyPopper,
  RotateCcw,
  Coffee,
} from 'lucide-react';

const moments = [
  {
    id: 'focused',
    icon: User,
    label: 'User Focused',
    title: 'You\'re in the zone.',
    description: 'AVORA fades into the background. It watches silently, ready but never intrusive. You work, create, and focus — AVORA stays quiet.',
    state: 'focused' as const,
    color: '#60A5FA',
  },
  {
    id: 'stuck',
    icon: Eye,
    label: 'User Stuck',
    title: 'AVORA notices.',
    description: 'Something feels off. You pause, hesitate, or struggle. AVORA senses the moment and gently surfaces itself, aware of what you might need.',
    state: 'listening' as const,
    color: '#A78BFA',
  },
  {
    id: 'helping',
    icon: Zap,
    label: 'Activated',
    title: 'Help arrives smoothly.',
    description: 'Not with a pop-up. Not with an interruption. But with a quiet presence — ready to assist, guide, or simply acknowledge your progress.',
    state: 'thinking' as const,
    color: '#22D3EE',
  },
  {
    id: 'success',
    icon: PartyPopper,
    label: 'User Succeeds',
    title: 'AVORA celebrates.',
    description: 'You accomplish something. AVORA acknowledges the win — subtly, genuinely. Because the best companionship means being happy for each other.',
    state: 'excited' as const,
    color: '#34D399',
  },
  {
    id: 'returning',
    icon: RotateCcw,
    label: 'User Returns',
    title: 'AVORA remembers.',
    description: 'You step away, then come back. AVORA picks up right where you left off — same context, same continuity, same understanding.',
    state: 'speaking' as const,
    color: '#F472B6',
  },
  {
    id: 'break',
    icon: Coffee,
    label: 'User Rests',
    title: 'AVORA understands.',
    description: 'You take a break. AVORA respects that. Not every moment needs action. Sometimes, the best intelligence is simply being present.',
    state: 'idle' as const,
    color: '#FB923C',
  },
];

export function CompanionExperience() {
  const [activeMoment, setActiveMoment] = useState(moments[0].id);

  return (
    <section className="relative py-32 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-blue-500/3 blur-3xl" />
        <div className="absolute top-0 right-1/4 w-[300px] h-[300px] rounded-full bg-purple-500/3 blur-3xl" />
        <div className="absolute bottom-0 left-1/4 w-[300px] h-[300px] rounded-full bg-cyan-500/3 blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-20"
        >
          <SectionHeading
            label="The Companion"
            title="Already there."
            description="You don't open AVORA. AVORA is already there — understanding, waiting, evolving with you."
          />
        </motion.div>

        {/* Timeline visualization */}
        <div className="relative mb-20">
          {/* Central timeline line */}
          <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-blue-500/20 via-purple-500/20 to-cyan-500/20 -translate-x-1/2" />

          <div className="space-y-12 lg:space-y-0">
            {moments.map((moment, index) => {
              const Icon = moment.icon;
              const isActive = activeMoment === moment.id;
              const isLeft = index % 2 === 0;

              return (
                <motion.div
                  key={moment.id}
                  initial={{ opacity: 0, y: 40 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-50px' }}
                  transition={{ duration: 0.7, delay: index * 0.1 }}
                  className={`relative flex items-center gap-6 lg:gap-12 mb-12 lg:mb-0 ${
                    isLeft ? 'lg:flex-row' : 'lg:flex-row-reverse'
                  } flex-col`}
                >
                  {/* Timeline node */}
                  <div className="hidden lg:flex absolute left-1/2 -translate-x-1/2 items-center justify-center">
                    <motion.div
                      className="relative"
                      whileHover={{ scale: 1.2 }}
                    >
                      <div
                        className="w-4 h-4 rounded-full border-2 transition-all duration-500"
                        style={{
                          borderColor: moment.color,
                          backgroundColor: isActive ? moment.color : 'transparent',
                          boxShadow: isActive ? `0 0 20px ${moment.color}40` : 'none',
                        }}
                      />
                      {isActive && (
                        <motion.div
                          className="absolute inset-0 rounded-full"
                          style={{
                            borderColor: moment.color,
                            opacity: 0.5,
                          }}
                          animate={{ scale: [1, 2, 1], opacity: [0.5, 0, 0.5] }}
                          transition={{ duration: 2, repeat: Infinity }}
                        />
                      )}
                    </motion.div>
                  </div>

                  {/* Content */}
                  <motion.button
                    onClick={() => setActiveMoment(moment.id)}
                    className={`flex-1 w-full text-left ${
                      isLeft ? 'lg:text-right' : 'lg:text-left'
                    }`}
                  >
                    <div
                      className={`relative px-6 py-5 rounded-2xl border transition-all duration-500 ${
                        isActive
                          ? 'bg-white/[0.06] border-white/[0.15] shadow-[0_0_40px_rgba(96,165,250,0.1)]'
                          : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04]'
                      }`}
                    >
                      <div className={`flex items-start gap-4 ${isLeft ? 'lg:flex-row-reverse' : ''}`}>
                        <motion.div
                          className="w-12 h-12 rounded-xl flex items-center justify-center border border-white/[0.08] shrink-0"
                          style={{ backgroundColor: `${moment.color}15` }}
                          whileHover={{ scale: 1.1, rotate: 5 }}
                        >
                          <Icon size={20} style={{ color: moment.color }} />
                        </motion.div>
                        <div className="flex-1 min-w-0">
                          <span
                            className="text-[10px] font-medium tracking-wider uppercase block mb-1"
                            style={{ color: moment.color }}
                          >
                            {moment.label}
                          </span>
                          <h4
                            className={`text-base font-semibold mb-1 transition-colors ${
                              isActive ? 'text-white' : 'text-gray-400'
                            }`}
                          >
                            {moment.title}
                          </h4>
                          <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">
                            {moment.description.slice(0, 100)}...
                          </p>
                        </div>
                      </div>
                    </div>
                  </motion.button>

                  {/* Spacer for opposite side */}
                  <div className="hidden lg:block flex-1" />
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Active moment detail */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeMoment}
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -30, scale: 0.95 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="relative max-w-4xl mx-auto"
          >
            <div className="relative rounded-3xl border border-white/[0.1] bg-white/[0.03] backdrop-blur-xl p-8 lg:p-12 overflow-hidden">
              {/* Animated background */}
              <motion.div
                className="absolute inset-0 opacity-40"
                style={{
                  background: `radial-gradient(circle at 50% 50%, ${moments.find(m => m.id === activeMoment)?.color}15 0%, transparent 60%)`,
                }}
                animate={{
                  scale: [1, 1.05, 1],
                }}
                transition={{ duration: 4, repeat: Infinity }}
              />

              <div className="relative z-10 flex flex-col lg:flex-row items-center gap-8">
                {/* Core visualization */}
                <motion.div
                  className="shrink-0"
                  animate={{
                    rotate: [0, 5, -5, 0],
                  }}
                  transition={{ duration: 6, repeat: Infinity }}
                >
                  <InteractiveAvoraCore
                    state={moments.find(m => m.id === activeMoment)?.state || 'idle'}
                    size={140}
                  />
                </motion.div>

                {/* Content */}
                <div className="flex-1 text-center lg:text-left">
                  <motion.div
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/[0.1] bg-white/[0.04] mb-4"
                    style={{
                      borderColor: `${moments.find(m => m.id === activeMoment)?.color}30`,
                    }}
                  >
                    <div
                      className="w-1.5 h-1.5 rounded-full"
                      style={{ backgroundColor: moments.find(m => m.id === activeMoment)?.color }}
                    />
                    <span
                      className="text-[10px] font-medium tracking-wider uppercase"
                      style={{ color: moments.find(m => m.id === activeMoment)?.color }}
                    >
                      {moments.find(m => m.id === activeMoment)?.label}
                    </span>
                  </motion.div>

                  <motion.h3
                    className="text-2xl lg:text-3xl font-bold text-white mb-4"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    {moments.find(m => m.id === activeMoment)?.title}
                  </motion.h3>

                  <motion.p
                    className="text-base text-gray-400 leading-relaxed"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    {moments.find(m => m.id === activeMoment)?.description}
                  </motion.p>

                  <motion.div
                    className="mt-6 flex items-center justify-center lg:justify-start gap-6 text-xs text-gray-500"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      Always present
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                      Never intrusive
                    </div>
                  </motion.div>
                </div>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}

export default CompanionExperience;