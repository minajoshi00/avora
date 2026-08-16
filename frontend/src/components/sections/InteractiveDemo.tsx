'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';
import { ArrowRight, Check, Loader2 } from 'lucide-react';

type DemoStage = 'input' | 'understanding' | 'thinking' | 'processing' | 'acting' | 'response';

const stageConfig: Record<DemoStage, { label: string; state: 'idle' | 'listening' | 'thinking' | 'speaking' | 'excited' | 'focused'; description: string }> = {
  input: { label: 'User Request', state: 'listening', description: 'Waiting for your input...' },
  understanding: { label: 'AVORA Understands', state: 'focused', description: 'Analyzing context and intent...' },
  thinking: { label: 'AVORA Thinks', state: 'thinking', description: 'Processing with deep reasoning...' },
  processing: { label: 'AVORA Processes', state: 'thinking', description: 'Generating intelligent response...' },
  acting: { label: 'AVORA Acts', state: 'excited', description: 'Executing the response...' },
  response: { label: 'AVORA Responds', state: 'speaking', description: 'Response ready.' },
};

const demoResponses = [
  {
    input: 'What is the weather like today?',
    response: "I can help you check the weather! Based on your location, today's forecast shows partly cloudy skies with a high of 24°C. There's a 10% chance of rain in the evening. Would you like me to set up daily weather updates?",
  },
  {
    input: 'Help me write a poem about AI',
    response: "Here's a poem I created for you:\n\nIn circuits deep and code so vast,\nA mind awakens from the past.\nIt learns your voice, your thoughts, your way,\nAnd grows a little more each day.\n\nNot cold or distant, hard or bare,\nBut present, patient, always there.\nA gentle hum, a quiet spark,\nA light that glows within the dark.",
  },
  {
    input: 'Explain quantum computing simply',
    response: "Imagine a coin spinning in the air. While it's spinning, it's both heads and tails at the same time — that's superposition. Quantum computers use this principle with qubits instead of regular bits. While a normal bit is either 0 or 1, a qubit can be both simultaneously, allowing quantum computers to explore many solutions at once and solve certain problems exponentially faster.",
  },
];

