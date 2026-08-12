/**
 * Admin Dashboard - Global Search
 *
 * Searches REAL data: analytics events (summary) plus locally stored
 * feedback, bug reports, and feature requests. No mock rows.
 */

'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, MessageSquare, Lightbulb, Bug, Download, FileText, Users } from 'lucide-react';
import { getBugReports, getFeatureRequests } from '../../lib/storage';
import { useAnalyticsSummary } from '../../hooks/useAnalyticsSummary';

type ItemType = 'feedback' | 'bug' | 'feature' | 'download' | 'user' | 'event';

interface SearchItem {
  type: ItemType;
  title: string;
  description: string;
  date: string;
}

const typeConfig: Record<ItemType, { icon: any; color: string }> = {
  feedback: { icon: MessageSquare, color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
  bug: { icon: Bug, color: 'text-red-400 bg-red-500/10 border-red-500/20' },
  feature: { icon: Lightbulb, color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' },
  download: { icon: Download, color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
  user: { icon: Users, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
  event: { icon: FileText, color: 'text-gray-400 bg-gray-500/10 border-gray-500/20' },
};

export function SearchSection() {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<string>('all');
  const { state } = useAnalyticsSummary('all');

  const allItems = useMemo<SearchItem[]>(() => {
    const items: SearchItem[] = [];

    // Local feedback/bugs/features stored in the browser
    getBugReports().forEach((r: any) => items.push({
      type: 'bug',
      title: 'Bug Report',
      description: r.error_message || r.comments || 'No description',
      date: r.timestamp ? new Date(r.timestamp).toISOString().slice(0, 10) : 'unknown',
    }));
    getFeatureRequests().forEach((r: any) => items.push({
      type: 'feature',
      title: r.title || 'Feature Request',
      description: r.description || '',
      date: (r.date || r.timestamp) ? new Date(r.date || r.timestamp).toISOString().slice(0, 10) : 'unknown',
    }));

    if (state.status === 'ready') {
      const d = state.data;
      items.push({ type: 'download', title: `${d.totals.downloads} downloads`, description: 'Total downloads tracked', date: d.generatedAt.slice(0, 10) });
      items.push({ type: 'user', title: `${d.totals.totalUsers} users`, description: `${d.totals.activeUsers} active`, date: d.generatedAt.slice(0, 10) });
      items.push({ type: 'event', title: `${d.totals.totalEvents} events`, description: 'Total tracked events', date: d.generatedAt.slice(0, 10) });
      d.breakdowns.providers.forEach((p) => items.push({ type: 'event', title: `${p.name} AI requests`, description: `${p.count} requests (${p.percentage}%)`, date: d.generatedAt.slice(0, 10) }));
      d.breakdowns.platforms.forEach((p) => items.push({ type: 'download', title: p.name, description: `${p.count} platform events`, date: d.generatedAt.slice(0, 10) }));
    }

    return items;
  }, [state]);

  const results = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase();
    return allItems.filter((item) => {
      if (searchType !== 'all' && item.type !== searchType) return false;
      return item.title.toLowerCase().includes(q) || item.description.toLowerCase().includes(q);
    });
  }, [query, searchType, allItems]);

  const counts = useMemo(() => {
    const c: Record<string, number> = { feedback: 0, bug: 0, feature: 0, download: 0, user: 0, event: 0 };
    allItems.forEach((i) => { c[i.type] = (c[i.type] || 0) + 1; });
    return c;
  }, [allItems]);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Global Search</h3>
        <div className="space-y-4">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text" value={query} onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across real data..."
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.08] text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all"
              autoFocus
            />
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {['all', 'feedback', 'bug', 'feature', 'download', 'user'].map((type) => (
              <button key={type} onClick={() => setSearchType(type)}
                className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                  searchType === type ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] border border-transparent'}`}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {query.trim() && results.length === 0 && (
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-12 text-center">
            <Search size={32} className="text-gray-600 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No results found for "{query}"</p>
          </div>
        )}

        {results.map((result, index) => {
          const cfg = typeConfig[result.type];
          const Icon = cfg.icon;
          return (
            <motion.div key={`${result.type}-${index}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6 cursor-pointer hover:bg-white/[0.04] transition-all">
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg border ${cfg.color}`}><Icon size={14} /></div>
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

        {!query.trim() && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Quick label="Total Items" value={allItems.length} icon={FileText} color="blue" />
            <Quick label="Bugs (local)" value={counts.bug} icon={Bug} color="red" />
            <Quick label="Features (local)" value={counts.feature} icon={Lightbulb} color="yellow" />
          </div>
        )}
      </div>
    </div>
  );
}

function Quick({ label, value, icon: Icon, color }: { label: string; value: number; icon: any; color: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} className={`text-${color}-400`} />
        <p className="text-xs text-gray-500">{label}</p>
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
    </div>
  );
}
