'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { hasValidSession, logout } from '../lib/admin';
import { trackEvent } from '../lib/analytics';
import { OverviewSection } from '../components/admin/OverviewSection';
import { UserAnalyticsSection } from '../components/admin/UserAnalyticsSection';
import { FeedbackCenter } from '../components/admin/FeedbackCenter';
import { FeatureRequestsSection } from '../components/admin/FeatureRequestsSection';
import { BugReportsSection } from '../components/admin/BugReportsSection';
import { DownloadAnalyticsSection } from '../components/admin/DownloadAnalyticsSection';
import { SystemHealthSection } from '../components/admin/SystemHealthSection';
import { ChangelogManager } from '../components/admin/ChangelogManager';
import { SearchSection } from '../components/admin/SearchSection';
import {
  LayoutDashboard, Users, MessageSquare, Lightbulb, Bug, Download, Activity,
  RefreshCw, Search, LogOut, ChevronRight, BarChart3, User, Shield,
  History,
} from 'lucide-react';
import { useAnalyticsSummary } from '../hooks/useAnalyticsSummary';
import { LoadingState, ErrorState, EmptyState } from '../components/admin/AnalyticsStates';
import { formatCount, formatRate, type Range } from '../lib/analytics-client';

type Section =
  | 'overview' | 'users' | 'feedback' | 'features' | 'bugs'
  | 'downloads' | 'health' | 'changelog' | 'updates' | 'search'
  | 'analytics' | 'visitors';

const sections: { id: Section; label: string; icon: any }[] = [
  { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'analytics', label: '📈 Website Analytics', icon: BarChart3 },
  { id: 'users', label: '👥 Visitors', icon: User },
  { id: 'downloads', label: '📥 Downloads', icon: Download },
  { id: 'feedback', label: '💬 Feedback', icon: MessageSquare },
  { id: 'bugs', label: '🐞 Bug Reports', icon: Bug },
  { id: 'features', label: '💡 Feature Requests', icon: Lightbulb },
  { id: 'health', label: '⚙ System Status', icon: Shield },
  { id: 'changelog', label: '📜 Logs', icon: History },
  { id: 'updates', label: '📈 Charts', icon: RefreshCw },
  { id: 'search', label: 'Recent Activity', icon: Search },
];

const sectionLabels: Record<Section, string> = {
  overview: 'Dashboard',
  analytics: 'Website Analytics',
  users: 'Visitors',
  visitors: 'Visitors',
  downloads: 'Downloads',
  feedback: 'Feedback',
  features: 'Feature Requests',
  bugs: 'Bug Reports',
  health: 'System Status',
  changelog: 'Logs',
  updates: 'Charts',
  search: 'Recent Activity',
};

export default function AdminDashboardPage() {
  const [activeSection, setActiveSection] = useState<Section>('overview');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#/admin/', '');
      if (hash) {
        const section = hash as Section;
        if (sections.find((s) => s.id === section)) setActiveSection(section);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    handleHashChange();
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    if (hasValidSession()) {
      setIsAuthenticated(true);
      setIsLoading(false);
    } else {
      window.location.hash = '#/admin';
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) trackEvent('admin_navigate', { props: { section: activeSection } });
  }, [activeSection, isAuthenticated]);

  const handleLogout = () => {
    trackEvent('admin_logout');
    logout();
    window.location.hash = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const navigateTo = (section: Section) => {
    setActiveSection(section);
    window.location.hash = `#/admin/${section}`;
    trackEvent('admin_navigate', { props: { section } });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="w-12 h-12 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex">
      <aside className="w-64 border-r border-white/[0.08] bg-white/[0.02] flex flex-col">
        <div className="p-6 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/[0.08] flex items-center justify-center">
              <span className="text-xl">⚙️</span>
            </div>
            <div>
              <h1 className="text-sm font-bold text-white">Admin Console</h1>
              <p className="text-xs text-gray-500">AVORA Developer</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {sections.map((section) => {
            const Icon = section.icon;
            const isActive = activeSection === section.id;
            return (
              <button
                key={section.id}
                onClick={() => navigateTo(section.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                  isActive
                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] border border-transparent'
                }`}
              >
                <Icon size={16} />
                <span className="flex-1 text-left">{section.label}</span>
                {isActive && <ChevronRight size={14} />}
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/[0.08]">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-red-400 hover:bg-red-500/10 transition-all"
          >
            <LogOut size={16} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <header className="sticky top-0 z-10 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/[0.08] px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">{sectionLabels[activeSection] || 'Dashboard'}</h2>
              <p className="text-xs text-gray-500 mt-1">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-500">v1.0.0</span>
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
          </div>
        </header>

        <div className="p-8">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {renderSection(activeSection)}
          </motion.div>
        </div>
      </main>
    </div>
  );
}

function renderSection(section: Section) {
  switch (section) {
    case 'overview': return <OverviewSection />;
    case 'users': return <UserAnalyticsSection />;
    case 'feedback': return <FeedbackCenter />;
    case 'features': return <FeatureRequestsSection />;
    case 'bugs': return <BugReportsSection />;
    case 'downloads': return <DownloadAnalyticsSection />;
    case 'health': return <SystemHealthSection />;
    case 'changelog': return <ChangelogManager />;
    case 'updates': return <ChartsSection />;
    case 'search': return <SearchSection />;
    case 'analytics': return <AnalyticsSection />;
    case 'visitors': return <VisitorsSection />;
    default: return <OverviewSection />;
  }
}

function AnalyticsSection() {
  const [range, setRange] = useState<Range>('7d');
  const { state, reload } = useAnalyticsSummary(range);
  const ranges: { id: Range; label: string }[] = [
    { id: 'today', label: 'Today' }, { id: '7d', label: '7 Days' },
    { id: '30d', label: '30 Days' }, { id: '90d', label: '90 Days' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        {ranges.map((r) => (
          <button key={r.id} onClick={() => setRange(r.id)}
            className={`px-4 py-2 rounded-lg text-sm transition-all ${
              range === r.id ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] border border-transparent'}`}>
            {r.label}
          </button>
        ))}
      </div>

      {state.status === 'loading' && <LoadingState />}
      {state.status === 'error' && <ErrorState message={state.message} onRetry={reload} />}
      {state.status === 'ready' && (
        <>
          {!state.data.hasData ? <EmptyState label="No analytics data yet" /> : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card icon={Users} color="blue" label="Total Visitors" value={formatCount(state.data.totals.totalUsers)} delta={formatRate(state.data.rates.newUsers)} />
              <Card icon={BarChart3} color="purple" label="AI Requests" value={formatCount(state.data.totals.aiRequests)} />
              <Card icon={Activity} color="emerald" label="Errors" value={formatCount(state.data.totals.errors)} />
              <Card icon={Shield} color="cyan" label="App Launches" value={formatCount(state.data.totals.appLaunches)} />
            </div>
          )}
        </>
      )}
    </div>
  );
}

