// Create a new Developer page for Pratik Ojha's personal website
// This is a premium developer profile page

import { useState, useEffect } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';
import { Button } from '../components/ui/Button';
import { GlassCard } from '../components/ui/GlassCard';
import { SectionHeading } from '../components/ui/SectionHeading';
import {
  Code2, Brain, Rocket, Heart, Lightbulb, Target, Eye,
  Mail, MapPin, School, Sparkles, Zap, BookOpen, Award,
  Globe, Cloud, Database, Layers, GitBranch,
  TrendingUp, Star, Coffee, Music, Gamepad2, Camera, Book, PenTool,
  Shield, CheckCircle2, ArrowRight, Quote, Flame,
  Moon, Link
} from 'lucide-react';

// Typing text variants for hero section
const typingVariants = [
  "Building the Future with AI",
  "Founder & Developer",
  "Python Developer",
  "AI Application Builder",
  "Creating Intelligent Software",
  "Turning Ideas into Reality"
];

// ─── Hero Section Component ──────────────────────────────────────────────────
export function DeveloperHero() {
  const [currentTextIndex, setCurrentTextIndex] = useState(0);
  const mouseX = useSpring(useMotionValue(0), { stiffness: 40, damping: 20 });
  const mouseY = useSpring(useMotionValue(0), { stiffness: 40, damping: 20 });

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTextIndex((prev) => (prev + 1) % typingVariants.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section id="developer-hero" className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-[#0a0a0f]">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-purple-900/20 to-pink-900/20 animate-gradient" />
      </div>

      {/* Floating particles */}
      <div className="absolute inset-0">
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-white/20 rounded-full"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight
            }}
            animate={{
              y: [null, Math.random() * -100, null],
              opacity: [0.2, 0.8, 0.2]
            }}
            transition={{
              duration: Math.random() * 10 + 5,
              repeat: Infinity,
              ease: "linear"
            }}
          />
        ))}
      </div>

      {/* Mouse interaction effect */}
      <div className="absolute inset-0">
        <motion.div
          className="absolute inset-0 bg-gradient-radial from-white/10 to-transparent"
          style={{
            x: mouseX,
            y: mouseY,
            opacity: 0.6
          }}
        />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-6 text-center">
        {/* Profile info */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 1, ease: "easeOut" }}
        >
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-4">
            Pratik Ojha
          </h1>
          <p className="text-2xl md:text-3xl text-gray-300 mb-8">
            Founder & Developer
          </p>
        </motion.div>

        {/* Location and School */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          className="space-y-4 mb-12"
        >
          <div className="flex items-center justify-center gap-2 text-gray-400">
            <span className="text-lg">📍</span>
            <span>Dhangadhi, Kailali, Nepal</span>
          </div>
          <div className="flex items-center justify-center gap-2 text-gray-400">
            <span className="text-lg">🏫</span>
            <span>Balmiki International School</span>
          </div>
        </motion.div>

        {/* Animated typing text */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.4 }}
          className="h-12 mb-16"
        >
          <motion.p
            key={currentTextIndex}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="text-xl md:text-2xl text-blue-400 font-medium"
          >
            {typingVariants[currentTextIndex]}
          </motion.p>
        </motion.div>

        {/* Action buttons */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.6 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-6"
        >
          <motion.div
            whileHover={{ scale: 1.05, y: -3 }}
            whileTap={{ scale: 0.95 }}
          >
            <Button
              size="lg"
              onClick={() => {
                const projectsSection = document.getElementById('projects');
                if (projectsSection) projectsSection.scrollIntoView({ behavior: 'smooth' });
              }}
              className="shadow-[0_0_30px_rgba(96,165,250,0.3)]"
            >
              Explore My Projects
            </Button>
          </motion.div>
          <motion.div
            whileHover={{ scale: 1.05, y: -3 }}
            whileTap={{ scale: 0.95 }}
          >
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                const contactSection = document.getElementById('contact');
                if (contactSection) contactSection.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Contact Me
            </Button>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

// ─── About Me Section ────────────────────────────────────────────────────────
export function AboutMe() {
  return (
    <section id="about" className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        <SectionHeading
          label="About Me"
          title="Who I Am"
        />

        <GlassCard className="space-y-6" glow="blue">
          <p className="text-lg text-gray-300 leading-relaxed">
            I'm Pratik Ojha, an AI developer and co-founder of AVORA AI based in Dhangadhi, Nepal. Balmiki International School is where I study, and this project is built together with my co-founder, Atharba Bhandari.
          </p>

          <p className="text-lg text-gray-300 leading-relaxed">
            I love technology because it allows me to solve real problems and create meaningful experiences. I started building AI because I wanted to create systems that feel natural and genuinely help people.
          </p>

          <p className="text-lg text-gray-300 leading-relaxed">
            My passion for creating software comes from the satisfaction of turning ideas into reality. I find joy in building intelligent systems that learn and evolve with users, making their lives easier and more productive.
          </p>

          <p className="text-lg text-gray-300 leading-relaxed">
            I'm constantly improving as a developer, learning new technologies and techniques while focusing on creating quality, reliable software. My goal is to build products that people around the world can use and appreciate.
          </p>
        </GlassCard>
      </div>
    </section>
  );
}

// ─── Journey Section ─────────────────────────────────────────────────────────
export function JourneySection() {
  const milestones = [
    {
      year: '2023',
      title: 'The Beginning',
      description: 'Discovered programming and fell in love with Python. Started with simple scripts and quickly moved to building real applications.',
      icon: Code2,
    },
    {
      year: '2024',
      title: 'Exploring AI',
      description: 'Dived deep into artificial intelligence, machine learning, and natural language processing. Built my first AI-powered chatbot.',
      icon: Brain,
    },
    {
      year: '2025',
      title: 'Building AVORA',
      description: 'Started AVORA as an independent AI project. Designed the architecture, trained models, and built a complete intelligent assistant.',
      icon: Rocket,
    },
    {
      year: '2026',
      title: 'Founder & Developer',
      description: 'Continuing to build and improve AVORA while balancing school. Focused on creating software that makes a real difference.',
      icon: Star,
    },
  ];

  return (
    <section id="journey" className="relative py-32">
      <div className="max-w-5xl mx-auto px-6">
        <SectionHeading
          label="My Journey"
          title="The Road So Far"
          description="Every great developer has a story. Here's mine — from curious student to AI builder."
        />

        <div className="relative mt-16">
          {/* Vertical line */}
          <div className="absolute left-4 md:left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-blue-500/50 via-purple-500/50 to-transparent md:-translate-x-1/2" />

          <div className="space-y-12">
            {milestones.map((milestone, index) => {
              const Icon = milestone.icon;
              const isLeft = index % 2 === 0;
              return (
                <motion.div
                  key={milestone.year}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-50px' }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className={`relative flex items-center gap-8 ${isLeft ? 'md:flex-row' : 'md:flex-row-reverse'}`}
                >
                  {/* Dot */}
                  <div className="absolute left-4 md:left-1/2 w-3 h-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 ring-4 ring-[#0a0a0f] md:-translate-x-1/2 z-10" />

                  {/* Content */}
                  <div className={`ml-12 md:ml-0 md:w-1/2 ${isLeft ? 'md:pr-12 md:text-right' : 'md:pl-12'}`}>
                    <GlassCard glow="blue" className="hover-target">
                      <div className={`flex items-center gap-3 mb-3 ${isLeft ? 'md:flex-row-reverse' : ''}`}>
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                          <Icon size={20} className="text-blue-400" />
                        </div>
                        <span className="text-2xl font-bold text-white">{milestone.year}</span>
                      </div>
                      <h3 className="text-lg font-semibold text-white mb-2">{milestone.title}</h3>
                      <p className="text-sm text-gray-400 leading-relaxed">{milestone.description}</p>
                    </GlassCard>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Mission Section ─────────────────────────────────────────────────────────
export function MissionSection() {
  return (
    <section id="mission" className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        <SectionHeading
          label="Mission"
          title="What Drives Me Forward"
          description="My mission is to build AI that feels human — software that understands, adapts, and genuinely helps."
        />

        <div className="grid md:grid-cols-3 gap-6 mt-16">
          {[
            { icon: Target, title: 'Goal', text: 'Create AI systems that are accessible, private, and genuinely useful to everyone.' },
            { icon: Heart, title: 'Purpose', text: 'Solve real problems with technology that feels natural and intuitive.' },
            { icon: Globe, title: 'Impact', text: 'Build products that people around the world can use and appreciate.' },
          ].map((item, index) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <GlassCard glow="blue" className="h-full hover-target">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-4">
                    <Icon size={24} className="text-blue-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">{item.text}</p>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ─── Vision Section ──────────────────────────────────────────────────────────
export function VisionSection() {
  return (
    <section id="vision" className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        <SectionHeading
          label="Vision"
          title="The Future I See"
          description="A world where AI is a companion, not a tool — where technology understands you and grows with you."
        />

        <GlassCard className="mt-16 space-y-6" glow="purple">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center flex-shrink-0">
              <Eye size={24} className="text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">AI as a Companion</h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                I envision a future where AI assistants are true companions — they remember what matters, understand context, and adapt to your needs without being told.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center flex-shrink-0">
              <Shield size={24} className="text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Privacy First</h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                Your data should belong to you. I believe AI should work locally when possible, keeping your information private and secure.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500/20 to-blue-500/20 flex items-center justify-center flex-shrink-0">
              <Sparkles size={24} className="text-green-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Accessible to All</h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                Technology should bridge gaps, not create them. I'm committed to building AI that's accessible regardless of technical background.
              </p>
            </div>
          </div>
        </GlassCard>
      </div>
    </section>
  );
}

// ─── Projects Section ────────────────────────────────────────────────────────
export function ProjectsSection() {
  const projects = [
    {
      title: 'AVORA AI',
      description: 'An intelligent AI assistant that learns, remembers, and adapts. Built from scratch with natural language processing, memory systems, and a beautiful interface.',
      tags: ['Python', 'AI', 'NLP', 'React'],
      icon: Brain,
      gradient: 'from-blue-500/20 to-purple-500/20',
      iconColor: 'text-blue-400',
    },
    {
      title: 'Smart Automation',
      description: 'Automation tools that handle repetitive tasks intelligently. Clipboard management, hotkeys, and workflow optimization powered by AI.',
      tags: ['Python', 'Automation', 'Desktop'],
      icon: Zap,
      gradient: 'from-yellow-500/20 to-orange-500/20',
      iconColor: 'text-yellow-400',
    },
    {
      title: 'Web Experiences',
      description: 'Premium web interfaces with smooth animations, glassmorphism design, and responsive layouts. Built with React, TypeScript, and Tailwind CSS.',
      tags: ['React', 'TypeScript', 'Tailwind'],
      icon: Layers,
      gradient: 'from-cyan-500/20 to-blue-500/20',
      iconColor: 'text-cyan-400',
    },
    {
      title: 'Memory Systems',
      description: 'Persistent memory architecture that allows AI to remember conversations, preferences, and context across sessions.',
      tags: ['Python', 'Database', 'AI'],
      icon: Database,
      gradient: 'from-purple-500/20 to-pink-500/20',
      iconColor: 'text-purple-400',
    },
  ];

  return (
    <section id="projects" className="relative py-32">
      <div className="max-w-6xl mx-auto px-6">
        <SectionHeading
          label="Projects"
          title="Things I've Built"
          description="A collection of projects that showcase my passion for AI, automation, and beautiful interfaces."
        />

        <div className="grid md:grid-cols-2 gap-6 mt-16">
          {projects.map((project, index) => {
            const Icon = project.icon;
            return (
              <motion.div
                key={project.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <GlassCard glow="blue" className="h-full hover-target group">
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${project.gradient} flex items-center justify-center mb-4 transition-transform duration-300 group-hover:scale-110`}>
                    <Icon size={28} className={project.iconColor} />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">{project.title}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed mb-4">{project.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {project.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 text-xs font-medium rounded-full bg-white/[0.05] border border-white/[0.08] text-gray-300"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ─── Learning Section ────────────────────────────────────────────────────────
export function LearningSection() {
  const learningPath = [
    { title: 'Python Fundamentals', progress: 95, description: 'Mastered core Python, OOP, async programming, and advanced patterns.' },
    { title: 'AI & Machine Learning', progress: 85, description: 'Deep understanding of NLP, neural networks, and model training.' },
    { title: 'Web Development', progress: 80, description: 'React, TypeScript, Tailwind CSS, and modern frontend practices.' },
    { title: 'System Architecture', progress: 75, description: 'Designing scalable, maintainable systems with clean architecture.' },
    { title: 'Database Design', progress: 70, description: 'Data modeling, SQL, NoSQL, and efficient query optimization.' },
    { title: 'DevOps & Deployment', progress: 60, description: 'Learning containerization, CI/CD, and cloud deployment.' },
  ];

  return (
    <section id="learning" className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        <SectionHeading
          label="Learning"
          title="Always Growing"
          description="Learning never stops. Here's my current skill development journey."
        />

        <div className="space-y-6 mt-16">
          {learningPath.map((item, index) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.6, delay: index * 0.05 }}
            >
              <GlassCard glow="blue" className="hover-target">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-semibold text-white">{item.title}</h3>
                  <span className="text-sm font-bold text-blue-400">{item.progress}%</span>
                </div>
                <p className="text-sm text-gray-400 mb-3">{item.description}</p>
                <div className="h-2 rounded-full bg-white/[0.05] overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: `${item.progress}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
                    className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                  />
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Tech Stack Section ──────────────────────────────────────────────────────
export function StackSection() {
  const stack = [
    { category: 'Languages', items: ['Python', 'TypeScript', 'JavaScript', 'HTML/CSS'], icon: Code2 },
    { category: 'AI & ML', items: ['NLP', 'Neural Networks', 'TensorFlow', 'Transformers'], icon: Brain },
    { category: 'Frontend', items: ['React', 'Tailwind CSS', 'Framer Motion', 'Vite'], icon: Layers },
    { category: 'Backend', items: ['FastAPI', 'Flask', 'SQLite', 'PostgreSQL'], icon: Database },
    { category: 'Tools', items: ['Git', 'VS Code', 'Figma', 'Docker'], icon: GitBranch },
    { category: 'Cloud', items: ['Vercel', 'Railway', 'Render', 'Local First'], icon: Cloud },
  ];

  return (
    <section id="stack" className="relative py-32">
      <div className="max-w-5xl mx-auto px-6">
        <SectionHeading
          label="Tech Stack"
          title="Tools I Work With"
          description="The technologies and tools I use to bring ideas to life."
        />

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mt-16">
          {stack.map((category, index) => {
            const Icon = category.icon;
            return (
              <motion.div
                key={category.category}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.6, delay: index * 0.08 }}
              >
                <GlassCard glow="blue" className="h-full hover-target">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                      <Icon size={20} className="text-blue-400" />
                    </div>
                    <h3 className="text-base font-semibold text-white">{category.category}</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {category.items.map((item) => (
                      <span
                        key={item}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg bg-white/[0.04] border border-white/[0.06] text-gray-300"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ─── Roles Section ───────────────────────────────────────────────────────────
export function RolesSection() {
  const roles = [
    { title: 'Founder', description: 'Building AVORA as an independent startup. Making all the decisions, taking all the risks.', icon: Rocket },
    { title: 'Developer', description: 'Writing every line of code. From backend logic to beautiful frontend interfaces.', icon: Code2 },
    { title: 'Designer', description: 'Crafting the visual identity, user experience, and every pixel of the interface.', icon: PenTool },
    { title: 'Student', description: 'Balancing school at Balmiki International School while building a real product.', icon: BookOpen },
  ];

  return (
    <section id="roles" className="relative py-32">
      <div className="max-w-5xl mx-auto px-6">
        <SectionHeading
          label="Roles"
          title="Hats I Wear"
          description="Being a solo founder means being everything at once. Here are the roles I juggle every day."
        />

        <div className="grid md:grid-cols-2 gap-6 mt-16">
          {roles.map((role, index) => {
            const Icon = role.icon;
            return (
              <motion.div
                key={role.title}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <GlassCard glow="purple" className="h-full hover-target group">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center transition-transform duration-300 group-hover:scale-110 flex-shrink-0">
                      <Icon size={28} className="text-purple-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white">{role.title}</h3>
                      <p className="text-sm text-gray-400 mt-1">{role.description}</p>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ─── Drives Section ──────────────────────────────────────────────────────────
export function DrivesSection() {
  const drives = [
    { title: 'Curiosity', description: 'The desire to understand how things work and make them better.', icon: Lightbulb },
    { title: 'Impact', description: 'Building things that genuinely help people in their daily lives.', icon: TrendingUp },
    { title: 'Challenge', description: 'Solving hard problems that others shy away from.', icon: Flame },
    { title: 'Independence', description: 'The freedom to build what I believe in, my way.', icon: Rocket },
  ];

  return (
    <section id="drives" className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        <SectionHeading
          label="What Drives Me"
          title="My Motivation"
          description="The forces that keep me coding late into the night."
        />

        <div className="grid md:grid-cols-2 gap-6 mt-16">
          {drives.map((drive, index) => {
            const Icon = drive.icon;
            return (
              <motion.div
                key={drive.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <GlassCard glow="blue" className="h-full hover-target">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center flex-shrink-0">
                      <Icon size={24} className="text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-1">{drive.title}</h3>
                      <p className="text-sm text-gray-400 leading-relaxed">{drive.description}</p>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ─── Philosophy Section ──────────────────────────────────────────────────────
export function PhilosophySection() {
  const principles = [
    'Build for the user, not for the demo.',
    'Privacy is a right, not a feature.',
    'Simple is better than clever.',
    'Ship early, iterate fast, listen always.',
    'Code is craft — treat it with respect.',
    'If it doesn\'t help someone, don\'t build it.',
  ];

  return (
    <section id="philosophy" className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        <SectionHeading
          label="Philosophy"
          title="How I Think About Software"
          description="Principles that guide every line of code I write."
        />

        <div className="mt-16 space-y-4">
          {principles.map((principle, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.5, delay: index * 0.08 }}
            >
              <GlassCard glow="purple" className="hover-target">
                <div className="flex items-center gap-4">
                  <Quote size={24} className="text-purple-400 flex-shrink-0" />
                  <p className="text-lg text-gray-200 font-medium italic">{principle}</p>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Timeline Section ────────────────────────────────────────────────────────
export function TimelineSection() {
  const events = [
    { date: 'Jan 2023', event: 'Wrote my first Python script', icon: Code2 },
    { date: 'Mar 2023', event: 'Built my first real application', icon: Rocket },
    { date: 'Jul 2023', event: 'Started learning AI and ML', icon: Brain },
    { date: 'Nov 2023', event: 'Created my first AI chatbot', icon: Sparkles },
    { date: 'Feb 2024', event: 'Began designing AVORA', icon: Lightbulb },
    { date: 'Jun 2024', event: 'AVORA first working prototype', icon: CheckCircle2 },
    { date: 'Oct 2024', event: 'Launched AVORA web interface', icon: Globe },
    { date: 'Jan 2025', event: 'Added memory and learning systems', icon: Database },
    { date: 'May 2025', event: 'Premium UI redesign', icon: Award },
    { date: '2026', event: 'Continuing to build and improve', icon: Star },
  ];

  return (
    <section id="timeline" className="relative py-32">
      <div className="max-w-3xl mx-auto px-6">
        <SectionHeading
          label="Timeline"
          title="Milestones"
          description="Key moments in my development journey."
        />

        <div className="mt-16 relative">
          <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-blue-500/50 via-purple-500/30 to-transparent" />

          <div className="space-y-6">
            {events.map((event, index) => {
              const Icon = event.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: '-30px' }}
                  transition={{ duration: 0.5, delay: index * 0.05 }}
                  className="relative flex items-center gap-6 pl-0"
                >
                  <div className="relative z-10 w-12 h-12 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/[0.08] flex items-center justify-center flex-shrink-0">
                    <Icon size={20} className="text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <span className="text-xs font-medium text-blue-400 uppercase tracking-wider">{event.date}</span>
                    <p className="text-base text-gray-200 mt-0.5">{event.event}</p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Roadmap Section ─────────────────────────────────────────────────────────
export function RoadmapSection() {
  const roadmap = [
    {
      phase: 'Q1 2026',
      title: 'Enhanced Intelligence',
      items: ['Improved NLP models', 'Better context understanding', 'Faster response times'],
      status: 'in-progress',
    },
    {
      phase: 'Q2 2026',
      title: 'Mobile Experience',
      items: ['Responsive mobile UI', 'Touch-optimized interactions', 'Offline capabilities'],
      status: 'planned',
    },
    {
      phase: 'Q3 2026',
      title: 'Ecosystem',
      items: ['Plugin system', 'Third-party integrations', 'Developer API'],
      status: 'planned',
    },
    {
      phase: 'Q4 2026',
      title: 'Scale & Reach',
      items: ['Multi-language support', 'Cloud sync options', 'Community features'],
      status: 'vision',
    },
  ];

  const statusColors: Record<string, string> = {
    'in-progress': 'text-green-400 bg-green-500/10 border-green-500/20',
    'planned': 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    'vision': 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  };

  return (
    <section id="roadmap" className="relative py-32">
      <div className="max-w-5xl mx-auto px-6">
        <SectionHeading
          label="Roadmap"
          title="Where I'm Headed"
          description="The future of AVORA and my development journey."
        />

        <div className="grid md:grid-cols-2 gap-6 mt-16">
          {roadmap.map((phase, index) => (
            <motion.div
              key={phase.phase}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              <GlassCard glow="blue" className="h-full hover-target">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-bold text-white">{phase.phase}</span>
                  <span className={`px-3 py-1 text-xs font-medium rounded-full border ${statusColors[phase.status]}`}>
                    {phase.status.replace('-', ' ')}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-3">{phase.title}</h3>
                <ul className="space-y-2">
                  {phase.items.map((item) => (
                    <li key={item} className="flex items-center gap-2 text-sm text-gray-400">
                      <CheckCircle2 size={16} className="text-blue-400 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Interests Section ───────────────────────────────────────────────────────
export function InterestsSection() {
  const interests = [
    { name: 'Coding', icon: Code2, color: 'text-blue-400' },
    { name: 'AI Research', icon: Brain, color: 'text-purple-400' },
    { name: 'Reading', icon: Book, color: 'text-green-400' },
    { name: 'Music', icon: Music, color: 'text-pink-400' },
    { name: 'Gaming', icon: Gamepad2, color: 'text-orange-400' },
    { name: 'Photography', icon: Camera, color: 'text-cyan-400' },
    { name: 'Writing', icon: PenTool, color: 'text-yellow-400' },
    { name: 'Coffee', icon: Coffee, color: 'text-amber-400' },
  ];

  return (
    <section id="interests" className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        <SectionHeading
          label="Interests"
          title="Beyond the Code"
          description="When I'm not building AVORA, here's what I enjoy."
        />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16">
          {interests.map((interest, index) => {
            const Icon = interest.icon;
            return (
              <motion.div
                key={interest.name}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.5, delay: index * 0.05 }}
                whileHover={{ y: -8 }}
              >
                <GlassCard glow="blue" className="text-center hover-target">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-white/[0.04] flex items-center justify-center">
                      <Icon size={24} className={interest.color} />
                    </div>
                    <span className="text-sm font-medium text-gray-300">{interest.name}</span>
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ─── Facts Section ───────────────────────────────────────────────────────────
export function FactsSection() {
  const facts = [
    { label: 'Lines of Code', value: '50K+', icon: Code2 },
    { label: 'Projects Built', value: '10+', icon: Rocket },
    { label: 'Cups of Coffee', value: '∞', icon: Coffee },
    { label: 'Late Nights', value: 'Many', icon: Moon },
  ];

  return (
    <section id="facts" className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        <SectionHeading
          label="Quick Facts"
          title="By the Numbers"
        />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16">
          {facts.map((fact, index) => {
            const Icon = fact.icon;
            return (
              <motion.div
                key={fact.label}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <GlassCard glow="blue" className="text-center hover-target">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mx-auto mb-3">
                    <Icon size={24} className="text-blue-400" />
                  </div>
                  <div className="text-3xl font-bold text-white mb-1">{fact.value}</div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider">{fact.label}</div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ─── Fun Facts Section ───────────────────────────────────────────────────────
export function FunFactsSection() {
  const funFacts = [
    'I built my first AI before I had a proper computer setup.',
    'My best code is written after midnight.',
    'I debug with print statements and I\'m not ashamed of it.',
    'I named my AI AVORA because it sounds like "aura" — a presence.',
    'I can talk about AI for hours without getting bored.',
    'My school projects and my startup are very different things.',
  ];

  return (
    <section id="fun-facts" className="relative py-32">
      <div className="max-w-4xl mx-auto px-6">
        <SectionHeading
          label="Fun Facts"
          title="Things You Might Not Know"
          description="A few lighter facts about me."
        />

        <div className="grid md:grid-cols-2 gap-4 mt-16">
          {funFacts.map((fact, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.5, delay: index * 0.08 }}
            >
              <GlassCard glow="purple" className="h-full hover-target">
                <div className="flex items-start gap-3">
                  <Sparkles size={20} className="text-purple-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-gray-300 leading-relaxed">{fact}</p>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Values Section ──────────────────────────────────────────────────────────
export function ValuesSection() {
  const values = [
    { title: 'Integrity', description: 'I build what I believe in, honestly and transparently.', icon: Shield },
    { title: 'Quality', description: 'Every detail matters. Good enough is never good enough.', icon: Award },
    { title: 'Empathy', description: 'I build for real people with real needs, not for metrics.', icon: Heart },
    { title: 'Perseverance', description: 'Hard problems take time. I\'m in it for the long haul.', icon: Flame },
    { title: 'Curiosity', description: 'I never stop asking "why?" and "what if?"', icon: Lightbulb },
    { title: 'Independence', description: 'I think for myself and build on my own terms.', icon: Star },
  ];

  return (
    <section id="values" className="relative py-32">
      <div className="max-w-5xl mx-auto px-6">
        <SectionHeading
          label="Values"
          title="What I Stand For"
          description="The principles that define who I am as a developer and as a person."
        />

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mt-16">
          {values.map((value, index) => {
            const Icon = value.icon;
            return (
              <motion.div
                key={value.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.6, delay: index * 0.08 }}
              >
                <GlassCard glow="blue" className="h-full hover-target group">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-4 transition-transform duration-300 group-hover:scale-110">
                    <Icon size={24} className="text-blue-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{value.title}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">{value.description}</p>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ─── Contact Section ─────────────────────────────────────────────────────────
export function ContactSection() {
  const socials = [
    { name: 'GitHub', icon: GitBranch, href: '#', color: 'text-gray-300' },
    { name: 'Email', icon: Mail, href: '#', color: 'text-blue-400' },
    { name: 'LinkedIn', icon: Link, href: '#', color: 'text-cyan-400' },
  ];

  return (
    <section id="contact" className="relative py-32">
      <div className="max-w-3xl mx-auto px-6">
        <SectionHeading
          label="Contact"
          title="Let's Connect"
          description="Have a question, idea, or just want to say hi? I'd love to hear from you."
        />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.6 }}
        >
          <GlassCard className="mt-16 text-center" glow="blue">
            <div className="space-y-8">
              <div>
                <h3 className="text-2xl font-bold text-white mb-2">Get in Touch</h3>
                <p className="text-gray-400">
                  I'm always open to talking about AI, development, or potential collaborations.
                </p>
              </div>

              <div className="flex items-center justify-center gap-2 text-gray-400">
                <MapPin size={18} className="text-blue-400" />
                <span>Dhangadhi, Kailali, Nepal</span>
              </div>

              <div className="flex items-center justify-center gap-2 text-gray-400">
                <School size={18} className="text-blue-400" />
                <span>Balmiki International School</span>
              </div>

              {/* Social Links */}
              <div className="flex items-center justify-center gap-4 pt-4">
                {socials.map((social) => {
                  const Icon = social.icon;
                  return (
                    <motion.a
                      key={social.name}
                      href={social.href}
                      whileHover={{ scale: 1.1, y: -3 }}
                      whileTap={{ scale: 0.95 }}
                      className="w-12 h-12 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center hover:border-white/[0.15] transition-all"
                      aria-label={social.name}
                    >
                      <Icon size={22} className={social.color} />
                    </motion.a>
                  );
                })}
              </div>

              {/* CTA Button */}
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="inline-block"
              >
                <Button
                  size="lg"
                  onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                  icon={<ArrowRight size={20} />}
                >
                  Back to Top
                </Button>
              </motion.div>
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </section>
  );
}

// ─── Main Developer Page Component ───────────────────────────────────────────
export function DeveloperPage() {
  return (
    <main className="bg-[#0a0a0f] text-white overflow-x-hidden">
      <DeveloperHero />
      <AboutMe />
      <JourneySection />
      <MissionSection />
      <VisionSection />
      <ProjectsSection />
      <LearningSection />
      <StackSection />
      <RolesSection />
      <DrivesSection />
      <PhilosophySection />
      <TimelineSection />
      <RoadmapSection />
      <InterestsSection />
      <FactsSection />
      <FunFactsSection />
      <ValuesSection />
      <ContactSection />
    </main>
  );
}

export default DeveloperPage;