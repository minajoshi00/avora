/**
 * Admin Dashboard - Overview Section
 *
 * High-level metrics. Numbers come from the analytics server; the
 * Open Bugs count comes from real locally-stored bug reports.
 */

'use client';

import { motion } from 'framer-motion';
import {
  Users, Download, MessageSquare, Bug, Activity, Monitor, Clock, TrendingUp, Globe,
} from 'lucide-react';
import { getBugReports } from '../../lib/storage';
import { useAnalyticsSummary } from '../../hooks/useAnalyticsSummary';
import { LoadingState, ErrorState } from './AnalyticsStates';
import { formatCount, formatRate } from '../../lib/analytics-client';

export function OverviewSection() {
  const bugReports = getBugReports();
  const { state } = useAnalyticsSummary('30d');

  if (state.status === 'loading') return <LoadingState />;
  if (state.status === 'error') return <ErrorState message={state.message} />;

  const { totals, rates, breakdowns, hasData } = state.data;
  const providers = breakdowns.providers;

  const stats = [
    { label: 'Total Users', value: formatCount(totals.totalUsers), change: formatRate(rates.newUsers), icon: Users, color: 'blue' },
    { label: 'Active Users (30d)', value: formatCount(totals.activeUsers), change: { text: 'live', positive: true }, icon: Activity, color: 'yellow' },
    { label: 'Downloads', value: formatCount(totals.downloads), change: formatRate(rates.downloads), icon: Download, color: 'emerald' },
    { label: 'Conversations', value: formatCount(totals.totalConversations), change: formatRate(rates.conversations), icon: MessageSquare, color: 'purple' },
    { label: 'AI Requests', value: formatCount(totals.aiRequests), change: { text: 'live', positive: true }, icon: Globe, color: 'cyan' },
    { label: 'Errors', value: formatCount(totals.errors), change: { text: 'live', positive: false }, icon: Bug, color: 'red' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-xl bg-${stat.color}-500/10 border border-${stat.color}-500/20`}>
                  <Icon size={20} className={`text-${stat.color}-400`} />
                </div>
                <span className={`text-xs font-medium ${stat.change.positive ? 'text-emerald-400' : 'text-red-300'}`}>
                  {stat.change.text}
                </span>
              </div>
              <div>
                <p className="text-2xl font-bold text-white mb-1">{stat.value}</p>
                <p className="text-xs text-gray-500">{stat.label}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Monitor size={14} /> AI Provider Usage
          </h3>
          {providers.length ? (
            <div className="space-y-3">
              {providers.map((p) => (
                <div key={p.name} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400 capitalize">{p.name}</span>
                    <span className="text-gray-500">{p.percentage}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: `${p.percentage}%` }}
                      transition={{ duration: 1, delay: 0.2 }} className="h-full rounded-full bg-blue-500" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500">No AI requests recorded.</p>
          )}
        </div>

        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <TrendingUp size={14} /> Engagement
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <Mini label="Messages" value={formatCount(totals.messagesSent)} />
            <Mini label="Missions made" value={formatCount(totals.missionsCreated)} />
            <Mini label="Missions done" value={formatCount(totals.missionsCompleted)} />
            <Mini label="Tasks done" value={formatCount(totals.tasksCompleted)} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <Bug size={16} className="text-red-400" />
            <p className="text-xs text-gray-500">Open Bugs (local reports)</p>
          </div>
          <p className="text-2xl font-bold text-white">{bugReports.length}</p>
          <p className="text-xs text-gray-500 mt-1">From user-submitted reports</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <Clock size={16} className="text-blue-400" />
            <p className="text-xs text-gray-500">Feedback</p>
          </div>
          <p className="text-2xl font-bold text-white">{formatCount(totals.feedbackTotal)}</p>
          <p className="text-xs text-gray-500 mt-1">Submitted ratings/notes</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <Activity size={16} className="text-purple-400" />
            <p className="text-xs text-gray-500">Total Events</p>
          </div>
          <p className="text-2xl font-bold text-white">{formatCount(totals.totalEvents)}</p>
          <p className="text-xs text-gray-500 mt-1">{hasData ? 'Real tracked events' : 'No data yet'}</p>
        </div>
      </div>
    </div>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-3">
      <p className="text-lg font-bold text-white">{value}</p>
      <p className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</p>
    </div>
  );
}
