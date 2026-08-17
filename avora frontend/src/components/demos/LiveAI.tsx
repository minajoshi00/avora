'use client';

import { useState, useEffect } from 'react';

type Message = {
  id: string;
  role: 'user' | 'avora';
  content: string;
};

type AIStatus = 'idle' | 'connecting' | 'thinking' | 'responding' | 'error' | 'empty';

interface AIConfig {
  suggestedPrompts: string[];
  apiEndpoint: string;
};

const DEFAULT_CONFIG: AIConfig = {
  suggestedPrompts: [
    'Explain what AVORA is.',
    'How does AVORA understand context?',
    'What makes AVORA different?',
    'Show me what you can do.',
  ],
  apiEndpoint: '/api/ai/gemini',
};

export function LiveAI() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'avora',
      content: 'Hello. I am AVORA. What shall we explore together?',
    },
  ]);
  const [input, setInput] = useState('');
  const [aiStatus, setAIStatus] = useState<AIStatus>('idle');
  const [isConnected, setIsConnected] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [showReset, setShowReset] = useState(false);

  useEffect(() => {
    const checkMaintenance = async () => {
      try {
        const maintenanceRes = await fetch('/api/admin/maintenance/status', {
          cache: 'no-store',
        });
        const data = await maintenanceRes.json();
        if (data.maintenanceMode) {
          setAIStatus('error');
          setLastError('AI demo is unavailable while maintenance mode is active.');
          setIsConnected(false);
        }
      } catch {
        // proceed if check fails
      }
    };

    checkMaintenance();
    const interval = setInterval(() => checkMaintenance(), 30000);
    return () => clearInterval(interval);
  }, []);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setAIStatus('connecting');
    setLastError(null);
    setShowReset(false);

    try {
      const res = await fetch('/api/ai/gemini', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: text }),
        cache: 'no-store',
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error || 'AI service failed');
      }

      const data = await res.json();
      setAIStatus('responding');

      const avoraMessage: Message = {
        id: (Date.now() + Math.random()).toString(),
        role: 'avora',
        content:
          data.response || 'I encountered an issue processing your request.',
      };

      setMessages((prev) => [...prev, avoraMessage]);
      setAIStatus('idle');
      setIsConnected(true);
      setShowReset(true);
    } catch (err) {
      console.error('AI demo error:', err);
      setAIStatus('error');
      setLastError(
        err instanceof Error ? err.message : 'An unexpected error occurred. Please try again.'
      );
      setShowReset(true);
    }
  };

  const handleSend = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    setInput('');
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey && input.trim()) {
        sendMessage(input);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (lastError && aiStatus === 'idle') {
      const timer = setTimeout(() => setLastError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [lastError, aiStatus]);

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl overflow-hidden max-w-2xl w-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-400/20 flex items-center justify-center">
            <svg className="w-5 h-5 text-blue-400" viewBox="0 0 24 24">
              <path d="M20 21v-2a4 4 0 0 0-4-4H4a4 4 0 0 0-4 4v2" />
              <path d="M9 10h6v7a4 4 0 0 0 4 4h4a4 4 0 0 0 4-4v-7h6z" />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-medium text-white">AVORA</h4>
            <p className="text-xs text-gray-400">{isConnected ? 'Connected' : 'Disconnected'}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {aiStatus !== 'idle' && aiStatus !== 'error' && (
            <span className="w-8 h-8 animate-spin bg-blue-500/20 border border-blue-400/20" />
          )}
          {aiStatus === 'error' && (
            <svg className="w-5 h-5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="12" cy="12" r="10" />
              <path d="M15 3H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z" />
            </svg>
          )}
          {isConnected && (
            <button onClick={() => setMessages([{ id: '1', role: 'avora', content: 'Hello. I am AVORA. What shall we explore together?' }])} className="p-1 rounded-lg hover:bg-white/[0.04] transition-colors text-gray-400 hover:text-gray-300">
              Reset
            </button>
          )}
          {aiStatus === 'error' && (
            <svg className="w-5 h-5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="12" cy="12" r="10" />
              <path d="M15 3H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z" />
            </svg>
          )}
        </div>
      </div>

      <div className="p-6 h-[400px] overflow-y-auto space-y-4">
        {messages.map((msg, _index) => (
          <div
            key={msg.id}
            className={msg.role === 'user'
              ? 'max-w-[80%] px-4 py-2.5 rounded-2xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/20 text-white rounded-tr-sm'
              : 'px-4 py-2.5 rounded-2xl bg-white/[0.06] text-gray-300 rounded-tl-sm'
            }
          >
            <div className="break-all">{msg.content}</div>
          </div>
        ))}
        {aiStatus === 'thinking' && (
          <div className="flex justify-end pt-2">
            <div className="px-4 py-2 rounded-2xl bg-white/[0.06] border border-blue-400/20 text-sm text-white">
              AVORA is thinking...
            </div>
          </div>
          )}
        {aiStatus === 'error' && lastError && (
          <div className="flex justify-end pt-2">
            <div className="px-4 py-2 rounded-2xl bg-white/[0.06] border border-red-500/20 text-sm text-white">
              {lastError}
            </div>
          </div>
          )}
        {showReset && aiStatus !== 'idle' && (
          <div className="flex justify-end pt-2">
            <button onClick={() => setMessages([{ id: '1', role: 'avora', content: 'Hello. I am AVORA. What shall we explore together?' }])} className="p-1 rounded-lg hover:bg-white/[0.04] transition-colors text-gray-400 hover:text-gray-300">
              Try another
            </button>
          </div>
          )}
      </div>

      <div className="p-4 border-t border-white/[0.06] flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
          placeholder="Type a message..."
          className="flex-1 bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-blue-400/30 transition-colors"
          aria-label="Message AVORA"
        />
        <button
          type="submit"
          onClick={handleSend}
          disabled={aiStatus !== 'idle' || !input.trim()}
          className="p-1.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white hover-target disabled:opacity-50"
          title="Send message to AVORA"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M21 15v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1M11 7h2v2h-2v-2zm-6 6h2v2H7v-2zm6 2v2h2v-2zm2-7h2v3h-2v-3zm2 7h2v2h-2v-2z" />
          </svg>
        </button>
      </div>

      {messages.length === 1 && (
        <div className="px-6 py-4 border-t border-white/[0.06]">
          <p className="text-sm text-gray-400 mb-4">Ask AVORA anything:</p>
          <div className="flex flex-wrap gap-2">
            {DEFAULT_CONFIG.suggestedPrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => {
                  setInput(prompt);
                  sendMessage(prompt);
                }}
                className="px-2 py-1 rounded-full border border-white/[0.08] bg-white/[0.02] text-xs text-gray-400 hover:text-white hover:border-white/[0.15] transition-all"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default LiveAI;