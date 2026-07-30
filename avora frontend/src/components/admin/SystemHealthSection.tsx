/**
 * Admin Dashboard - System Health Section
 */

'use client';

import { motion } from 'framer-motion';
import { 
  Cpu, 
  HardDrive, 
  MemoryStick, 
  Database, 
  Activity,
  CheckCircle,
  AlertCircle,
  XCircle,
} from 'lucide-react';

const healthMetrics = [
  {
    name: 'CPU Usage',
    value: 45,
    max: 100,
    unit: '%',
    icon: Cpu,
    color: 'blue',
    status: 'healthy',
  },
  {
    name: 'Memory Usage',
    value: 6.2,
    max: 16,
    unit: 'GB',
    icon: MemoryStick,
    color: 'purple',
    status: 'healthy',
  },
  {
    name: 'Disk Usage',
    value: 128,
    max: 500,
    unit: 'GB',
    icon: HardDrive,
    color: 'emerald',
    status: 'healthy',
  },
];

const services = [
  { name: 'Analytics Service', status: 'running', uptime: '99.9%' },
  { name: 'Update Checker', status: 'running', uptime: '99.8%' },
  { name: 'Feedback Collector', status: 'running', uptime: '100%' },
  { name: 'Changelog Manager', status: 'running', uptime: '100%' },
];

const databases = [
  { name: 'Local Storage', status: 'healthy', size: '2.3 MB' },
  { name: 'Analytics Cache', status: 'healthy', size: '1.1 MB' },
  { name: 'User Sessions', status: 'healthy', size: '0.5 MB' },
];

export function SystemHealthSection() {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'running':
        return <CheckCircle size={14} className="text-emerald-400" />;
      case 'warning':
        return <AlertCircle size={14} className="text-yellow-400" />;
      case 'error':
        return <XCircle size={14} className="text-red-400" />;
      default:
        return <Activity size={14} className="text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'running':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'warning':
        return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      case 'error':
        return 'text-red-400 bg-red-500/10 border-red-500/20';
      default:
        return 'text-gray-400 bg-gray-500/10 border-gray-500/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* System Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {healthMetrics.map((metric, index) => {
          const Icon = metric.icon;
          const percentage = (metric.value / metric.max) * 100;
          
          return (
            <motion.div
              key={metric.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                  <Icon size={20} className="text-blue-400" />
                </div>
                <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border ${getStatusColor(metric.status)}`}>
                  {getStatusIcon(metric.status)}
                  <span className="text-xs font-medium capitalize">{metric.status}</span>
                </div>
              </div>
              
              <div className="mb-3">
                <p className="text-2xl font-bold text-white">
                  {metric.value}{metric.unit}
                </p>
                <p className="text-xs text-gray-500">{metric.name}</p>
              </div>
              
              <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ duration: 1, delay: 0.2 }}
                  className={`h-full rounded-full bg-${metric.color}-500`}
                />
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Services Status */}
      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Activity size={14} />
          Background Services
        </h3>
        <div className="space-y-3">
          {services.map((service, index) => (
            <motion.div
              key={service.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]"
            >
              <div className="flex items-center gap-3">
                {getStatusIcon(service.status)}
                <div>
                  <p className="text-sm font-medium text-white">{service.name}</p>
                  <p className="text-xs text-gray-500">Uptime: {service.uptime}</p>
                </div>
              </div>
              <span className={`text-xs font-medium capitalize px-3 py-1 rounded-lg border ${getStatusColor(service.status)}`}>
                {service.status}
              </span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Database Status */}
      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Database size={14} />
          Database & Storage
        </h3>
        <div className="space-y-3">
          {databases.map((db, index) => (
            <motion.div
              key={db.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]"
            >
              <div className="flex items-center gap-3">
                <Database size={14} className="text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-white">{db.name}</p>
                  <p className="text-xs text-gray-500">Size: {db.size}</p>
                </div>
              </div>
              <span className={`text-xs font-medium capitalize px-3 py-1 rounded-lg border ${getStatusColor(db.status)}`}>
                {db.status}
              </span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* AI Status */}
      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Activity size={14} />
          AI Engine Status
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <p className="text-xs text-gray-500 mb-1">Primary Provider</p>
            <p className="text-sm font-medium text-white">Google Gemini</p>
            <p className="text-xs text-emerald-400 mt-1">Operational</p>
          </div>
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <p className="text-xs text-gray-500 mb-1">Fallback Provider</p>
            <p className="text-sm font-medium text-white">Groq</p>
            <p className="text-xs text-emerald-400 mt-1">Operational</p>
          </div>
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <p className="text-xs text-gray-500 mb-1">Response Time</p>
            <p className="text-sm font-medium text-white">1.2s avg</p>
            <p className="text-xs text-emerald-400 mt-1">Excellent</p>
          </div>
        </div>
      </div>
    </div>
  );
}