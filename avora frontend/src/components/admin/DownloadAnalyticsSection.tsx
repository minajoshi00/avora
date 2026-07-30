/**
 * Admin Dashboard - Download Analytics Section
 */

'use client';

import { motion } from 'framer-motion';
import { Download, TrendingUp, Calendar } from 'lucide-react';

const downloadData = [
  { date: '2026-07-24', count: 45 },
  { date: '2026-07-25', count: 67 },
  { date: '2026-07-26', count: 52 },
  { date: '2026-07-27', count: 89 },
  { date: '2026-07-28', count: 120 },
  { date: '2026-07-29', count: 98 },
  { date: '2026-07-30', count: 145 },
];

const platformStats = [
  { name: 'Windows', downloads: 2450, percentage: 76.6 },
  { name: 'macOS', downloads: 520, percentage: 16.3 },
  { name: 'Linux', downloads: 230, percentage: 7.1 },
];

export function DownloadAnalyticsSection() {
  const totalDownloads = platformStats.reduce((sum, p) => sum + p.downloads, 0);

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Download size={14} className="text-blue-400" />
            <p className="text-xs text-gray-500">Today</p>
          </div>
          <p className="text-xl font-bold text-white">145</p>
          <p className="text-xs text-emerald-400 mt-1">+47% vs yesterday</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={14} className="text-purple-400" />
            <p className="text-xs text-gray-500">This Week</p>
          </div>
          <p className="text-xl font-bold text-white">716</p>
          <p className="text-xs text-emerald-400 mt-1">+23% vs last week</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Calendar size={14} className="text-emerald-400" />
            <p className="text-xs text-gray-500">This Month</p>
          </div>
          <p className="text-xl font-bold text-white">3,200</p>
          <p className="text-xs text-emerald-400 mt-1">+15% vs last month</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Download size={14} className="text-yellow-400" />
            <p className="text-xs text-gray-500">Total</p>
          </div>
          <p className="text-xl font-bold text-white">{totalDownloads.toLocaleString()}</p>
          <p className="text-xs text-gray-500 mt-1">All time</p>
        </div>
      </div>

      {/* Download Chart */}
      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Downloads Over Time</h3>
        <div className="space-y-2">
          {downloadData.map((day, index) => (
            <div key={day.date} className="flex items-center gap-3">
              <span className="text-xs text-gray-500 w-16">{day.date.split('-')[2]}</span>
              <div className="flex-1 h-8 rounded-lg bg-white/[0.03] relative overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(day.count / 200) * 100}%` }}
                  transition={{ duration: 0.8, delay: index * 0.1 }}
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg"
                />
              </div>
              <span className="text-xs text-gray-400 w-12 text-right">{day.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Platform Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">By Platform</h3>
          <div className="space-y-3">
            {platformStats.map((platform) => (
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
                    className="h-full rounded-full bg-blue-500"
                  />
                </div>
                <p className="text-xs text-gray-500">{platform.downloads.toLocaleString()} downloads</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Conversion Rate</h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">Visitor to Download</span>
                <span className="text-xs text-gray-400">24.5%</span>
              </div>
              <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '24.5%' }}
                  transition={{ duration: 1 }}
                  className="h-full rounded-full bg-emerald-500"
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">Download to Install</span>
                <span className="text-xs text-gray-400">78.3%</span>
              </div>
              <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '78.3%' }}
                  transition={{ duration: 1 }}
                  className="h-full rounded-full bg-purple-500"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}