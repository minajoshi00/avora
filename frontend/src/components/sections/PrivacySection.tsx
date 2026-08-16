'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { Shield, Wifi, WifiOff, Lock, Server, Eye, Check } from 'lucide-react';

export function PrivacySection() {
  const [mode, setMode] = useState<'local' | 'cloud'>('local');

  return (
    <section id="privacy" className="relative py-32 overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-emerald-500/3 blur-3xl" />
      </div>

      <div className="max-w-6xl mx-auto px-6">
        <SectionHeading
          label="Privacy First"
          title="Your data, your intelligence"
          description="AVORA is designed with privacy at its core. Local by default, cloud when you choose."
        />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-16"
        >
          {/* Local/Cloud Toggle */}
          <div className="flex justify-center mb-16">
            <div className="relative inline-flex items-center bg-white/[0.03] rounded-2xl border border-white/[0.08] p-1.5">
              {(['local', 'cloud'] as const).map((m) => (
                <motion.button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`relative flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium transition-all duration-300 z-10 ${
                    mode === m ? 'text-white' : 'text-gray-400 hover:text-gray-200'
                  }`}
                  whileHover={{ scale: mode === m ? 1 : 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {m === 'local' ? <WifiOff size={16} /> : <Wifi size={16} />}
                  {m === 'local' ? 'Local AI' : 'Cloud AI'}
                </motion.button>
              ))}
              <motion.div
                className="absolute top-1.5 bottom-1.5 rounded-xl bg-white/[0.08] border border-white/[0.1]"
                layoutId="privacy-toggle"
                style={{
                  left: mode === 'local' ? '0.375rem' : '50%',
                  width: 'calc(50% - 0.375rem)',
                }}
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left: Feature cards */}
            <div className="space-y-4">
              <AnimatePresence mode="wait">
                {mode === 'local' ? (
                  <motion.div
                    key="local"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="space-y-4"
                  >
                    <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 backdrop-blur-xl p-6">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                          <Server size={20} className="text-emerald-400" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-white">Local Processing</h3>
                          <p className="text-xs text-emerald-400">Data stays on your device</p>
                        </div>
                      </div>
                      <ul className="space-y-3">
                        {[
                          'All core intelligence runs locally',
                          'No data leaves your device without permission',
                          'Works offline with full functionality',
                          'End-to-end encryption for all data',
                          'No training on your personal conversations',
                        ].map((item) => (
                          <li key={item} className="flex items-start gap-2 text-sm text-gray-300">
                            <Check size={14} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
                      <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                        <Lock size={14} className="text-emerald-400" />
                        Offline Mode
                      </h4>
                      <p className="text-sm text-gray-400 leading-relaxed">
                        Core features continue working without internet. Your conversations,
                        memory, and personalization remain fully functional even when you're
                        offline. Sync when you reconnect.
                      </p>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="cloud"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="space-y-4"
                  >
                    <div className="rounded-2xl border border-blue-500/20 bg-blue-500/5 backdrop-blur-xl p-6">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                          <Wifi size={20} className="text-blue-400" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-white">Cloud Enhancement</h3>
                          <p className="text-xs text-blue-400">Advanced processing when enabled</p>
                        </div>
                      </div>
                      <ul className="space-y-3">
                        {[
                          'Access to larger AI models',
                          'Faster complex reasoning',
                          'Cross-device sync (optional)',
                          'Advanced vision and voice processing',
                          'You control what goes to the cloud',
                        ].map((item) => (
                          <li key={item} className="flex items-start gap-2 text-sm text-gray-300">
                            <Check size={14} className="text-blue-400 mt-0.5 flex-shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
                      <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                        <Eye size={14} className="text-blue-400" />
                        Transparent Control
                      </h4>
                      <p className="text-sm text-gray-400 leading-relaxed">
                        You decide when and what to sync. Every cloud request is visible in your
                        activity log. No background data collection. No hidden processing.
                        Complete transparency.
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Right: Visual representation */}
            <div className="flex items-center justify-center">
              <motion.div
                className="relative w-full max-w-sm aspect-square"
                animate={{ rotate: mode === 'local' ? 0 : 5 }}
                transition={{ type: 'spring', stiffness: 200, damping: 20 }}
              >
                {/* Device outline */}
                <div className="absolute inset-[15%] rounded-3xl border-2 border-white/[0.1] bg-white/[0.02] backdrop-blur-xl flex items-center justify-center">
                  <motion.div
                    className="text-center"
                    animate={{ scale: mode === 'local' ? 1 : 0.9 }}
                  >
                    <Shield size={48} className={mode === 'local' ? 'text-emerald-400' : 'text-blue-400'} />
                    <p className="text-sm text-gray-400 mt-3">
                      {mode === 'local' ? 'Your Device' : 'Secure Cloud'}
                    </p>
                  </motion.div>
                </div>

                {/* Orbiting rings */}
                <motion.div
                  className="absolute inset-0 rounded-full border border-white/[0.06]"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
                />
                <motion.div
                  className="absolute inset-[5%] rounded-full border border-dashed border-white/[0.04]"
                  animate={{ rotate: -360 }}
                  transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
                />

                {/* Orbiting dots */}
                {[0, 1, 2, 3].map((i) => {
                  const angle = (i * 90 + 45) * (Math.PI / 180);
                  const radius = 42;
                  return (
                    <motion.div
                      key={i}
                      className="absolute w-2 h-2 rounded-full"
                      style={{
                        left: `calc(50% + ${Math.cos(angle) * radius}% - 4px)`,
                        top: `calc(50% + ${Math.sin(angle) * radius}% - 4px)`,
                        backgroundColor: mode === 'local' ? '#34D399' : '#60A5FA',
                        opacity: 0.4,
                      }}
                      animate={{
                        scale: [1, 1.5, 1],
                        opacity: [0.4, 0.8, 0.4],
                      }}
                      transition={{
                        duration: 3,
                        repeat: Infinity,
                        delay: i * 0.75,
                      }}
                    />
                  );
                })}
              </motion.div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export default PrivacySection;