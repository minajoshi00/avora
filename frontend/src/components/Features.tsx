import { motion } from 'framer-motion';
import { MessageSquare, Mic, Eye, Wand2, Brain, User } from 'lucide-react';
import { SectionHeading } from './ui/SectionHeading';
import { InteractiveAvoraCore } from './brand/InteractiveAvoraCore';

type FeatureId = 'conversation' | 'voice' | 'vision' | 'creation' | 'memory' | 'personalization';

interface Feature {
  id: FeatureId;
  label: string;
  icon: React.ElementType;
  description: string;
  state: 'idle' | 'listening' | 'thinking' | 'speaking' | 'excited' | 'focused';
  color: string;
}

const features: Feature[] = [
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

export function Features() {
  return (
    <section className="relative py-32">
      <div className="max-w-7xl mx-auto px-6">
        <SectionHeading
          label="Capabilities"
          title="More than intelligence"
          description="Explore what becomes possible when an AI truly understands."
        />

        <div className="mt-20 grid lg:grid-cols-2 gap-16 items-center">
          {/* Feature selector */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {features.map((feature) => {
              const Icon = feature.icon;
              
              return (
                <motion.button
                  key={feature.id}
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 17 }}
                  className="relative p-4 rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/[0.1] transition-all duration-500 text-left group hover-target"
                >
                  <Icon
                    size={20}
                    className="mb-3 text-gray-500 group-hover:text-gray-300 transition-colors duration-300"
                  />
                  <span className="text-sm font-medium block text-gray-400 group-hover:text-gray-200 transition-colors duration-300">
                    {feature.label}
                  </span>
                </motion.button>
              );
            })}
          </div>

          {/* Interactive feature panel */}
          <div className="relative">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              className="relative rounded-3xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-8 sm:p-10"
            >
              <div className="relative z-10 flex flex-col items-center text-center">
                <div className="mb-8">
                  <InteractiveAvoraCore state="focused" size={180} />
                </div>
                <h3 className="text-2xl sm:text-3xl font-bold text-white mb-4">
                  Intelligent Adaptation
                </h3>
                <p className="text-gray-400 max-w-md leading-relaxed">
                  AVORA continuously learns from your interactions, adapting its responses and capabilities to better serve your unique needs and preferences.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Features;