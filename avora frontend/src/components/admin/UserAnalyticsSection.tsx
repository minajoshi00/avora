/**
 * Admin Dashboard - User Analytics Section
 * 
 * Displays detailed user analytics and metrics.
 */

'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Users,
  TrendingUp,
  Clock,
  Globe,
  Monitor,
  Smartphone,
  Tablet,
  Activity,
} from 'lucide-react';

const timeRanges = ['Today', '7 Days', '30 Days', '90 Days'];

const dailyData = [
  { date: '2026-07-24', users: 245, sessions: 389 },
  { date: '2026-07-25', users: 312, sessions: 456 },
  { date: '2026-07-26', users: 289, sessions: 423 },
  { date: '2026-07-27', users: 367, sessions: 512 },
  { date: '2026-07-28', users: 445, sessions: 623 },
  { date: '2026-07-29', users: 398, sessions: 567 },
  { date: '2026-07-30', users: 512, sessions: 712 },
];

const countries = [
  { name: 'United States', users: 4520, percentage: 36.2 },
  { name: 'United Kingdom', users: 2340, percentage: 18.7 },
  { name: 'Germany', users: 1890, percentage: 15.1 },
  { name: 'Canada', users: 1230, percentage: 9.8 },
  { name: 'France', users: 980, percentage: 7.8 },
  { name: 'Others', users: 1510, percentage: 12.4 },
];

const devices = [
  { name: 'Desktop', percentage: 68, icon: Monitor },
  { name: 'Mobile', percentage: 24, icon: Smartphone },
  { name: 'Tablet', percentage: 8, icon: Tablet },
];

const trafficSources = [
  { name: 'Direct', percentage: 45, color: 'bg-blue-500' },
  { name: 'Google', percentage: 30, color: 'bg-purple-500' },
  { name: 'Social Media', percentage: 15, color: 'bg-emerald-500' },
  { name: 'Referral', percentage: 10, color: 'bg-yellow-500' },
];

export function UserAnalyticsSection() {
  const [selectedRange, setSelectedRange] = useState('7 Days');

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex items-center gap-2">
        {timeRanges.map((range) => (
          <button
            key={range}
            onClick={() => setSelectedRange(range)}
            className={`px-4 py-2 rounded-lg text-sm transition-all ${
              selectedRange === range
                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] border border-transparent'
            }`}
          >
            {range}
          </button>
        ))}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <Users size={16} className="text-blue-400" />
            </div>
            <p className="text-xs text-gray-500">Daily Users</p>
          </div>
          <p className="text-2xl font-bold text-white">512</p>
          <p className="text-xs text-emerald-400 mt-1">+28.6% vs yesterday</p>
        </div>

        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
              <TrendingUp size={16} className="text-purple-400" />
            </div>
            <p className="text-xs text-gray-500">Weekly Users</p>
          </div>
          <p className="text-2xl font-bold text-white">2,847</p>
          <p className="text-xs text-emerald-400 mt-1">+12.3% vs last week</p>
        </div>

        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <Activity size={16} className="text-emerald-400" />
            </div>
            <p className="text-xs text-gray-500">Monthly Users</p>
          </div>
          <p className="text-2xl font-bold text-white">11.2K</p>
          <p className="text-xs text-emerald-400 mt-1">+8.7% vs last month</p>
        </div>

        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
              <Clock size={16} className="text-yellow-400" />
            </div>
            <p className="text-xs text-gray-500">Live Users</p>
          </div>
          <p className="text-2xl font-bold text-white">127</p>
          <p className="text-xs text-gray-500 mt-1">Currently online</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Activity Chart */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">User Activity</h3>
          <div className="space-y-2">
            {dailyData.map((day, index) => (
              <div key={day.date} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-16">{day.date.split('-')[2]}</span>
                <div className="flex-1 h-8 rounded-lg bg-white/[0.03] relative overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(day.users / 600) * 100}%` }}
                    transition={{ duration: 0.8, delay: index * 0.1 }}
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg"
                  />
                </div>
                <span className="text-xs text-gray-400 w-12 text-right">{day.users}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Traffic Sources */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Globe size={14} />
            Traffic Sources
          </h3>
          <div className="space-y-3">
            {trafficSources.map((source) => (
              <div key={source.name} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">{source.name}</span>
                  <span className="text-gray-500">{source.percentage}%</span>
                </div>
                <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${source.percentage}%` }}
                    transition={{ duration: 1, delay: 0.2 }}
                    className={`h-full rounded-full ${source.color}`}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Countries and Devices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Countries */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Globe size={14} />
            Top Countries
          </h3>
          <div className="space-y-2">
            {countries.map((country) => (
              <div key={country.name} className="flex items-center justify-between p-2 rounded-lg hover:bg-white/[0.02] transition-colors">
                <span className="text-xs text-gray-400">{country.name}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${country.percentage}%` }}
                      transition={{ duration: 0.8 }}
                      className="h-full bg-blue-500 rounded-full"
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-16 text-right">{country.users.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Devices */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Monitor size={14} />
            Device Types
          </h3>
          <div className="space-y-3">
            {devices.map((device) => {
              const Icon = device.icon;
              return (
                <div key={device.name} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                  <div className="flex items-center gap-3">
                    <Icon size={16} className="text-gray-400" />
                    <span className="text-sm text-gray-300">{device.name}</span>
                  </div>
                  <span className="text-sm font-medium text-white">{device.percentage}%</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}