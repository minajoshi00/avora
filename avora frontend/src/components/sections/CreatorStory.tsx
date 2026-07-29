'use client';

import { motion } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import {
  MapPin,
  Briefcase,
  Cpu,
  Eye,
  Heart,
  Code2,
  Boxes,
  Sparkles,
  Rocket,
  Shield,
  Users,
  Globe,
  Mail,
  MessageSquare,
  Mic,
  Monitor,
  FileText,
  Sun,
  BookOpen,
  Lightbulb,
  Zap,
} from 'lucide-react';

const roles = [
  { label: 'Founder', color: 'from-blue-500/20 to-blue-500/5' },
  { label: 'Solo Developer', color: 'from-purple-500/20 to-purple-500/5' },
  { label: 'AI Application Developer', color: 'from-cyan-500/20 to-cyan-500/5' },
  { label: 'Python Developer', color: 'from-emerald-500/20 to-emerald-500/5' },
  { label: 'Desktop Software Developer', color: 'from-pink-500/20 to-pink-500/5' },
  { label: 'Frontend Developer', color: 'from-amber-500/20 to-amber-500/5' },
  { label: 'Backend Developer', color: 'from-violet-500/20 to-violet-500/5' },
  { label: 'UI/UX Designer', color: 'from-rose-500/20 to-rose-500/5' },
  { label: 'System Architect', color: 'from-indigo-500/20 to-indigo-500/5' },
  { label: 'Prompt Engineer', color: 'from-teal-500/20 to-teal-500/5' },
  { label: 'Product Designer', color: 'from-sky-500/20 to-sky-500/5' },
];

const skills = [
  { label: 'Python', color: 'hover:border-blue-500/40' },
  { label: 'PySide6', color: 'hover:border-cyan-500/40' },
  { label: 'Artificial Intelligence', color: 'hover:border-purple-500/40' },
  { label: 'Large Language Models', color: 'hover:border-pink-500/40' },
  { label: 'Prompt Engineering', color: 'hover:border-emerald-500/40' },
  { label: 'Desktop Applications', color: 'hover:border-amber-500/40' },
  { label: 'Automation', color: 'hover:border-violet-500/40' },
  { label: 'Computer Vision', color: 'hover:border-rose-500/40' },
  { label: 'Natural Language Processing', color: 'hover:border-teal-500/40' },
  { label: 'UI/UX Design', color: 'hover:border-sky-500/40' },
  { label: 'API Integration', color: 'hover:border-indigo-500/40' },
  { label: 'JSON', color: 'hover:border-orange-500/40' },
  { label: 'Git & GitHub', color: 'hover:border-red-500/40' },
  { label: 'Software Architecture', color: 'hover:border-fuchsia-500/40' },
  { label: 'Problem Solving', color: 'hover:border-lime-500/40' },
];

const techStack = [
  { label: 'Python', color: 'from-blue-500/10 to-blue-500/5', textColor: 'text-blue-300' },
  { label: 'PySide6', color: 'from-cyan-500/10 to-cyan-500/5', textColor: 'text-cyan-300' },
  { label: 'Gemini API', color: 'from-purple-500/10 to-purple-500/5', textColor: 'text-purple-300' },
  { label: 'Groq API', color: 'from-emerald-500/10 to-emerald-500/5', textColor: 'text-emerald-300' },
  { label: 'HTML', color: 'from-orange-500/10 to-orange-500/5', textColor: 'text-orange-300' },
  { label: 'CSS', color: 'from-blue-500/10 to-blue-500/5', textColor: 'text-blue-300' },
  { label: 'JavaScript', color: 'from-yellow-500/10 to-yellow-500/5', textColor: 'text-yellow-300' },
  { label: 'JSON', color: 'from-gray-500/10 to-gray-500/5', textColor: 'text-gray-300' },
  { label: 'Git', color: 'from-red-500/10 to-red-500/5', textColor: 'text-red-300' },
  { label: 'GitHub', color: 'from-white/10 to-white/5', textColor: 'text-gray-200' },
];