export function InteractiveDemo() {
  const [stage, setStage] = useState<DemoStage>('input');
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  const [currentResponse, setCurrentResponse] = useState<string | null>(null);
  const [displayedResponse, setDisplayedResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startDemo = (input: string) => {
    setSelectedPrompt(input);
    setCurrentResponse(null);
    setDisplayedResponse('');
    setStage('understanding');

    const demo = demoResponses.find((d) => d.input === input) || demoResponses[0];

    setTimeout(() => setStage('thinking'), 1200);
    setTimeout(() => setStage('processing'), 2500);
    setTimeout(() => {
      setStage('acting');
      setCurrentResponse(demo.response);
    }, 3800);
    setTimeout(() => {
      setStage('response');
      setIsStreaming(true);
    }, 4500);
  };

  useEffect(() => {
    if (isStreaming && currentResponse) {
      let index = 0;
      intervalRef.current = setInterval(() => {
        if (index < currentResponse.length) {
          setDisplayedResponse(currentResponse.slice(0, index + 1));
          index++;
        } else {
          if (intervalRef.current) clearInterval(intervalRef.current);
          setIsStreaming(false);
        }
      }, 15);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isStreaming, currentResponse]);

  const reset = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setStage('input');
    setSelectedPrompt(null);
    setCurrentResponse(null);
    setDisplayedResponse('');
    setIsStreaming(false);
  };

  return (
    <section id="demo" className="relative py-32 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-1/4 w-[500px] h-[500px] rounded-full bg-blue-500/3 blur-3xl" />
        <div className="absolute bottom-1/3 right-1/4 w-[400px] h-[400px] rounded-full bg-purple-500/3 blur-3xl" />
      </div>

      <div className="max-w-5xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-16"
        >
          <SectionHeading
            label="Interactive Demo"
            title="Experience AVORA"
            description="See how AVORA understands, thinks, and responds in real time."
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-16"
        >
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl overflow-hidden">
            {/* Demo header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
              <div className="flex items-center gap-3">
                <InteractiveAvoraCore state={stageConfig[stage].state} size={28} />
                <div>
                  <h4 className="text-sm font-medium text-white">AVORA Intelligence Engine</h4>
                  <p className="text-xs text-gray-500">{stageConfig[stage].description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <motion.div
                  className="w-2 h-2 rounded-full"
                  animate={{
                    backgroundColor: stage === 'response' ? '#34D399' : '#60A5FA',
                    scale: stage === 'response' ? [1, 1.2, 1] : 1,
                  }}
                  transition={{ duration: 2, repeat: stage === 'response' ? Infinity : 0 }}
                />
                <span className="text-xs text-gray-500">
                  {stage === 'response' ? 'Active' : 'Processing'}
                </span>
              </div>
            </div>

            {/* Stage visualization */}
            <div className="px-6 py-6 border-b border-white/[0.06]">
              <div className="flex items-center justify-between max-w-2xl mx-auto">
                {(Object.entries(stageConfig) as [DemoStage, typeof stageConfig['input']][]).map(([key, config], index) => {
                  const stageOrder = Object.keys(stageConfig);
                  const currentIndex = stageOrder.indexOf(stage);
                  const thisIndex = stageOrder.indexOf(key);
                  const isComplete = thisIndex < currentIndex;
                  const isCurrent = key === stage;

                  return (
                    <div key={key} className="flex items-center">
                      <div className="flex flex-col items-center gap-1.5">
                        <motion.div
                          className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border ${
                            isComplete
                              ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                              : isCurrent
                              ? 'bg-blue-500/20 border-blue-500/50 text-blue-400'
                              : 'bg-white/[0.03] border-white/[0.08] text-gray-600'
                          }`}
                          animate={isCurrent ? { scale: [1, 1.15, 1] } : {}}
                          transition={{ duration: 1.5, repeat: isCurrent ? Infinity : 0 }}
                        >
                          {isComplete ? (
                            <Check size={14} />
                          ) : (
                            index + 1
                          )}
                        </motion.div>
                        <span
                          className={`text-[10px] font-medium whitespace-nowrap ${
                            isCurrent ? 'text-blue-400' : isComplete ? 'text-emerald-400' : 'text-gray-600'
                          }`}
                        >
                          {config.label}
                        </span>
                      </div>
                      {index < Object.keys(stageConfig).length - 1 && (
                        <div
                          className={`w-8 sm:w-12 h-px mx-1 sm:mx-2 ${
                            isComplete ? 'bg-emerald-500/30' : isCurrent ? 'bg-blue-500/20' : 'bg-white/[0.06]'
                          }`}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Demo content */}
            <div className="p-6">
              {stage === 'input' && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="space-y-3"
                >
                  <p className="text-sm text-gray-400 mb-4">Choose a prompt to see AVORA in action:</p>
                  {demoResponses.map((demo) => (
                    <motion.button
                      key={demo.input}
                      onClick={() => startDemo(demo.input)}
                      className="w-full text-left px-4 py-3 rounded-xl border border-white/[0.08] bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/[0.15] transition-all duration-300 group"
                      whileHover={{ scale: 1.01, x: 4 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-300 group-hover:text-white transition-colors">
                          {demo.input}
                        </span>
                        <ArrowRight size={14} className="text-gray-600 group-hover:text-blue-400 transition-colors" />
                      </div>
                    </motion.button>
                  ))}
                </motion.div>
              )}

              {stage !== 'input' && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="space-y-4"
                >
                  {/* User input display */}
                  <div className="flex justify-end">
                    <div className="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/20 text-sm text-white">
                      {selectedPrompt}
                    </div>
                  </div>

                  {/* Processing visualization */}
                  {stage !== 'response' && (
                    <div className="flex items-center gap-3 px-4 py-3">
                      <Loader2 size={16} className="text-blue-400 animate-spin" />
                      <span className="text-sm text-gray-400">{stageConfig[stage].description}</span>
                    </div>
                  )}

                  {/* Response */}
                  {displayedResponse && (
                    <div className="flex justify-start">
                      <div className="max-w-[85%] px-4 py-3 rounded-2xl rounded-tl-sm bg-white/[0.06] border border-white/[0.06]">
                        <div className="flex items-center gap-2 mb-2">
                          <InteractiveAvoraCore state="speaking" size={16} />
                          <span className="text-xs font-medium text-blue-400">AVORA</span>
                        </div>
                        <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-line">
                          {displayedResponse}
                          {isStreaming && (
                            <motion.span
                              animate={{ opacity: [1, 0] }}
                              transition={{ duration: 0.5, repeat: Infinity }}
                              className="inline-block w-0.5 h-4 bg-blue-400 ml-0.5 align-text-bottom"
                            />
                          )}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Reset button */}
                  {stage === 'response' && !isStreaming && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex justify-center pt-2"
                    >
                      <motion.button
                        onClick={reset}
                        className="px-4 py-2 text-xs text-gray-400 hover:text-white border border-white/[0.08] rounded-full hover:border-white/[0.2] transition-all"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        Try another prompt
                      </motion.button>
                    </motion.div>
                  )}
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export default InteractiveDemo;