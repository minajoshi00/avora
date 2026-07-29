'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Mic, Image as ImageIcon } from 'lucide-react';
import { InteractiveAvoraCore } from '../brand/InteractiveAvoraCore';
import { cn } from '../../lib/utils';

interface Message {
  id: string;
  role: 'user' | 'avora';
  content: string;
}

const suggestedPrompts = [
  'What can you help me with?',
  'Tell me something surprising',
  'Help me brainstorm ideas',
];

const avoraResponses: Record<string, string> = {
  'What can you help me with?':
    'I can help with conversations, creative projects, analysis, coding, writing, and much more. Think of me as a thinking partner.',
  'Tell me something surprising':
    'The human brain generates about 12-25 watts of electricity continuously — enough to power a small LED bulb. Intelligence comes in many forms.',
  'Help me brainstorm ideas':
    'Tell me what domain you want to explore — design, technology, writing, business — and I will help map possibilities.',
};

export function ChatDemo() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'avora',
      content: 'Hello. I am AVORA. What shall we explore together?',
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);

  const handleSend = (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setSelectedPrompt(null);
    setIsTyping(true);

    setTimeout(() => {
      const responseText = avoraResponses[text] || 'That is interesting. Tell me more — I want to understand.';
      const avoraMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'avora',
        content: responseText,
      };
      setMessages((prev) => [...prev, avoraMessage]);
      setIsTyping(false);
    }, 1200 + Math.random() * 800);
  };

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl overflow-hidden">
      {/* Header */}
      <motion.div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
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
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.1, rotate: 5 }}
            whileTap={{ scale: 0.9 }}
            className="p-2 rounded-lg hover:bg-white/[0.04] transition-colors text-gray-500 hover:text-gray-300 hover-target"
          >
            <ImageIcon size={16} />
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.1, rotate: -5 }}
            whileTap={{ scale: 0.9 }}
            className="p-2 rounded-lg hover:bg-white/[0.04] transition-colors text-gray-500 hover:text-gray-300 hover-target"
          >
            <Mic size={16} />
          </motion.button>
        </div>
      </motion.div>

      {/* Messages */}
      <div className="p-5 space-y-4 h-64 overflow-y-auto scrollbar-thin">
        <AnimatePresence>
          {messages.map((msg, index) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{
                duration: 0.4,
                delay: index * 0.1,
                ease: [0.16, 1, 0.3, 1]
              }}
              whileHover={{ scale: 1.02 }}
              className={cn(
                'flex',
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  'max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/20 text-white rounded-tr-sm'
                    : 'bg-white/[0.06] text-gray-300 rounded-tl-sm'
                )}
              >
                {msg.content}
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
                {[...Array(3)].map((_, i) => (
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
      </div>

      {/* Suggested prompts */}
      {messages.length === 1 && !selectedPrompt && (
        <div className="px-5 pb-3">
          <div className="flex flex-wrap gap-2">
            {suggestedPrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => setSelectedPrompt(prompt)}
                className="px-3 py-1.5 rounded-full border border-white/[0.08] bg-white/[0.02] text-xs text-gray-400 hover:text-white hover:border-white/[0.15] transition-all duration-300"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-white/[0.06]">
        <div className="flex items-center gap-2">
          <motion.input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
            placeholder="Type a message..."
            className="flex-1 bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-blue-400/30 transition-colors"
            whileFocus={{ scale: 1.02 }}
          />
          <motion.button
            onClick={() => handleSend(input)}
            disabled={!input.trim()}
            className="p-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white hover-target disabled:opacity-50"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            transition={{ type: 'spring', stiffness: 400, damping: 17 }}
          >
            <Send size={16} />
          </motion.button>
        </div>
      </div>
    </div>
  );
}

export default ChatDemo;