const missionItems = [
  { icon: MessageSquare, title: 'Natural Conversations', description: 'Fluid, human-like dialogue that understands context and nuance.' },
  { icon: Shield, title: 'Long-term Memory', description: 'Remembers interactions and builds genuine relationships over time.' },
  { icon: Mic, title: 'Voice Interaction', description: 'Natural speech recognition and expressive voice responses.' },
  { icon: Monitor, title: 'Desktop Awareness', description: 'Understands your screen, workflows, and environment.' },
  { icon: FileText, title: 'File Understanding', description: 'Reads, analyzes, and learns from your documents.' },
  { icon: Eye, title: 'Image Understanding', description: 'Perceives and interprets visual information intelligently.' },
  { icon: Code2, title: 'Computer Assistance', description: 'Automates tasks and assists with digital workflows.' },
  { icon: Heart, title: 'Emotional Personality', description: 'Responds with empathy, mood awareness, and personality.' },
  { icon: Globe, title: 'Context Awareness', description: 'Adapts to situations, time, and user preferences.' },
  { icon: Zap, title: 'Productivity Assistance', description: 'Helps you accomplish more with intelligent suggestions.' },
  { icon: Sun, title: 'Modern User Experience', description: 'Beautiful, intuitive interface designed for daily use.' },
];

const timeline = [
  { year: '2025', title: 'Idea', description: 'Conceived the vision for a truly personal AI companion.' },
  { year: '2025', title: 'Research', description: 'Studied LLMs, prompt engineering, and desktop automation.' },
  { year: '2025', title: 'Planning', description: 'Designed architecture, feature sets, and development roadmap.' },
  { year: '2025', title: 'UI Design', description: 'Crafted modern, emotional, and intuitive user interface.' },
  { year: '2025', title: 'Core Development', description: 'Built the foundational engine and application framework.' },
  { year: '2025', title: 'AI Integration', description: 'Connected advanced language models and reasoning systems.' },
  { year: '2026', title: 'Memory System', description: 'Implemented long-term memory and contextual recall.' },
  { year: '2026', title: 'Voice Features', description: 'Added natural speech recognition and voice responses.' },
  { year: '2026', title: 'Desktop Features', description: 'Integrated screen awareness and computer control.' },
  { year: 'Now', title: 'Current Development', description: 'Refining personality, emotion, and daily assistance.' },
  { year: 'Future', title: 'Future Expansion', description: 'Cloud sync, mobile support, and marketplace growth.' },
];

const roadmapItems = [
  { label: 'Mobile Version', color: 'border-blue-500/30 hover:border-blue-400/60' },
  { label: 'Cloud Sync', color: 'border-purple-500/30 hover:border-purple-400/60' },
  { label: 'Multiple AI Characters', color: 'border-cyan-500/30 hover:border-cyan-400/60' },
  { label: 'Custom Themes', color: 'border-pink-500/30 hover:border-pink-400/60' },
  { label: 'Plugin Marketplace', color: 'border-emerald-500/30 hover:border-emerald-400/60' },
  { label: 'Team Collaboration', color: 'border-amber-500/30 hover:border-amber-400/60' },
  { label: 'Cross Platform Support', color: 'border-violet-500/30 hover:border-violet-400/60' },
  { label: 'AI Marketplace', color: 'border-rose-500/30 hover:border-rose-400/60' },
];

const values = [
  { label: 'Innovation', icon: Lightbulb },
  { label: 'Continuous Learning', icon: BookOpen },
  { label: 'Creativity', icon: Sparkles },
  { label: 'Quality', icon: Shield },
  { label: 'User Experience', icon: Sun },
  { label: 'Privacy', icon: Eye },
  { label: 'Reliability', icon: Zap },
  { label: 'Performance', icon: Cpu },
  { label: 'Accessibility', icon: Globe },
];

const funFacts = [
  'Loves building AI.',
  'Always learning new technologies.',
  'Enjoys solving challenging problems.',
  'Interested in startup development.',
  'Passionate about software engineering.',
  'Enjoys creating modern user interfaces.',
];

