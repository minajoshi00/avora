'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { Sparkles, Brain, Heart, Zap, Shield, Clock } from 'lucide-react';

const features = [
  {
    id: 'context',
    icon: Sparkles,
    label: 'Context Awareness',
    title: 'Understands the moment',
    description: 'AVORA perceives your current situation, recent activity, and environmental cues. It doesn\'t just respond to words — it understands the full picture.',
    color: '#60A5FA',
  },
  {
    id: 'memory',
    icon: Brain,
    label: 'Persistent Memory',
    title: 'Remembers what matters',
    description: 'Every conversation, preference, and detail is preserved. AVORA builds a continuous understanding of you over time, not just within a single session.',
    color: '#A78BFA',
  },
  {
    id: 'emotion',
    icon: Heart,
    label: 'Emotional Intelligence',
    title: 'Feels the nuance',
    description: 'AVORA recognizes emotional context, adapts its tone, and responds with genuine empathy. It understands not just what you say, but how you feel.',
    color: '#F472B6',
  },
  {
    id: 'proactive',
    icon: Zap,
    label: 'Proactive Assistance',
    title: 'Helps before you ask',
    description: 'AVORA anticipates needs based on context and patterns. It surfaces relevant information, suggests actions, and assists without being prompted.',
    color: '#34D399',
  },
  {
    id: 'continuity',
    icon: Clock,
    label: 'Continuous Learning',
    title: 'Evolves with you',
    description: 'Every interaction makes AVORA smarter. It learns your preferences, adapts to your style, and becomes more personalized over time.',
    color: '#22D3EE',
  },
  {
    id: 'trust',
    icon: Shield,
    label: 'Privacy First',
    title: 'Your data stays yours',
    description: 'Built with privacy at its core. AVORA respects your data, operates with transparency, and gives you complete control over your information.',
    color: '#FB923C',
  },
];

export function NotAChatbot() {
  const [activeFeature, setActiveFeature] = useState(features[0].id);

  return (
    <section className="relative py-32 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 right-0 w-[500px] h-[500px] rounded-full bg-purple-500/3 blur-3xl" />
        <div className="absolute bottom-1/3 left-0 w-[400px] h-[400px] rounded-full bg-blue-500/3 blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-16"
        >
          <SectionHeading
            label="Not a Chatbot"
            title="The difference is everything"
            description="Most AI waits for prompts. AVORA understands the moment."
          />
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8 items-start">
          {/* Feature selector */}
          <div className="space-y-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              const isActive = activeFeature === feature.id;

              return (
                <motion.button
                  key={feature.id}
                  onClick={() => setActiveFeature(feature.id)}
                  className="w-full text-left group"
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.08, duration: 0.5 }}
                >
                  <div
                    className={`relative px-5 py-4 rounded-xl border transition-all duration-500 ${
                      isActive
                        ? 'bg-white/[0.06] border-white/[0.15] shadow-[0_0_30px_rgba(96,165,250,0.1)]'
                        : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04] hover:border-white/[0.1]'
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <motion.div
                        className={`w-10 h-10 rounded-lg flex items-center justify-center border transition-colors ${
                          isActive ? 'border-white/[0.15]' : 'border-white/[0.08]'
                        }`}
                        style={{ backgroundColor: `${feature.color}15` }}
                        whileHover={{ scale: 1.1, rotate: 5 }}
                      >
                        <Icon size={18} style={{ color: feature.color }} />
                      </motion.div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className="text-[10px] font-medium tracking-wider uppercase"
                            style={{ color: feature.color }}
                          >
                            {feature.label}
                          </span>
                          {isActive && (
                            <motion.div
                              layoutId="activeIndicator"
                              className="w-1 h-1 rounded-full"
                              style={{ backgroundColor: feature.color }}
                            />
                          )}
                        </div>
                        <h4
                          className={`text-sm font-semibold transition-colors ${
                            isActive ? 'text-white' : 'text-gray-400'
                          }`}
                        >
                          {feature.title}
                        </h4>
                      </div>
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </div>

          {/* Feature details */}
          <div className="lg:sticky lg:top-32">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeFeature}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                className="relative rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-8 lg:p-10 overflow-hidden"
              >
                {/* Dynamic background glow */}
                <motion.div
                  className="absolute inset-0 opacity-30"
                  style={{
                    background: `radial-gradient(circle at 30% 30%, ${features.find(f => f.id === activeFeature)?.color}15 0%, transparent 60%)`,
                  }}
                  transition={{ duration: 0.5 }}
                />

                <div className="relative z-10">
                  <motion.div
                    className="w-14 h-14 rounded-xl flex items-center justify-center border border-white/[0.08] mb-6"
                    style={{ backgroundColor: `${features.find(f => f.id === activeFeature)?.color}15` }}
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                  >
                    {(() => {
                      const Icon = features.find(f => f.id === activeFeature)?.icon;
                      return Icon ? (
                        <Icon size={24} style={{ color: features.find(f => f.id === activeFeature)?.color }} />
                      ) : null;
                    })()}
                  </motion.div>

                  <motion.span
                    className="inline-block text-[10px] font-medium tracking-[0.2em] uppercase mb-3"
                    style={{ color: features.find(f => f.id === activeFeature)?.color }}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    {features.find(f => f.id === activeFeature)?.label}
                  </motion.span>

                  <motion.h3
                    className="text-2xl lg:text-3xl font-bold text-white mb-4"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                  >
                    {features.find(f => f.id === activeFeature)?.title}
                  </motion.h3>

                  <motion.p
                    className="text-base text-gray-400 leading-relaxed"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    {features.find(f => f.id === activeFeature)?.description}
                  </motion.p>

                  <motion.div
                    className="mt-8 pt-6 border-t border-white/[0.06]"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                  >
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        Active by default
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                        Continuously improving
                      </div>
                    </div>
                  </motion.div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}

export default NotAChatbot;