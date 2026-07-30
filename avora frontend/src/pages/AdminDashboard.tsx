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
  | 'search';

const sections: { id: Section; label: string; icon: any }[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'users', label: 'User Analytics', icon: Users },
  { id: 'feedback', label: 'Feedback', icon: MessageSquare },
  { id: 'features', label: 'Features', icon: Lightbulb },
  { id: 'bugs', label: 'Bug Reports', icon: Bug },
  { id: 'downloads', label: 'Downloads', icon: Download },
  { id: 'health', label: 'System Health', icon: Activity },
  { id: 'changelog', label: 'Changelog', icon: FileText },
  { id: 'updates', label: 'Updates', icon: RefreshCw },
  { id: 'search', label: 'Search', icon: Search },
];

export default function AdminDashboard() {
  const [activeSection, setActiveSection] = useState<Section>('overview');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check authentication
    if (hasValidSession()) {
      setIsAuthenticated(true);
      trackEvent('admin_dashboard_view', { section: activeSection });
    } else {
      window.location.href = '/admin';
    }
  }, []);

  const handleLogout = () => {
    trackEvent('admin_logout');
    logout();
    window.location.href = '/admin';
  };

  const navigateTo = (section: Section) => {
    setActiveSection(section);
    trackEvent('admin_navigate', { section });
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/[0.08] bg-white/[0.02] flex flex-col">
        {/* Logo */}
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

        {/* Navigation */}
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

        {/* Footer */}
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

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/[0.08] px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">
                {sections.find(s => s.id === activeSection)?.label}
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

        {/* Content */}
        <div className="p-8">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {activeSection === 'overview' && <OverviewSection />}
            {activeSection === 'users' && <UserAnalyticsSection />}
            {activeSection === 'feedback' && <FeedbackCenter />}
            {activeSection === 'features' && <FeatureRequestsSection />}
            {activeSection === 'bugs' && <BugReportsSection />}
            {activeSection === 'downloads' && <DownloadAnalyticsSection />}
            {activeSection === 'health' && <SystemHealthSection />}
            {activeSection === 'changelog' && <ChangelogManager />}
            {activeSection === 'updates' && <UpdateManagement />}
            {activeSection === 'search' && <SearchSection />}
          </motion.div>
        </div>
      </main>
    </div>
  );
}