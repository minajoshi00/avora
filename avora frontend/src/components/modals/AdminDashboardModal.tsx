'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { OverviewSection } from '../admin/OverviewSection';
import { UserAnalyticsSection } from '../admin/UserAnalyticsSection';
import { FeedbackCenter } from '../admin/FeedbackCenter';
import { FeatureRequestsSection } from '../admin/FeatureRequestsSection';
import { BugReportsSection } from '../admin/BugReportsSection';
import { DownloadAnalyticsSection } from '../admin/DownloadAnalyticsSection';
import { SystemHealthSection } from '../admin/SystemHealthSection';
import { 
  X,
  LayoutDashboard,
  Users,
  MessageSquare,
  Lightbulb,
  Bug,
  Download,
  Activity,
  LogOut,
} from 'lucide-react';

type Section = 'overview' | 'users' | 'feedback' | 'features' | 'bugs' | 'downloads' | 'health';

const sections: { id: Section; label: string; icon: any }[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'users', label: 'Analytics', icon: Users },
  { id: 'feedback', label: 'Feedback', icon: MessageSquare },
  { id: 'features', label: 'Features', icon: Lightbulb },
  { id: 'bugs', label: 'Bugs', icon: Bug },
  { id: 'downloads', label: 'Downloads', icon: Download },
  { id: 'health', label: 'System', icon: Activity },
];

interface AdminDashboardModalProps {
  onClose: () => void;
  onLogout: () => void;
}

export function AdminDashboardModal({ onClose, onLogout }: AdminDashboardModalProps) {
  const [activeSection, setActiveSection] = useState<Section>('overview');

  const handleLogout = () => {
    onLogout();
  };

  const handleEsc = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  };

  useState(() => {
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[400] bg-[#0a0a0f] overflow-hidden"
    >
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-white/[0.08] bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/[0.08] flex items-center justify-center text-sm">
              ⚙️
            </div>
            <div>
              <h1 className="text-sm font-bold text-white">Developer Console</h1>
              <p className="text-[10px] text-gray-500">AVORA Admin</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/[0.08] text-xs text-red-400 hover:bg-red-500/10 transition-all"
            >
              <LogOut size={12} />
              Logout
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg border border-white/[0.08] text-gray-400 hover:text-white hover:bg-white/[0.04] transition-all"
            >
              <X size={16} />
            </button>
          </div>
        </header>

        {/* Body */}
        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar */}
          <aside className="w-48 border-r border-white/[0.08] bg-white/[0.02] overflow-y-auto">
            <nav className="p-3 space-y-1">
              {sections.map((section) => {
                const Icon = section.icon;
                const isActive = activeSection === section.id;
                
                return (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-all ${
                      isActive
                        ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] border border-transparent'
                    }`}
                  >
                    <Icon size={14} />
                    <span>{section.label}</span>
                  </button>
                );
              })}
            </nav>
          </aside>

          {/* Content */}
          <main className="flex-1 overflow-y-auto">
            <div className="p-6">
              <div className="max-w-5xl mx-auto">
                {activeSection === 'overview' && <OverviewSection />}
                {activeSection === 'users' && <UserAnalyticsSection />}
                {activeSection === 'feedback' && <FeedbackCenter />}
                {activeSection === 'features' && <FeatureRequestsSection />}
                {activeSection === 'bugs' && <BugReportsSection />}
                {activeSection === 'downloads' && <DownloadAnalyticsSection />}
                {activeSection === 'health' && <SystemHealthSection />}
              </div>
            </div>
          </main>
        </div>
      </div>
    </motion.div>
  );
}