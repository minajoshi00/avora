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
import { UpdateManagement } from '../components/admin/UpdateManagement';
import { SearchSection } from '../components/admin/SearchSection';
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  Lightbulb,
  Bug,
  Download,
  Activity,
  FileText,
  RefreshCw,
  Search,
  LogOut,
  ChevronRight,
  BarChart3,
  User,
  Shield,
  History,
} from 'lucide-react';

type Section =
  | 'overview'
  | 'users'
  | 'feedback'
  | 'features'
  | 'bugs'
  | 'downloads'
  | 'health'
  | 'changelog'
  | 'updates'
  | 'search'
  | 'analytics'
  | 'visitors'
  | 'releases'
  | 'system'
  | 'logs'
  | 'charts';

const sections: { id: Section; label: string; icon: any }[] = [
  { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'analytics', label: '📈 Website Analytics', icon: BarChart3 },
  { id: 'users', label: '👥 Visitors', icon: User },
  { id: 'downloads', label: '📥 Downloads', icon: Download },
  { id: 'feedback', label: '💬 Feedback', icon: MessageSquare },
  { id: 'bugs', label: '🐞 Bug Reports', icon: Bug },
  { id: 'features', label: '💡 Feature Requests', icon: Lightbulb },
  { id: 'releases', label: '📦 Releases', icon: FileText },
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
  releases: 'Releases',
  health: 'System Status',
  system: 'System',
  changelog: 'Logs',
  logs: 'Logs',
  updates: 'Charts',
  charts: 'Charts',
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
        if (sections.find(s => s.id === section)) {
          setActiveSection(section);
        }
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
    if (isAuthenticated) {
      trackEvent('admin_navigate', { section: activeSection });
    }
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
    trackEvent('admin_navigate', { section });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="w-12 h-12 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

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
              <h2 className="text-xl font-bold text-white">
                {sectionLabels[activeSection] || 'Dashboard'}
              </h2>
              <p className="text-xs text-gray-500 mt-1">
                {new Date().toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
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
    case 'overview':
      return <OverviewSection />;
    case 'users':
      return <UserAnalyticsSection />;
    case 'feedback':
      return <FeedbackCenter />;
    case 'features':
      return <FeatureRequestsSection />;
    case 'bugs':
      return <BugReportsSection />;
    case 'downloads':
      return <DownloadAnalyticsSection />;
    case 'health':
      return <SystemHealthSection />;
    case 'changelog':
      return <ChangelogManager />;
    case 'updates':
      return <UpdateManagement />;
    case 'search':
      return <SearchSection />;
    case 'analytics':
      return <AnalyticsSection />;
    case 'visitors':
      return <VisitorsSection />;
    case 'releases':
      return <ReleasesSection />;
    case 'system':
      return <SystemStatusSection />;
    case 'logs':
      return <LogsSection />;
    case 'charts':
      return <ChartsSection />;
    default:
      return <OverviewSection />;
  }
}

function AnalyticsSection() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <Users size={16} className="text-blue-400" />
            </div>
            <p className="text-xs text-gray-500">Total Visitors</p>
          </div>
          <p className="text-2xl font-bold text-white">12.5K</p>
          <p className="text-xs text-emerald-400 mt-1">+12% from last month</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
              <BarChart3 size={16} className="text-purple-400" />
            </div>
            <p className="text-xs text-gray-500">Page Views</p>
          </div>
          <p className="text-2xl font-bold text-white">45.2K</p>
          <p className="text-xs text-emerald-400 mt-1">+8.5% from last month</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <Activity size={16} className="text-emerald-400" />
            </div>
            <p className="text-xs text-gray-500">Bounce Rate</p>
          </div>
          <p className="text-2xl font-bold text-white">32.4%</p>
          <p className="text-xs text-red-300 mt-1">-2.1% from last month</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
              <Shield size={16} className="text-cyan-400" />
            </div>
            <p className="text-xs text-gray-500">Avg Session</p>
          </div>
          <p className="text-2xl font-bold text-white">4m 32s</p>
          <p className="text-xs text-emerald-400 mt-1">+12s from last month</p>
        </div>
      </div>
    </div>
  );
}

