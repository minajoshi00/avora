'use client';

import { motion } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';
import {
  Monitor,
  Brain,
  Mic,
  Eye,
  Database,
  Heart,
  Code,
  GraduationCap,
  Gamepad2,
  LayoutDashboard,
} from 'lucide-react';

const ecosystemItems = [
  { icon: Monitor, label: 'AVORA Desktop', description: 'Core application with full intelligence capabilities', color: '#60A5FA' },
  { icon: Brain, label: 'AVORA AI Brain', description: 'Deep reasoning and neural processing engine', color: '#A78BFA' },
  { icon: Mic, label: 'AVORA Voice', description: 'Natural speech interaction and voice commands', color: '#22D3EE' },
  { icon: Eye, label: 'AVORA Vision', description: 'Visual recognition and image understanding', color: '#F472B6' },
  { icon: Database, label: 'AVORA Memory', description: 'Persistent context and personalized recall', color: '#34D399' },
  { icon: Heart, label: 'AVORA Companion', description: 'Adaptive AI companion that grows with you', color: '#FB923C' },
  { icon: Code, label: 'Developer Tools', description: 'API access, plugins, and integration SDK', color: '#38BDF8' },
  { icon: GraduationCap, label: 'Student Mode', description: 'Learning assistance and educational support', color: '#A78BFA' },
  { icon: Gamepad2, label: 'Gaming Mode', description: 'Game-aware intelligence and assistance', color: '#F472B6' },
  { icon: LayoutDashboard, label: 'Productivity', description: 'Task automation and workflow optimization', color: '#34D399' },
];

export function Ecosystem() {
  return (
    <section id="ecosystem" className="relative py-32 overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-purple-500/3 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] rounded-full bg-blue-500/3 blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-16"
        >
          <SectionHeading
            label="Ecosystem"
            title="One connected intelligence"
            description="AVORA is not just an app — it's an entire ecosystem of intelligent capabilities working together."
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-16"
        >
          {/* Central core */}
          <div className="flex justify-center mb-16">
            <motion.div
              className="relative"
              whileHover={{ scale: 1.05 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
              <InteractiveAvoraCore state="focused" size={100} />
              <div className="absolute -inset-10 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-cyan-500/5 rounded-full blur-2xl" />
            </motion.div>
          </div>

          {/* Ecosystem grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {ecosystemItems.map((item, index) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.6, delay: index * 0.05, ease: [0.16, 1, 0.3, 1] }}
                whileHover={{ y: -6, scale: 1.02 }}
                className="group relative"
              >
                <div className="relative px-5 py-5 rounded-2xl border border-white/[0.06] bg-white/[0.02] backdrop-blur-xl hover:border-white/[0.15] transition-all duration-500 h-full">
                  {/* Gradient hover overlay */}
                  <div
                    className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                    style={{
                      background: `linear-gradient(135deg, ${item.color}10, transparent)`,
                    }}
                  />

                  <div className="relative z-10">
                    <motion.div
                      className="w-10 h-10 rounded-xl flex items-center justify-center border border-white/[0.06] mb-3"
                      style={{ backgroundColor: `${item.color}15` }}
                      whileHover={{ scale: 1.1, rotate: 5 }}
                      transition={{ type: 'spring', stiffness: 300, damping: 15 }}
                    >
                      <item.icon size={18} style={{ color: item.color }} />
                    </motion.div>
                    <h4 className="text-sm font-semibold text-gray-200 group-hover:text-white transition-colors mb-1">
                      {item.label}
                    </h4>
                    <p className="text-xs text-gray-500 group-hover:text-gray-400 transition-colors leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export default Ecosystem;