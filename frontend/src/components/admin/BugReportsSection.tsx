/**
 * Admin Dashboard - Bug Reports Section
 */

'use client';

import { motion } from 'framer-motion';
import { Bug, Calendar, AlertCircle, CheckCircle, XCircle, Clock, Search } from 'lucide-react';
import { getBugReports } from '../../lib/storage';

const severityConfig = {
  low: { color: 'text-blue-400 bg-blue-500/10 border-blue-500/20', label: 'Low' },
  medium: { color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20', label: 'Medium' },
  high: { color: 'text-orange-400 bg-orange-500/10 border-orange-500/20', label: 'High' },
  critical: { color: 'text-red-400 bg-red-500/10 border-red-500/20', label: 'Critical' },
};

const statusConfig = {
  investigating: { icon: Search, color: 'text-blue-400', label: 'Investigating' },
  resolved: { icon: CheckCircle, color: 'text-emerald-400', label: 'Resolved' },
  ignored: { icon: XCircle, color: 'text-gray-400', label: 'Ignored' },
};

export function BugReportsSection() {
  const reports = getBugReports();

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Bug size={14} className="text-red-400" />
            <p className="text-xs text-gray-500">Total Bugs</p>
          </div>
          <p className="text-xl font-bold text-white">{reports.length}</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <AlertCircle size={14} className="text-orange-400" />
            <p className="text-xs text-gray-500">Critical</p>
          </div>
          <p className="text-xl font-bold text-white">0</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Clock size={14} className="text-yellow-400" />
            <p className="text-xs text-gray-500">Investigating</p>
          </div>
          <p className="text-xl font-bold text-white">0</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle size={14} className="text-emerald-400" />
            <p className="text-xs text-gray-500">Resolved</p>
          </div>
          <p className="text-xl font-bold text-white">0</p>
        </div>
      </div>

      {/* Reports List */}
      <div className="space-y-3">
        {reports.length === 0 ? (
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-12 text-center">
            <Bug size={32} className="text-gray-600 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No bug reports yet</p>
          </div>
        ) : (
          reports.map((report: any, index: number) => {
            const status = statusConfig.investigating;
            const StatusIcon = status.icon;
            const severity = severityConfig.medium;
            
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg border ${severity.color}`}>
                      <Bug size={14} />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-white">Bug Report</h3>
                      <p className="text-xs text-gray-500">v{report.app_version || 'unknown'}</p>
                    </div>
                  </div>
                  <div className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border ${severity.color}`}>
                    <span className="text-xs font-medium">{severity.label}</span>
                  </div>
                </div>
                
                {report.error_message && (
                  <div className="mb-3 p-3 rounded-xl bg-red-500/5 border border-red-500/10">
                    <p className="text-xs text-red-300 font-mono">{report.error_message}</p>
                  </div>
                )}
                
                {report.comments && (
                  <p className="text-sm text-gray-300 mb-4">{report.comments}</p>
                )}
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Calendar size={12} />
                    {report.timestamp ? new Date(report.timestamp).toLocaleDateString() : 'Unknown date'}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <div className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border ${status.color.replace('text-', 'text-').replace('/10', '/10')}`}>
                      <StatusIcon size={12} />
                      <span className="text-xs">{status.label}</span>
                    </div>
                    <button className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors">Resolve</button>
                    <button className="text-xs text-gray-400 hover:text-gray-300 transition-colors">Ignore</button>
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}