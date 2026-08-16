/**
 * Admin Dashboard - Feature Requests Section
 */

'use client';

import { motion } from 'framer-motion';
import { Lightbulb, Calendar, CheckCircle, Clock, XCircle, PlayCircle } from 'lucide-react';
import { getFeatureRequests } from '../../lib/storage';

const statusConfig = {
  pending: { icon: Clock, color: 'text-gray-400 bg-gray-500/10 border-gray-500/20', label: 'Pending' },
  planned: { icon: Lightbulb, color: 'text-blue-400 bg-blue-500/10 border-blue-500/20', label: 'Planned' },
  in_progress: { icon: PlayCircle, color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20', label: 'In Progress' },
  completed: { icon: CheckCircle, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', label: 'Completed' },
  rejected: { icon: XCircle, color: 'text-red-400 bg-red-500/10 border-red-500/20', label: 'Rejected' },
};

export function FeatureRequestsSection() {
  const requests = getFeatureRequests();

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Lightbulb size={14} className="text-blue-400" />
            <p className="text-xs text-gray-500">Total Requests</p>
          </div>
          <p className="text-xl font-bold text-white">{requests.length}</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Clock size={14} className="text-yellow-400" />
            <p className="text-xs text-gray-500">Pending</p>
          </div>
          <p className="text-xl font-bold text-white">{requests.length}</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <PlayCircle size={14} className="text-purple-400" />
            <p className="text-xs text-gray-500">In Progress</p>
          </div>
          <p className="text-xl font-bold text-white">0</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle size={14} className="text-emerald-400" />
            <p className="text-xs text-gray-500">Completed</p>
          </div>
          <p className="text-xl font-bold text-white">0</p>
        </div>
      </div>

      {/* Requests List */}
      <div className="space-y-3">
        {requests.length === 0 ? (
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-12 text-center">
            <Lightbulb size={32} className="text-gray-600 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No feature requests yet</p>
          </div>
        ) : (
          requests.map((request: any, index: number) => {
            const status = statusConfig.pending;
            const StatusIcon = status.icon;
            
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-white mb-1">{request.title || 'Untitled Request'}</h3>
                    <p className="text-xs text-gray-500">v{request.app_version || 'unknown'}</p>
                  </div>
                  <div className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border ${status.color}`}>
                    <StatusIcon size={12} />
                    <span className="text-xs font-medium">{status.label}</span>
                  </div>
                </div>
                
                {request.description && (
                  <p className="text-sm text-gray-300 mb-4">{request.description}</p>
                )}
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Calendar size={12} />
                    {request.date || request.timestamp ? new Date(request.date || request.timestamp).toLocaleDateString() : 'Unknown date'}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button className="text-xs text-blue-400 hover:text-blue-300 transition-colors">Mark Planned</button>
                    <button className="text-xs text-yellow-400 hover:text-yellow-300 transition-colors">In Progress</button>
                    <button className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors">Complete</button>
                    <button className="text-xs text-red-400 hover:text-red-300 transition-colors">Reject</button>
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