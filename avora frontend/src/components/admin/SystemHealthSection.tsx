/**
 * Admin Dashboard - System Health Section (REAL data)
 * Fetches /api/health and never shows fake CPU/RAM as real.
 */
'use client';

import { useEffect, useState } from 'react';
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

type Health = {
  status: string;
  uptimeSec: number;
  uptimeHuman: string;
  memory: { rssMB: number; heapUsedMB: number; heapTotalMB: number; systemTotalMB: number; systemFreeMB: number };
  cpu: { count: number; model: string; loadAvg: number[] };
  platform: string;
  node: string;
  analytics: { bytes: number | null; events: number | null; path?: string; note?: string };
  ai: { geminiConfigured: boolean; groqConfigured: boolean; geminiModel: string; groqModel: string };
  maintenanceMode: boolean;
};

export function SystemHealthSection() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/api/health', { cache: 'no-store' });
        if (!res.ok) throw new Error(`Health ${res.status}`);
        const data = (await res.json()) as Health;
        if (!cancelled) setHealth(data);
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'running':
      case 'ok':
        return <CheckCircle size={14} className="text-emerald-400" />;
      case 'warning':
        return <AlertCircle size={14} className="text-yellow-400" />;
      case 'error':
        return <XCircle size={14} className="text-red-400" />;
      default:
        return <Activity size={14} className="text-gray-400" />;
    }
  };
  const getStatusColor = (s: string) => {
    switch (s) {
      case 'healthy': case 'running': case 'ok': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'warning': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      case 'error': return 'text-red-400 bg-red-500/10 border-red-500/20';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/20';
    }
  };

  if (loading) return <div className="flex items-center gap-3 py-16 justify-center text-gray-500 text-sm"><span className="w-4 h-4 border-2 border-blue-400/30 border-t-blue-400 rounded-full animate-spin" /> Loading real system health…</div>;
  if (error) return <div className="rounded-2xl border border-yellow-500/20 bg-yellow-500/5 p-6 text-center"><AlertCircle className="mx-auto mb-2 text-yellow-400" size={24} /><p className="text-sm text-white font-medium">Health endpoint unavailable</p><p className="text-xs text-gray-400 mt-1">{error}</p><p className="text-xs text-gray-500 mt-2">Metrics are shown as unavailable rather than fake values.</p></div>;
  if (!health) return null;

  const metrics = [
    { name: 'Process RSS', value: health.memory.rssMB, max: Math.max(health.memory.rssMB * 1.6, 512), unit: 'MB', icon: Cpu, color: 'blue', status: 'ok' as const },
    { name: 'Heap Used', value: health.memory.heapUsedMB, max: health.memory.heapTotalMB || 200, unit: 'MB', icon: MemoryStick, color: 'purple', status: 'ok' as const },
    { name: 'System Free', value: health.memory.systemFreeMB, max: health.memory.systemTotalMB || 16384, unit: 'MB', icon: HardDrive, color: 'emerald', status: 'ok' as const },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {metrics.map((metric, index) => {
          const Icon = metric.icon;
          const percentage = Math.min(100, (metric.value / metric.max) * 100);
          return (
            <motion.div key={metric.name} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20"><Icon size={20} className="text-blue-400" /></div>
                <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border ${getStatusColor(metric.status)}`}>{getStatusIcon(metric.status)}<span className="text-xs font-medium capitalize">{metric.status}</span></div>
              </div>
              <div className="mb-3">
                <p className="text-2xl font-bold text-white">{metric.value}{metric.unit}</p>
                <p className="text-xs text-gray-500">{metric.name} — real</p>
              </div>
              <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                <motion.div initial={{ width: 0 }} animate={{ width: `${percentage}%` }} transition={{ duration: 1, delay: 0.2 }} className={`h-full rounded-full ${metric.color === 'purple' ? 'bg-purple-500' : metric.color === 'emerald' ? 'bg-emerald-500' : 'bg-blue-500'}`} />
              </div>
              <p className="text-[10px] text-gray-600 mt-2">{metric.value} / {Math.round(metric.max)} {metric.unit}</p>
            </motion.div>
          );
        })}
      </div>

      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2"><Activity size={14} /> Host & Runtime (real)</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]"><p className="text-gray-500">Platform</p><p className="text-white font-medium">{health.platform} — Node {health.node}</p></div>
          <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]"><p className="text-gray-500">Uptime</p><p className="text-white font-medium">{health.uptimeHuman} ({health.uptimeSec}s)</p></div>
          <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]"><p className="text-gray-500">CPU</p><p className="text-white font-medium">{health.cpu.count} cores</p><p className="text-gray-600 text-[10px] truncate" title={health.cpu.model}>{health.cpu.model}</p></div>
        </div>
        <p className="text-[10px] text-gray-600 mt-3">System memory: {health.memory.systemTotalMB} MB total, {health.memory.systemFreeMB} MB free — live from OS.</p>
      </div>

      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2"><Database size={14} /> Analytics Persistence (real)</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <div className="flex items-center gap-3"><Database size={14} className="text-gray-400" /><div><p className="text-sm font-medium text-white">analytics_data.json</p><p className="text-xs text-gray-500">{health.analytics.bytes !== null ? `${(health.analytics.bytes/1024).toFixed(1)} KB · ${health.analytics.events} events` : health.analytics.note || 'Unavailable'}</p></div></div>
            <span className={`text-xs font-medium px-3 py-1 rounded-lg border ${health.analytics.bytes !== null ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20'}`}>{health.analytics.bytes !== null ? 'healthy' : 'unavailable'}</span>
          </div>
          <div className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <div className="flex items-center gap-3"><Activity size={14} className="text-gray-400" /><div><p className="text-sm font-medium text-white">Maintenance Mode</p><p className="text-xs text-gray-500">{health.maintenanceMode ? 'Enabled (public sees maintenance screen)' : 'Disabled (site live)'}</p></div></div>
            <span className={`text-xs px-3 py-1 rounded-lg border ${health.maintenanceMode ? 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'}`}>{health.maintenanceMode ? 'on' : 'off'}</span>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2"><Activity size={14} /> AI Engine Status (real config)</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]"><p className="text-xs text-gray-500 mb-1">Primary — Gemini</p><p className="text-sm font-medium text-white">{health.ai.geminiModel}</p><p className={`text-xs mt-1 ${health.ai.geminiConfigured ? 'text-emerald-400' : 'text-red-400'}`}>{health.ai.geminiConfigured ? 'Configured (key present, not exposed)' : 'Not configured — set GEMINI_API_KEY'}</p></div>
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]"><p className="text-xs text-gray-500 mb-1">Fallback — Groq</p><p className="text-sm font-medium text-white">{health.ai.groqModel}</p><p className={`text-xs mt-1 ${health.ai.groqConfigured ? 'text-emerald-400' : 'text-red-400'}`}>{health.ai.groqConfigured ? 'Configured (key present, not exposed)' : 'Not configured — set GROQ_API_KEY'}</p></div>
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]"><p className="text-xs text-gray-500 mb-1">Pipeline</p><p className="text-sm font-medium text-white">Gemini → Groq</p><p className="text-xs text-gray-500 mt-1">15s AbortController timeout · no key in logs/client</p></div>
        </div>
        <p className="text-[10px] text-gray-600 mt-3">Keys are verified server-side only via <code className="bg-white/5 px-1 rounded">process.env.GEMINI_API_KEY/GROQ_API_KEY</code> + <code>dotenv</code>. Never sent to frontend. See <code>/api/ai/gemini/health</code> &amp; <code>/api/health</code>.</p>
      </div>
    </div>
  );
}
