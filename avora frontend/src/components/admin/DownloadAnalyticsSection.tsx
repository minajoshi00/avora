/**
 * Admin Dashboard - Download Analytics Section
 *
 * Real download counts and platform breakdown from the analytics server.
 */

'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Download, TrendingUp, Calendar } from 'lucide-react';
import { useAnalyticsSummary } from '../../hooks/useAnalyticsSummary';
import { LoadingState, ErrorState, EmptyState } from './AnalyticsStates';
import { formatCount, formatRate, type Range } from '../../lib/analytics-client';

const timeRanges: { id: Range; label: string }[] = [
  { id: 'today', label: 'Today' },
  { id: '7d', label: '7 Days' },
  { id: '30d', label: '30 Days' },
  { id: '90d', label: '90 Days' },
];

export function DownloadAnalyticsSection() {
  const [range, setRange] = useState<Range>('7d');
  const { state } = useAnalyticsSummary(range);

  if (state.status === 'loading') return <LoadingState />;
  if (state.status === 'error') return <ErrorState message={state.message} />;

  const { totals, rates, breakdowns, series, hasData } = state.data;
  const platformTotal = breakdowns.platforms.reduce((s, p) => s + p.count, 0) || 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        {timeRanges.map((r) => (
          <button
            key={r.id}
            onClick={() => setRange(r.id)}
            className={`px-4 py-2 rounded-lg text-sm transition-all ${
              range === r.id
                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] border border-transparent'
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {!hasData ? (
        <EmptyState label="No downloads tracked yet" />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard icon={Download} color="blue" label="Downloads (range)" value={formatCount(totals.downloads)}
              delta={formatRate(rates.downloads)} />
            <StatCard icon={TrendingUp} color="purple" label="App Launches" value={formatCount(totals.appLaunches)} />
            <StatCard icon={Calendar} color="emerald" label="Conversations" value={formatCount(totals.totalConversations)} />
            <StatCard icon={Download} color="yellow" label="Total Events" value={formatCount(totals.totalEvents)} />
          </div>

          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
            <h3 className="text-sm font-semibold text-gray-300 mb-4">Downloads Over Time</h3>
            {series && series.downloads.some((v) => v > 0) ? (
              <SeriesBars labels={series.labels} values={series.downloads} />
            ) : (
              <p className="text-xs text-gray-500">No downloads in this range.</p>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">By Platform</h3>
              {breakdowns.platforms.length ? (
                <div className="space-y-3">
                  {breakdowns.platforms.map((p) => (
                    <div key={p.name} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-400 capitalize">{p.name}</span>
                        <span className="text-gray-500">{p.percentage}%</span>
                      </div>
                      <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                        <motion.div initial={{ width: 0 }} animate={{ width: `${p.percentage}%` }}
                          transition={{ duration: 1, delay: 0.2 }} className="h-full rounded-full bg-blue-500" />
                      </div>
                      <p className="text-xs text-gray-500">{p.count} downloads</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500">No platform data recorded.</p>
              )}
            </div>

            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">Conversion (real, computed)</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-gray-500">Visitor → Download</span>
                    <span className="text-xs text-gray-400">
                      {totals.totalEvents ? ((totals.downloads / Math.max(1, totals.totalEvents)) * 100).toFixed(1) : '0.0'}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                    <motion.div initial={{ width: 0 }}
                      animate={{ width: `${Math.min(100, (totals.downloads / Math.max(1, totals.totalEvents)) * 100)}%` }}
                      transition={{ duration: 1 }} className="h-full rounded-full bg-emerald-500" />
                  </div>
                </div>
                <p className="text-xs text-gray-600">Based on {totals.downloads} downloads across {platformTotal} platform events.</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({
  icon: Icon, color, label, value, delta,
}: {
  icon: typeof Download; color: string; label: string; value: string; delta?: { text: string; positive: boolean };
}) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} className={`text-${color}-400`} />
        <p className="text-xs text-gray-500">{label}</p>
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
      {delta && (
        <p className={`text-xs mt-1 ${delta.positive ? 'text-emerald-400' : 'text-red-300'}`}>{delta.text}</p>
      )}
    </div>
  );
}

function SeriesBars({ labels, values }: { labels: string[]; values: number[] }) {
  const max = Math.max(1, ...values);
  return (
    <div className="space-y-2">
      {values.map((v, i) => (
        <div key={labels[i]} className="flex items-center gap-3">
          <span className="text-xs text-gray-500 w-16">{labels[i]?.slice(5) || labels[i]}</span>
          <div className="flex-1 h-8 rounded-lg bg-white/[0.03] relative overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(v / max) * 100}%` }}
              transition={{ duration: 0.8, delay: i * 0.1 }}
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg"
            />
          </div>
          <span className="text-xs text-gray-400 w-12 text-right">{v}</span>
        </div>
      ))}
    </div>
  );
}