function VisitorsSection() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <User size={14} />
            Visitor Countries
          </h3>
          <div className="space-y-3">
            {[
              { name: 'United States', percentage: 36.2, color: 'bg-blue-500' },
              { name: 'United Kingdom', percentage: 18.7, color: 'bg-purple-500' },
              { name: 'Germany', percentage: 15.1, color: 'bg-emerald-500' },
              { name: 'Canada', percentage: 9.8, color: 'bg-cyan-500' },
              { name: 'France', percentage: 7.8, color: 'bg-pink-500' },
            ].map((country) => (
              <div key={country.name} className="flex items-center justify-between">
                <span className="text-xs text-gray-400">{country.name}</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                    <div className={`h-full rounded-full ${country.color}`} style={{ width: `${country.percentage}%` }} />
                  </div>
                  <span className="text-xs text-gray-500 w-12 text-right">{country.percentage}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Activity size={14} />
            Device Types
          </h3>
          <div className="space-y-3">
            {[
              { name: 'Desktop', percentage: 68, color: 'bg-blue-500' },
              { name: 'Mobile', percentage: 24, color: 'bg-purple-500' },
              { name: 'Tablet', percentage: 8, color: 'bg-emerald-500' },
            ].map((device) => (
              <div key={device.name} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                <span className="text-sm text-gray-300">{device.name}</span>
                <span className="text-sm font-medium text-white">{device.percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ReleasesSection() {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-bold text-white">Recent Releases</h3>
      <div className="space-y-4">
        {[
          { version: 'v1.0.0', date: '2026-07-31', changes: 'Initial stable release with full admin dashboard' },
          { version: 'v0.9.5', date: '2026-07-28', changes: 'Performance improvements and bug fixes' },
          { version: 'v0.9.0', date: '2026-07-25', changes: 'Added analytics and visitor tracking' },
        ].map((release) => (
          <div key={release.version} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.08]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-bold text-blue-400">{release.version}</span>
              <span className="text-xs text-gray-500">{release.date}</span>
            </div>
            <p className="text-sm text-gray-400">{release.changes}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function SystemStatusSection() {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-bold text-white mb-4">System Status</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-3 h-3 rounded-full bg-emerald-400" />
            <span className="text-sm font-bold text-white">AI Services</span>
          </div>
          <p className="text-xs text-gray-500">All systems operational</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-3 h-3 rounded-full bg-emerald-400" />
            <span className="text-sm font-bold text-white">Database</span>
          </div>
          <p className="text-xs text-gray-500">Connection stable</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-3 h-3 rounded-full bg-emerald-400" />
            <span className="text-sm font-bold text-white">Storage</span>
          </div>
          <p className="text-xs text-gray-500">85% capacity used</p>
        </div>
      </div>
    </div>
  );
}

function LogsSection() {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-bold text-white mb-4">Recent Activity</h3>
      <div className="space-y-3">
        {[
          { time: '2 minutes ago', action: 'New download from Windows 11' },
          { time: '15 minutes ago', action: 'Bug report submitted by user' },
          { time: '1 hour ago', action: 'Feature request received' },
          { time: '2 hours ago', action: 'Admin login successful' },
        ].map((log, index) => (
          <div key={index} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <div className="w-2 h-2 rounded-full bg-blue-400" />
            <div className="flex-1">
              <p className="text-sm text-gray-300">{log.action}</p>
              <p className="text-xs text-gray-500">{log.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChartsSection() {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-bold text-white mb-4">Analytics Charts</h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h4 className="text-sm font-semibold text-gray-300 mb-4">Traffic Over Time</h4>
          <div className="h-48 flex items-end justify-between gap-2">
            {[
              { day: 'Mon', value: 45 },
              { day: 'Tue', value: 52 },
              { day: 'Wed', value: 38 },
              { day: 'Thu', value: 61 },
              { day: 'Fri', value: 72 },
              { day: 'Sat', value: 48 },
              { day: 'Sun', value: 55 },
            ].map((bar) => (
              <div key={bar.day} className="flex-1 flex flex-col items-center">
                <div className="w-8 h-32 rounded-t bg-gradient-to-t from-blue-500 to-purple-500" style={{ height: `${bar.value}%` }} />
                <span className="text-xs text-gray-500 mt-2">{bar.day}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h4 className="text-sm font-semibold text-gray-300 mb-4">User Growth</h4>
          <div className="h-48 flex items-center justify-center">
            <div className="w-64 h-64 rounded-full bg-gradient-to-r from-blue-500/20 to-purple-500/20 flex items-center justify-center">
              <div className="text-center">
                <p className="text-3xl font-bold text-white">24.5%</p>
                <p className="text-xs text-gray-500">Growth Rate</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}