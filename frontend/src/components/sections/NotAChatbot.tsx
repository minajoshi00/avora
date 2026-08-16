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
      {/* Subtle background - reduced from multiple large gradients */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 right-0 w-[300px] h-[300px] rounded-full bg-purple-500/2 blur-xl" />
        <div className="absolute bottom-1/4 left-0 w-[250px] h-[250px] rounded-full bg-blue-500/2 blur-xl" />
      </div>

      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-12"
        >
          <SectionHeading
            label="Not a Chatbot"
            title="The difference is everything"
            description="Most AI waits for prompts. AVORA understands the moment."
          />
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-6 items-start">
          {/* Feature selector - simplified */}
          <div className="space-y-2">
            {features.map((feature) => {
              const Icon = feature.icon;

              return (
                <motion.button
                  key={feature.id}
                  onClick={() => setActiveFeature(feature.id)}
className="w-full text-left px-4 py-3 rounded-xl border transition-colors duration-300 ${
                  activeFeature === feature.id
                    ? 'bg-white/[0.03] border-white/[0.1] text-white'
                    : 'bg-white/[0.01] border-white/[0.04] hover:text-gray-200 hover:border-white/[0.08]'
                }"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded flex items-center justify-center shrink-0" style={{ backgroundColor: `${feature.color}12` }}>
                      <Icon size={16} style={{ color: feature.color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-medium tracking-wider uppercase" style={{ color: feature.color }}>
                          {feature.label}
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold transition-colors ${
                  activeFeature === feature.id ? 'text-white' : 'text-gray-400'
                }">
                        {feature.title}
                      </h4>
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </div>

          {/* Feature details - simplified card */}
          <div className="lg:sticky lg:top-24">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeFeature}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                className="rounded-2xl border border-white/[0.05] bg-white/[0.01] backdrop-blur-sm p-6 overflow-hidden"
              >
                <div className="relative z-10">
                  <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                    {features.find(f => f.id === activeFeature)?.title}
                  </h4>

                  <p className="text-base text-gray-400 leading-relaxed">
                    {features.find(f => f.id === activeFeature)?.description}
                  </p>

                  <div className="mt-6 pt-4 border-t border-white/[0.03]">
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

export default NotAChatbot;