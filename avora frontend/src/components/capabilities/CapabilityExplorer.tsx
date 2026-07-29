'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Mic, Eye, Wand2, Brain, User } from 'lucide-react';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';
import { SectionHeading } from '../ui/SectionHeading';
import { cn } from '../../lib/utils';

type Capability = 'conversation' | 'voice' | 'vision' | 'creation' | 'memory' | 'personalization';

interface CapabilityConfig {
  id: Capability;
  label: string;
  icon: React.ElementType;
  description: string;
  state: 'idle' | 'listening' | 'thinking' | 'speaking' | 'excited' | 'focused';
  color: string;
}

const capabilities: CapabilityConfig[] = [
  {
    id: 'conversation',
    label: 'Conversation',
    icon: MessageSquare,
    description: 'Natural dialogue that understands context, nuance, and meaning beyond words.',
    state: 'speaking',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'voice',
    label: 'Voice',
    icon: Mic,
    description: 'Speak naturally. AVORA listens with perfect comprehension and responds in real-time.',
    state: 'listening',
    color: 'from-purple-500 to-pink-500',
  },
  {
    id: 'vision',
    label: 'Vision',
    icon: Eye,
    description: 'See the world through AVORA\'s eyes. Understand images, screens, and visual context.',
    state: 'focused',
    color: 'from-cyan-500 to-blue-500',
  },
  {
    id: 'creation',
    label: 'Creation',
    icon: Wand2,
    description: 'Transform imagination into reality. Generate images, text, and ideas instantly.',
    state: 'excited',
    color: 'from-violet-500 to-purple-500',
  },
  {
    id: 'memory',
    label: 'Memory',
    icon: Brain,
    description: 'AVORA remembers what matters. Every conversation builds deeper understanding.',
    state: 'thinking',
    color: 'from-indigo-500 to-blue-500',
  },
  {
    id: 'personalization',
    label: 'Personalization',
    icon: User,
    description: 'Truly yours. AVORA adapts to your style, preferences, and way of thinking.',
    state: 'idle',
    color: 'from-blue-500 to-purple-500',
  },
];

export function CapabilityExplorer() {
  const [selected, setSelected] = useState<Capability>('conversation');

  const activeCapability = capabilities.find((c) => c.id === selected)!;

  return (
    <section id="features" className="relative py-32">
      <div className="max-w-7xl mx-auto px-6">
        <SectionHeading
          label="Capabilities"
          title="More than intelligence"
          description="Explore what becomes possible when an AI truly understands."
        />

        <div className="mt-20 grid lg:grid-cols-2 gap-16 items-center">
          {/* Capability selector */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {capabilities.map((cap) => {
              const Icon = cap.icon;
              const isActive = selected === cap.id;

              return (
                <motion.button
                  key={cap.id}
                  onClick={() => setSelected(cap.id)}
                  className={cn(
                    'relative p-4 rounded-2xl border transition-all duration-500 text-left group hover-target',
                    isActive
                      ? 'bg-white/[0.06] border-white/[0.12]'
                      : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04] hover:border-white/[0.1]'
                  )}
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 17 }}
                >
                  <motion.div
                    animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                    transition={{ duration: 0.3 }}
                  >
                    <Icon
                      size={20}
                      className={cn(
                        'mb-3 transition-colors duration-300',
                        isActive ? 'text-white' : 'text-gray-500 group-hover:text-gray-300'
                      )}
                    />
                  </motion.div>
                  <span
                    className={cn(
                      'text-sm font-medium block transition-colors duration-300',
                      isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'
                    )}
                  >
                    {cap.label}
                  </span>
                  {isActive && (
                    <motion.div
                      layoutId="capability-indicator"
                      className="absolute inset-0 rounded-2xl bg-gradient-to-br opacity-10 pointer-events-none"
                      style={{ background: `linear-gradient(135deg, ${cap.color})` }}
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                </motion.button>
              );
            })}
          </div>

          {/* Interactive demo panel */}
          <div className="relative">
            <AnimatePresence mode="wait">
              <motion.div
                key={selected}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                className="relative rounded-3xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-8 sm:p-10"
              >
                {/* Gradient accent */}
                <div
                  className={cn(
                    'absolute inset-0 rounded-3xl opacity-20 pointer-events-none',
                    `bg-gradient-to-br ${activeCapability.color}`
                  )}
                  style={{ opacity: 0.1 }}
                />

                <div className="relative z-10 flex flex-col items-center text-center">
                  <div className="mb-8">
                    <InteractiveAvoraCore state={activeCapability.state} size={180} />
                  </div>

                  <h3 className="text-2xl sm:text-3xl font-bold text-white mb-4">
                    {activeCapability.label}
                  </h3>
                  <p className="text-gray-400 max-w-md leading-relaxed">
                    {activeCapability.description}
                  </p>

                  {/* Mini interactive demo based on capability */}
                  <div className="mt-8 w-full">
                    {selected === 'conversation' && (
                      <ConversationDemo />
                    )}
                    {selected === 'voice' && (
                      <VoiceDemo />
                    )}
                    {selected === 'vision' && (
                      <VisionDemo />
                    )}
                    {selected === 'creation' && (
                      <CreationDemo />
                    )}
                    {selected === 'memory' && (
                      <MemoryDemo />
                    )}
                    {selected === 'personalization' && (
                      <PersonalizationDemo />
                    )}
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}

function ConversationDemo() {
  return (
    <div className="space-y-3">
      <div className="flex justify-start">
        <div className="px-4 py-2.5 rounded-2xl rounded-tl-sm bg-white/[0.06] text-sm text-gray-300 max-w-[80%]">
          Tell me about the future of AI
        </div>
      </div>
      <div className="flex justify-end">
        <div className="px-4 py-2.5 rounded-2xl rounded-tr-sm bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/20 text-sm text-white max-w-[80%]">
          The future of AI isn't just about intelligence — it's about understanding, empathy, and
          partnership...
        </div>
      </div>
    </div>
  );
}

function VoiceDemo() {
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="flex items-end gap-1 h-12">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="w-1 bg-gradient-to-t from-blue-500 to-purple-500 rounded-full"
            animate={{
              height: [4, 20 + Math.random() * 20, 4],
            }}
            transition={{
              duration: 1 + Math.random() * 0.5,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: i * 0.05,
            }}
          />
        ))}
      </div>
      <p className="text-xs text-gray-500">Listening...</p>
    </div>
  );
}