function VisitorsSection() {
  const { state, reload } = useAnalyticsSummary('30d');
  if (state.status === 'loading') return <LoadingState />;
  if (state.status === 'error') return <ErrorState message={state.message} onRetry={reload} />;

  const countries = state.data.breakdowns.countries;
  const platforms = state.data.breakdowns.platforms;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2"><User size={14} /> Visitor Countries</h3>
          {countries.length ? countries.map((c) => (
            <div key={c.name} className="flex items-center justify-between py-1">
              <span className="text-xs text-gray-400">{c.name}</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                  <div className="h-full rounded-full bg-blue-500" style={{ width: `${c.percentage}%` }} />
                </div>
                <span className="text-xs text-gray-500 w-12 text-right">{c.percentage}%</span>
              </div>
            </div>
          )) : <p className="text-xs text-gray-500">No country data recorded.</p>}
        </div>

        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2"><Activity size={14} /> Platforms</h3>
          {platforms.length ? platforms.map((p) => (
            <div key={p.name} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] mb-2">
              <span className="text-sm text-gray-300 capitalize">{p.name}</span>
              <span className="text-sm font-medium text-white">{p.percentage}%</span>
            </div>
          )) : <p className="text-xs text-gray-500">No platform data recorded.</p>}
        </div>
      </div>
    </div>
  );
}

function ChartsSection() {
  const { state, reload } = useAnalyticsSummary('30d');
  if (state.status === 'loading') return <LoadingState />;
  if (state.status === 'error') return <ErrorState message={state.message} onRetry={reload} />;

  const { series, totals, rates, hasData } = state.data;

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-bold text-white mb-4">Analytics Charts</h3>
      {!hasData ? <EmptyState label="No analytics data yet" /> : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
            <h4 className="text-sm font-semibold text-gray-300 mb-4">Traffic Over Time (pageviews)</h4>
            <MiniBars labels={series.labels} values={series.pageviews} />
          </div>
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
            <h4 className="text-sm font-semibold text-gray-300 mb-4">Growth (real, computed)</h4>
            <div className="grid grid-cols-2 gap-4">
              <Growth label="Downloads" rate={rates.downloads} />
              <Growth label="New Users" rate={rates.newUsers} />
              <Growth label="Conversations" rate={rates.conversations} />
              <Growth label="Pageviews" rate={rates.pageviews} />
            </div>
            <p className="text-xs text-gray-600 mt-4">
              {totals.totalEvents} total real events tracked.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function Card({ icon: Icon, color, label, value, delta }: { icon: any; color: string; label: string; value: string; delta?: { text: string; positive: boolean } }) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg bg-${color}-500/10 border border-${color}-500/20`}>
          <Icon size={16} className={`text-${color}-400`} />
        </div>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      {delta && <p className={`text-xs mt-1 ${delta.positive ? 'text-emerald-400' : 'text-red-300'}`}>{delta.text}</p>}
    </div>
  );
}

function Growth({ label, rate }: { label: string; rate: number }) {
  const positive = rate >= 0;
  return (
    <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${positive ? 'text-emerald-400' : 'text-red-300'}`}>
        {positive ? '+' : ''}{rate}%
      </p>
      <p className="text-[10px] text-gray-600">vs previous period</p>
    </div>
  );
}

function MiniBars({ labels, values }: { labels: string[]; values: number[] }) {
  const max = Math.max(1, ...values);
  return (
    <div className="h-48 flex items-end justify-between gap-2">
      {values.map((v, i) => (
        <div key={labels[i]} className="flex-1 flex flex-col items-center">
          <div className="w-full rounded-t bg-gradient-to-t from-blue-500 to-purple-500"
            style={{ height: `${Math.max(2, (v / max) * 100)}%` }} title={`${labels[i]}: ${v}`} />
          <span className="text-[9px] text-gray-600 mt-1">{labels[i]?.slice(8) || ''}</span>
        </div>
      ))}
    </div>
  );
}