export function CreatorStory() {
  return (
    <section className="relative py-32 overflow-hidden" id="developer">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-blue-500/5 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] rounded-full bg-purple-500/5 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full bg-cyan-500/3 blur-3xl" />
      </div>

      <div className="max-w-6xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-20"
        >
          <SectionHeading
            label="About the Developer"
            title="Pratik Ojha"
            description="Founder & Solo Developer — Independent AI Startup"
          />
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex items-center justify-center gap-6 mt-8 text-sm text-gray-400"
          >
            <span className="flex items-center gap-2">
              <MapPin size={14} className="text-blue-400" />
              Dhangadhi, Nepal
            </span>
            <span className="w-1 h-1 rounded-full bg-gray-600" />
            <span className="flex items-center gap-2">
              <Briefcase size={14} className="text-purple-400" />
              Independent AI Startup
            </span>
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="max-w-3xl mx-auto mb-24"
        >
          <div className="relative rounded-3xl border border-white/[0.06] bg-white/[0.02] backdrop-blur-xl p-8 md:p-12">
            <div className="absolute inset-0 rounded-3xl bg-gradient-to-b from-white/[0.04] to-transparent pointer-events-none" />
            <p className="text-lg md:text-xl text-gray-300 leading-relaxed relative">
              I am an independent developer from Nepal with a passion for building intelligent software that solves real-world problems. 
              Currently focused on developing an advanced AI companion that feels natural, emotional, proactive, and genuinely helpful. 
              I love learning new technologies and continuously improving my skills through hands-on projects. 
              This project represents my long-term vision — built independently with ambition, creativity, and a commitment to quality.
            </p>
          </div>
        </motion.div>

        <div className="mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">My Roles</h2>
            <p className="text-gray-400">Wearing many hats to bring the vision to life</p>
          </motion.div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {roles.map((role, i) => (
              <motion.div
                key={role.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05, duration: 0.5 }}
                whileHover={{ y: -6, scale: 1.02 }}
                className={`relative p-5 rounded-2xl border border-white/[0.08] bg-gradient-to-br ${role.color} backdrop-blur-xl transition-all duration-500 hover:border-white/[0.15] hover:shadow-lg hover:shadow-blue-500/5 group cursor-default`}
              >
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-t from-white/[0.02] to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <p className="text-xs font-semibold text-gray-300 text-center relative group-hover:text-white transition-colors">
                  {role.label}
                </p>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Technical Skills</h2>
            <p className="text-gray-400">Technologies and disciplines I work with daily</p>
          </motion.div>
          <div className="flex flex-wrap justify-center gap-3">
            {skills.map((skill, i) => (
              <motion.span
                key={skill.label}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.04, duration: 0.4 }}
                whileHover={{ scale: 1.08, y: -2 }}
                className={`inline-block px-5 py-2.5 rounded-full border border-white/[0.08] bg-white/[0.02] text-sm text-gray-300 transition-all duration-300 hover:bg-white/[0.05] hover:text-white cursor-default ${skill.color}`}
              >
                {skill.label}
              </motion.span>
            ))}
          </div>
        </div>

        <div className="mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Current Mission</h2>
            <p className="text-gray-400">Building the next generation of personal AI</p>
          </motion.div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {missionItems.map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06, duration: 0.5 }}
                whileHover={{ y: -4, scale: 1.02 }}
                className="relative p-6 rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl transition-all duration-500 hover:border-white/[0.15] hover:bg-white/[0.04] group"
              >
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/[0.04] to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/[0.08] flex items-center justify-center mb-4 group-hover:border-white/[0.15] transition-all duration-300">
                    <item.icon size={18} className="text-blue-300" />
                  </div>
                  <h3 className="text-sm font-semibold text-white mb-2">{item.title}</h3>
                  <p className="text-xs text-gray-400 leading-relaxed">{item.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Vision</h2>
            <p className="text-gray-400">What drives every line of code</p>
          </motion.div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { icon: Heart, title: 'Genuinely Helpful', text: 'Build technology that feels genuinely helpful in everyday life.' },
              { icon: Sparkles, title: 'Feels Alive', text: 'Create an AI companion that feels alive, not just functional.' },
              { icon: Users, title: 'Human-Centered', text: 'Make AI more personal, empathetic, and human-centered.' },
              { icon: Sun, title: 'Enjoy Using', text: 'Build software that people genuinely enjoy using every day.' },
              { icon: BookOpen, title: 'Keep Growing', text: 'Continue learning and improving through real-world projects.' },
              { icon: Rocket, title: 'Independent Vision', text: 'Prove that one creator can build world-class software independently.' },
            ].map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
                whileHover={{ y: -4, scale: 1.02 }}
                className="relative p-6 rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl transition-all duration-500 hover:border-white/[0.15] hover:bg-white/[0.04] group"
              >
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/[0.04] to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-white/[0.08] flex items-center justify-center mb-4 group-hover:border-white/[0.15] transition-all duration-300">
                    <item.icon size={18} className="text-purple-300" />
                  </div>
                  <h3 className="text-sm font-semibold text-white mb-2">{item.title}</h3>
                  <p className="text-xs text-gray-400 leading-relaxed">{item.text}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Tech Stack</h2>
            <p className="text-gray-400">Tools and technologies powering this project</p>
          </motion.div>
          <div className="flex flex-wrap justify-center gap-3">
            {techStack.map((tech, i) => (
              <motion.span
                key={tech.label}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06, duration: 0.4 }}
                whileHover={{ scale: 1.1, y: -3 }}
                className={`inline-flex items-center px-5 py-2.5 rounded-full border border-white/[0.08] bg-gradient-to-br ${tech.color} backdrop-blur-sm text-sm font-medium ${tech.textColor} transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/5 cursor-default`}
              >
                {tech.label}
              </motion.span>
            ))}
          </div>
        </div>

        <div className="mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Featured Project</h2>
            <p className="text-gray-400">The flagship product of this independent journey</p>
          </motion.div>
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.8 }}
              className="relative rounded-3xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-b from-white/[0.04] to-transparent pointer-events-none" />
              <div className="relative p-8 md:p-12">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/[0.1] flex items-center justify-center">
                    <Boxes size={28} className="text-blue-300" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">AVORA — Desktop AI Companion</h3>
                    <p className="text-sm text-gray-400">Independent AI Startup</p>
                  </div>
                </div>
                <p className="text-gray-300 leading-relaxed mb-8 max-w-2xl">
                  An intelligent desktop AI companion designed to feel natural, emotional, and proactive. 
                  AVORA combines advanced language understanding with desktop awareness, voice interaction, 
                  and long-term memory to create a truly personal assistant that learns and grows with you.
                </p>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {[
                    { label: 'Context Awareness', color: 'text-blue-300' },
                    { label: 'Voice Assistant', color: 'text-purple-300' },
                    { label: 'Memory System', color: 'text-cyan-300' },
                    { label: 'Animated Character', color: 'text-pink-300' },
                    { label: 'Emotion Engine', color: 'text-emerald-300' },
                    { label: 'Modern UI', color: 'text-amber-300' },
                    { label: 'File Understanding', color: 'text-violet-300' },
                    { label: 'Image Analysis', color: 'text-rose-300' },
                    { label: 'Computer Automation', color: 'text-teal-300' },
                  ].map((feature) => (
                    <div key={feature.label} className="flex items-center gap-2 text-sm">
                      <div className="w-1.5 h-1.5 rounded-full bg-current opacity-60" style={{ color: feature.color.replace('text-', '') }} />
                      <span className={`${feature.color} text-gray-300`}>{feature.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </div>

        <div className="mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Project Timeline</h2>
            <p className="text-gray-400">From concept to reality</p>
          </motion.div>
          <div className="max-w-3xl mx-auto relative">
            <div className="absolute left-4 md:left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-blue-500/40 via-purple-500/40 to-pink-500/40 md:-translate-x-1/2" />
            <div className="space-y-8">
              {timeline.map((item, i) => (
                <motion.div
                  key={item.year + item.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08, duration: 0.5 }}
                  className="relative flex items-start gap-6"
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded-full border-2 border-blue-500 bg-[#0a0a0f] flex items-center justify-center z-10">
                    <div className="w-2.5 h-2.5 rounded-full bg-blue-400" />
                  </div>
                  <div className="flex-1 pb-2">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-[10px] font-medium text-blue-400 uppercase tracking-wider">{item.year}</span>
                      <h4 className="text-sm font-semibold text-white">{item.title}</h4>
                    </div>
                    <p className="text-xs text-gray-400 leading-relaxed">{item.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        <div className="mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Future Roadmap</h2>
            <p className="text-gray-400">Where the journey leads next</p>
          </motion.div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {roadmapItems.map((item, i) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05, duration: 0.5 }}
                whileHover={{ y: -4, scale: 1.03 }}
                className={`relative p-5 rounded-2xl border ${item.color} bg-white/[0.02] backdrop-blur-xl transition-all duration-500 hover:bg-white/[0.04] group cursor-default`}
              >
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-t from-white/[0.03] to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <p className="text-sm font-semibold text-gray-300 text-center relative group-hover:text-white transition-colors">
                  {item.label}
                </p>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Core Values</h2>
            <p className="text-gray-400">Principles that guide every decision</p>
          </motion.div>
          <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-4">
            {values.map((value, i) => (
              <motion.div
                key={value.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05, duration: 0.5 }}
                whileHover={{ y: -4, scale: 1.05 }}
                className="flex flex-col items-center gap-3 p-4 rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl transition-all duration-500 hover:border-white/[0.15] hover:bg-white/[0.04] group cursor-default"
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-white/[0.08] flex items-center justify-center group-hover:border-white/[0.15] transition-all duration-300">
                  <value.icon size={18} className="text-blue-300" />
                </div>
                <span className="text-xs font-medium text-gray-300 text-center group-hover:text-white transition-colors">
                  {value.label}
                </span>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Fun Facts</h2>
            <p className="text-gray-400">A little more about the person behind the code</p>
          </motion.div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {funFacts.map((fact, i) => (
              <motion.div
                key={fact}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05, duration: 0.5 }}
                whileHover={{ y: -4, scale: 1.02 }}
                className="relative p-5 rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl transition-all duration-500 hover:border-white/[0.15] hover:bg-white/[0.04] group flex items-center gap-3"
              >
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/[0.04] to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-400 to-purple-400 flex-shrink-0" />
                <p className="text-sm text-gray-300 relative group-hover:text-white transition-colors">{fact}</p>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="mb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Get In Touch</h2>
            <p className="text-gray-400">Connect and follow the journey</p>
          </motion.div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 max-w-3xl mx-auto">
              {[
                { label: 'GitHub', icon: Code2, href: '#', color: 'hover:border-gray-500/40 hover:bg-gray-500/5' },
                { label: 'LinkedIn', icon: Briefcase, href: '#', color: 'hover:border-blue-500/40 hover:bg-blue-500/5' },
                { label: 'Email', icon: Mail, href: '#', color: 'hover:border-purple-500/40 hover:bg-purple-500/5' },
              { label: 'Future Portfolio', icon: Globe, href: '#', color: 'hover:border-cyan-500/40 hover:bg-cyan-500/5' },
              { label: 'Future Blog', icon: FileText, href: '#', color: 'hover:border-amber-500/40 hover:bg-amber-500/5' },
            ].map((item, i) => (
              <motion.a
                key={item.label}
                href={item.href}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05, duration: 0.5 }}
                whileHover={{ y: -4, scale: 1.02 }}
                className={`relative flex items-center gap-3 p-5 rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl transition-all duration-500 group ${item.color}`}
              >
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-t from-white/[0.02] to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-white/[0.06] to-white/[0.02] border border-white/[0.08] flex items-center justify-center group-hover:border-white/[0.15] transition-all duration-300">
                  <item.icon size={18} className="text-gray-300 group-hover:text-white transition-colors" />
                </div>
                <span className="text-sm font-medium text-gray-300 relative group-hover:text-white transition-colors">
                  {item.label}
                </span>
              </motion.a>
            ))}
          </div>
        </div>

        {/* Built with passion ending */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-center py-16 border-t border-white/[0.06]"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-white/[0.08] mb-6"
          >
            <Heart size={28} className="text-pink-400" />
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-3xl md:text-4xl font-bold text-white mb-4"
          >
            Built with passion
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="text-gray-400 max-w-2xl mx-auto leading-relaxed"
          >
            AVORA is more than code — it's a labor of love, built independently
            with dedication, creativity, and an unwavering belief in the power of
            truly intelligent companionship. Every line is crafted with purpose.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-6 text-sm text-gray-500"
          >
            © {new Date().getFullYear()} AVORA. Independent project. Not a company.
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

export default CreatorStory;
