/**
 * Admin Dashboard - User Analytics Section
 *
 * ALL numbers are computed from real events stored in the analytics server.
 * No hardcoded counters, percentages, or chart arrays.
 */

'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Users, TrendingUp, Clock, Globe, Monitor, Smartphone, Tablet, Activity,
} from 'lucide-react';
import { useAnalyticsSummary } from '../../hooks/useAnalyticsSummary';
import { LoadingState, ErrorState, EmptyState } from './AnalyticsStates';
import { formatCount, formatRate, type Range } from '../../lib/analytics-client';

const timeRanges: { id: Range; label: string }[] = [
  { id: 'today', label: 'Today' },
  { id: '7d', label: '7 Days' },
  { id: '30d', label: '30 Days' },
  { id: '90d', label: '90 Days' },
];

const deviceIcons: Record<string, typeof Monitor> = {
  windows: Monitor,
  macos: Monitor,
  linux: Monitor,
  mobile: Smartphone,
  tablet: Tablet,
  desktop: Monitor,
};

export function UserAnalyticsSection() {
  const [range, setRange] = useState<Range>('7d');
  const { state } = useAnalyticsSummary(range);

  const platforms = state.status === 'ready' ? state.data.breakdowns.platforms : [];
  const countries = state.status === 'ready' ? state.data.breakdowns.countries : [];
  const series = state.status === 'ready' ? state.data.series : null;

  // Build device breakdown from real platform data (best-effort grouping).
  const deviceMap: Record<string, number> = { Desktop: 0, Mobile: 0, Tablet: 0, Other: 0 };
  for (const p of platforms) {
    const name = p.name.toLowerCase();
    if (name.includes('android') || name.includes('ios') || name === 'mobile') deviceMap.Mobile += p.count;
    else if (name.includes('tablet') || name === 'ipad') deviceMap.Tablet += p.count;
    else if (name.includes('win') || name.includes('mac') || name.includes('linux') || name.includes('desktop')) deviceMap.Desktop += p.count;
    else deviceMap.Other += p.count;
  }
  const deviceTotal = Object.values(deviceMap).reduce((a, b) => a + b, 0) || 1;
  const devices = Object.entries(deviceMap)
    .filter(([, c]) => c > 0)
    .map(([name, count]) => ({
      name,
      count,
      percentage: +((count / deviceTotal) * 100).toFixed(1),
      icon: deviceIcons[name.toLowerCase()] || Monitor,
    }));

  if (state.status === 'loading') return <LoadingState />;
  if (state.status === 'error') return <ErrorState message={state.message} />;

  const { totals, rates, hasData } = state.data;

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
        <EmptyState label="No visitors tracked yet" />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard icon={Users} color="blue" label="Total Users" value={formatCount(totals.totalUsers)} />
            <StatCard icon={Activity} color="purple" label="Active Users" value={formatCount(totals.activeUsers)}
              delta={formatRate(rates.newUsers)} />
            <StatCard icon={TrendingUp} color="emerald" label="New Users" value={formatCount(totals.newUsers)}
              delta={formatRate(rates.newUsers)} />
            <StatCard icon={Clock} color="yellow" label="Returning Users" value={formatCount(totals.returningUsers)} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Activity chart (real daily series) */}
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">User Activity (daily)</h3>
              {series && series.pageviews.some((v) => v > 0) ? (
                <SeriesBars labels={series.labels} values={series.pageviews} />
              ) : (
                <p className="text-xs text-gray-500">No activity in this range.</p>
              )}
            </div>

            {/* Platforms from real download/pageview props */}
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                <Globe size={14} /> By Platform
              </h3>
              {platforms.length ? (
                <div className="space-y-3">
                  {platforms.map((p) => (
                    <div key={p.name} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-400 capitalize">{p.name}</span>
                        <span className="text-gray-500">{p.percentage}%</span>
                      </div>
                      <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                        <motion.div initial={{ width: 0 }} animate={{ width: `${p.percentage}%` }}
                          transition={{ duration: 0.8 }} className="h-full rounded-full bg-blue-500" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500">No platform data recorded.</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Countries (real, server-derived) */}
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                <Globe size={14} /> Top Countries
              </h3>
              {countries.length ? (
                <div className="space-y-2">
                  {countries.map((c) => (
                    <div key={c.name} className="flex items-center justify-between p-2 rounded-lg hover:bg-white/[0.02]">
                      <span className="text-xs text-gray-400">{c.name}</span>
                      <div className="flex items-center gap-3">
                        <div className="w-32 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${c.percentage}%` }} />
                        </div>
                        <span className="text-xs text-gray-500 w-16 text-right">{c.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500">No country data recorded.</p>
              )}
            </div>

            {/* Devices (derived) */}
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                <Monitor size={14} /> Device Types
              </h3>
              {devices.length ? (
                <div className="space-y-3">
                  {devices.map((d) => {
                    const Icon = d.icon;
                    return (
                      <div key={d.name} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                        <div className="flex items-center gap-3">
                          <Icon size={16} className="text-gray-400" />
                          <span className="text-sm text-gray-300">{d.name}</span>
                        </div>
                        <span className="text-sm font-medium text-white">{d.percentage}%</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-gray-500">No device data recorded.</p>
              )}
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
  icon: typeof Users; color: string; label: string; value: string; delta?: { text: string; positive: boolean };
}) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg bg-${color}-500/10 border border-${color}-500/20`}>
          <Icon size={16} className={`text-${color}-400`} />
        </div>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      {delta && (
        <p className={`text-xs mt-1 ${delta.positive ? 'text-emerald-400' : 'text-red-300'}`}>
          {delta.text} vs previous period
        </p>
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
              transition={{ duration: 0.8, delay: i * 0.05 }}
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg"
            />
          </div>
          <span className="text-xs text-gray-400 w-12 text-right">{v}</span>
        </div>
      ))}
    </div>
  );
}
