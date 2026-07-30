/**
 * Admin Dashboard - Global Search
 */

'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, MessageSquare, Lightbulb, Bug, Download, FileText, Users } from 'lucide-react';

// Mock searchable data
const mockData = [
  { type: 'feedback', title: 'Great app!', description: 'Really enjoying using AVORA', date: '2026-07-30' },
  { type: 'bug', title: 'Crash on startup', description: 'App crashes when opening settings', date: '2026-07-29' },
  { type: 'feature', title: 'Dark mode', description: 'Add more theme options', date: '2026-07-28' },
  { type: 'download', title: 'v1.0.0', description: '245 MB installer', date: '2026-07-20' },
  { type: 'user', title: 'User #1234', description: 'Active user from United States', date: '2026-07-30' },
];

const typeConfig = {
  feedback: { icon: MessageSquare, color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
  bug: { icon: Bug, color: 'text-red-400 bg-red-500/10 border-red-500/20' },
  feature: { icon: Lightbulb, color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' },
  download: { icon: Download, color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
  user: { icon: Users, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
};

export function SearchSection() {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<string>('all');

  const results = useMemo(() => {
    if (!query.trim()) return [];
    
    const lowerQuery = query.toLowerCase();
    return mockData.filter(item => {
      if (searchType !== 'all' && item.type !== searchType) return false;
      return (
        item.title.toLowerCase().includes(lowerQuery) ||
        item.description.toLowerCase().includes(lowerQuery)
      );
    });
  }, [query, searchType]);

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Global Search</h3>
        
        <div className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across all data..."
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.08] text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all"
              autoFocus
            />
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-2">
            {['all', 'feedback', 'bug', 'feature', 'download', 'user'].map((type) => (
              <button
                key={type}
                onClick={() => setSearchType(type)}
                className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                  searchType === type
                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] border border-transparent'
                }`}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="space-y-3">
        {query.trim() && results.length === 0 && (
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-12 text-center">
            <Search size={32} className="text-gray-600 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No results found for "{query}"</p>
          </div>
        )}

        {results.map((result, index) => {
          const TypeIcon = typeConfig[result.type as keyof typeof typeConfig]?.icon || FileText;
          const typeColor = typeConfig[result.type as keyof typeof typeConfig]?.color || 'text-gray-400 bg-gray-500/10 border-gray-500/20';
          
          return (
            <motion.div
              key={`${result.type}-${index}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6 cursor-pointer hover:bg-white/[0.04] transition-all"
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg border ${typeColor}`}>
                  <TypeIcon size={14} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-white">{result.title}</h3>
                    <span className="text-xs text-gray-500">•</span>
                    <span className="text-xs text-gray-500 capitalize">{result.type}</span>
                  </div>
                  <p className="text-xs text-gray-400 mb-2">{result.description}</p>
                  <p className="text-xs text-gray-600">{result.date}</p>
                </div>
              </div>
            </motion.div>
          );
        })}

        {/* Quick Stats */}
        {!query.trim() && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
              <div className="flex items-center gap-2 mb-1">
                <FileText size={14} className="text-blue-400" />
                <p className="text-xs text-gray-500">Total Items</p>
              </div>
              <p className="text-xl font-bold text-white">{mockData.length}</p>
            </div>
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
              <div className="flex items-center gap-2 mb-1">
                <Bug size={14} className="text-red-400" />
                <p className="text-xs text-gray-500">Bugs</p>
              </div>
              <p className="text-xl font-bold text-white">{mockData.filter(i => i.type === 'bug').length}</p>
            </div>
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
              <div className="flex items-center gap-2 mb-1">
                <Lightbulb size={14} className="text-yellow-400" />
                <p className="text-xs text-gray-500">Features</p>
              </div>
              <p className="text-xl font-bold text-white">{mockData.filter(i => i.type === 'feature').length}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}