/**
 * Admin Dashboard - Overview Section
 * 
 * Displays high-level metrics and statistics.
 */

'use client';

import { motion } from 'framer-motion';
import { 
  Users,
  Download,
  MessageSquare,
  Bug,
  Activity,
  Globe,
  Monitor,
  Clock,
  TrendingUp,
} from 'lucide-react';
import { getBugReports } from '../../lib/storage';

const stats = [
  { label: 'Total Visitors', value: '12.5K', change: '+12%', icon: Users, color: 'blue' },
  { label: 'Unique Visitors', value: '8.3K', change: '+8%', icon: Globe, color: 'purple' },
  { label: 'Downloads', value: '3.2K', change: '+15%', icon: Download, color: 'emerald' },
  { label: 'Active Users', value: '1.2K', change: '+5%', icon: Activity, color: 'yellow' },
  { label: 'Feedback', value: '48', change: '+3', icon: MessageSquare, color: 'pink' },
  { label: 'Bug Reports', value: '12', change: '-2', icon: Bug, color: 'red' },
];

const platforms = [
  { name: 'Windows', percentage: 65, color: 'bg-blue-500' },
  { name: 'macOS', percentage: 25, color: 'bg-purple-500' },
  { name: 'Linux', percentage: 10, color: 'bg-emerald-500' },
];

const browsers = [
  { name: 'Chrome', percentage: 70 },
  { name: 'Firefox', percentage: 15 },
  { name: 'Safari', percentage: 10 },
  { name: 'Edge', percentage: 5 },
];

export function OverviewSection() {
  const bugReports = getBugReports();

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
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
                <span className="text-xs text-emerald-400 font-medium">{stat.change}</span>
              </div>
              <div>
                <p className="text-2xl font-bold text-white mb-1">{stat.value}</p>
                <p className="text-xs text-gray-500">{stat.label}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Operating Systems */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Monitor size={14} />
            Operating Systems
          </h3>
          <div className="space-y-3">
            {platforms.map((platform) => (
              <div key={platform.name} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">{platform.name}</span>
                  <span className="text-gray-500">{platform.percentage}%</span>
                </div>
                <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${platform.percentage}%` }}
                    transition={{ duration: 1, delay: 0.2 }}
                    className={`h-full rounded-full ${platform.color}`}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Browsers */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Globe size={14} />
            Browsers
          </h3>
          <div className="space-y-3">
            {browsers.map((browser) => (
              <div key={browser.name} className="flex items-center justify-between">
                <span className="text-xs text-gray-400">{browser.name}</span>
                <span className="text-xs text-gray-500">{browser.percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Clock size={14} />
          Latest Activity
        </h3>
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <div className="w-2 h-2 rounded-full bg-blue-400" />
            <div className="flex-1">
              <p className="text-xs text-white">New download from Windows</p>
              <p className="text-[10px] text-gray-500">2 minutes ago</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
            <div className="flex-1">
              <p className="text-xs text-white">Bug report submitted</p>
              <p className="text-[10px] text-gray-500">15 minutes ago</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <div className="w-2 h-2 rounded-full bg-purple-400" />
            <div className="flex-1">
              <p className="text-xs text-white">Feature request received</p>
              <p className="text-[10px] text-gray-500">1 hour ago</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp size={16} className="text-blue-400" />
            <p className="text-xs text-gray-500">Conversion Rate</p>
          </div>
          <p className="text-2xl font-bold text-white">24.5%</p>
          <p className="text-xs text-emerald-400 mt-1">+3.2% from last week</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <Activity size={16} className="text-purple-400" />
            <p className="text-xs text-gray-500">Avg Session Time</p>
          </div>
          <p className="text-2xl font-bold text-white">4m 32s</p>
          <p className="text-xs text-emerald-400 mt-1">+12s from last week</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <Bug size={16} className="text-red-400" />
            <p className="text-xs text-gray-500">Open Bugs</p>
          </div>
          <p className="text-2xl font-bold text-white">{bugReports.length}</p>
          <p className="text-xs text-gray-500 mt-1">Requires attention</p>
        </div>
      </div>
    </div>
  );
}