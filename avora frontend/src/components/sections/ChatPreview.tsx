'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Copy, Check } from 'lucide-react';
import { SectionHeading } from '../ui/SectionHeading';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';

const responses = [
  "Hello! I'm AVORA. How can I assist you today?",
  "I can help you explore ideas, analyze data, or simply have a conversation.",
  "Processing your request with real-time adaptive intelligence...",
  "I remember our previous context. What would you like to explore next?",
  "I'm designed to learn and evolve. Every interaction makes me smarter.",
];

export function ChatPreview() {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'avora'; content: string }>>([
    { role: 'avora', content: "Welcome. I'm AVORA — ask me anything." }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = (text: string) => {
    if (!text.trim()) return;
    
    const userMessage = { role: 'user' as const, content: text };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    setTimeout(() => {
      const avoraResponse = responses[Math.floor(Math.random() * responses.length)];
      const avoraMessage = { role: 'avora' as const, content: avoraResponse };
      setMessages(prev => [...prev, avoraMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(input);
    }
  };

  const copyToClipboard = (content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedMessageId(content);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  return (
    <section className="relative py-32 overflow-hidden">
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 w-[min(600px,92vw)] h-[360px] rounded-full bg-purple-500/5 blur-3xl avora-drift"
          animate={{ y: [0, -10, 0], opacity: [0.45, 0.7, 0.45] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>
      <div className="max-w-4xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="text-center"
        >
          <SectionHeading
            label="Capabilities"
            title="What AVORA can do"
            description="Explore the boundaries of what's possible with a truly intelligent companion."
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.98 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, delay: 0.14, ease: [0.16, 1, 0.3, 1] }}
          className="mt-16"
        >
          <motion.div
            className="max-w-2xl mx-auto hover-lift"
            whileHover={{ y: -3 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
                <div className="flex items-center gap-3">
                  <InteractiveAvoraCore state={isTyping ? 'thinking' : 'idle'} size={24} />
                  <div>
                    <h4 className="text-sm font-medium text-white">AVORA</h4>
                    <motion.p
                      className="text-xs text-gray-500"
                      animate={{ opacity: isTyping ? [0.5, 1, 0.5] : 1 }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      {isTyping ? 'Thinking...' : 'Online'}
                    </motion.p>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="p-5 space-y-4 h-64 overflow-y-auto scrollbar-thin">
                <AnimatePresence>
                  {messages.map((msg, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ 
                        duration: 0.4, 
                        delay: index * 0.1, 
                        ease: [0.16, 1, 0.3, 1] 
                      }}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed relative group ${
                          msg.role === 'user'
                            ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/20 text-white rounded-tr-sm'
                            : 'bg-white/[0.06] text-gray-300 rounded-tl-sm'
                        }`}
                      >
                        {msg.content}
                        <button
                          onClick={() => copyToClipboard(msg.content)}
                          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded text-gray-400 hover:text-white hover:bg-white/10"
                          aria-label="Copy message"
                        >
                          {copiedMessageId === msg.content ? (
                            <Check size={12} className="text-green-400" />
                          ) : (
                            <Copy size={12} />
                          )}
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {isTyping && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex justify-start"
                  >
                    <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-white/[0.06]">
                      <div className="flex gap-1">
                        {[0, 1, 2].map((i) => (
                          <motion.div
                            key={i}
                            className="w-1.5 h-1.5 rounded-full bg-gray-500"
                            animate={{ opacity: [0.3, 1, 0.3] }}
                            transition={{
                              duration: 1,
                              repeat: Infinity,
                              delay: i * 0.2,
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-4 border-t border-white/[0.06]">
                <div className="flex items-center gap-2">
                  <motion.input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask AVORA anything..."
                    className="flex-1 bg-transparent text-sm text-gray-200 placeholder-gray-500 outline-none"
                    whileFocus={{ scale: 1.02 }}
                  />
                  <motion.button
                    onClick={() => handleSend(input)}
                    disabled={!input.trim() || isTyping}
                    className="p-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 text-white hover-target disabled:opacity-50"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                  >
                    <ArrowRight size={16} />
                  </motion.button>
                </div>
              </div>
              </div>
            </motion.div>
          </motion.div>
      </div>
    </section>
  );
}

export default ChatPreview;