function VisionDemo() {
  return (
    <div className="relative rounded-xl overflow-hidden border border-white/[0.08] bg-white/[0.02] p-6">
      <div className="flex items-center gap-3 mb-4">
        <Eye size={16} className="text-blue-400" />
        <span className="text-xs uppercase tracking-wider text-gray-500">Analyzing visual context</span>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="aspect-square rounded-lg bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-white/[0.06]"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
          />
        ))}
      </div>
    </div>
  );
}

function CreationDemo() {
  return (
    <div className="relative rounded-xl overflow-hidden border border-white/[0.08] bg-white/[0.02] p-6">
      <div className="flex items-center gap-3 mb-4">
        <Wand2 size={16} className="text-purple-400" />
        <span className="text-xs uppercase tracking-wider text-gray-500">Generating from imagination</span>
      </div>
      <motion.div
        className="aspect-video rounded-lg bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20"
        animate={{
          opacity: [0.5, 1, 0.5],
          scale: [0.98, 1, 0.98],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
    </div>
  );
}

function MemoryDemo() {
  const nodes = ['preference', 'conversation', 'context', 'response'];
  return (
    <div className="flex items-center justify-center gap-2 flex-wrap">
      {nodes.map((node, i) => (
        <div key={node} className="flex items-center gap-2">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.2 }}
            className="px-3 py-1.5 rounded-lg bg-white/[0.06] border border-white/[0.08] text-xs text-gray-300"
          >
            {node}
          </motion.div>
          {i < nodes.length - 1 && (
            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ delay: i * 0.2 + 0.1 }}
              className="w-4 h-px bg-gradient-to-r from-blue-500/50 to-purple-500/50"
            />
          )}
        </div>
      ))}
    </div>
  );
}

function PersonalizationDemo() {
  return (
    <div className="grid grid-cols-3 gap-3">
      {['Your style', 'Your pace', 'Your interests'].map((trait, i) => (
        <motion.div
          key={trait}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.15 }}
          className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-center"
        >
          <div className="w-8 h-8 mx-auto mb-2 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
            <User size={14} className="text-gray-300" />
          </div>
          <p className="text-xs text-gray-400">{trait}</p>
        </motion.div>
      ))}
    </div>
  );
}

export default CapabilityExplorer;