/**
 * Admin Dashboard - Update Management
 */

'use client';

import { motion } from 'framer-motion';
import { RefreshCw, Plus, Edit, Trash2, CheckCircle, Clock, AlertTriangle, Download, HardDrive } from 'lucide-react';

const updates = [
  {
    version: '1.1.0',
    status: 'available',
    releaseDate: '2026-08-15',
    downloads: 234,
    size: '256 MB',
    isLatest: true,
  },
  {
    version: '1.0.0',
    status: 'stable',
    releaseDate: '2026-07-20',
    downloads: 3200,
    size: '245 MB',
    isLatest: false,
  },
  {
    version: '0.9.0',
    status: 'outdated',
    releaseDate: '2026-06-15',
    downloads: 890,
    size: '238 MB',
    isLatest: false,
  },
];

export function UpdateManagement() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-300">Version Management</h3>
          <p className="text-xs text-gray-500 mt-1">Manage releases and update distribution</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/20 text-blue-300 border border-blue-500/30 text-sm hover:bg-blue-500/30 transition-all">
          <Plus size={14} />
          Create Release
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <RefreshCw size={14} className="text-blue-400" />
            <p className="text-xs text-gray-500">Latest Version</p>
          </div>
          <p className="text-xl font-bold text-white">v1.1.0</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle size={14} className="text-emerald-400" />
            <p className="text-xs text-gray-500">Stable</p>
          </div>
          <p className="text-xl font-bold text-white">2</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Clock size={14} className="text-yellow-400" />
            <p className="text-xs text-gray-500">Beta</p>
          </div>
          <p className="text-xl font-bold text-white">0</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={14} className="text-red-400" />
            <p className="text-xs text-gray-500">Outdated</p>
          </div>
          <p className="text-xl font-bold text-white">1</p>
        </div>
      </div>

      {/* Updates List */}
      <div className="space-y-3">
        {updates.map((update, index) => (
          <motion.div
            key={update.version}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg border ${
                  update.isLatest 
                    ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' 
                    : 'text-gray-400 bg-gray-500/10 border-gray-500/20'
                }`}>
                  <RefreshCw size={14} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium text-white">v{update.version}</h3>
                    {update.isLatest && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Latest
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Released {new Date(update.releaseDate).toLocaleDateString()}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button className="p-2 rounded-lg hover:bg-white/[0.04] transition-colors">
                  <Edit size={14} className="text-gray-400" />
                </button>
                <button className="p-2 rounded-lg hover:bg-white/[0.04] transition-colors">
                  <Trash2 size={14} className="text-red-400" />
                </button>
              </div>
            </div>
            
            <div className="flex items-center gap-6 text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <Download size={12} />
                {update.downloads.toLocaleString()} downloads
              </div>
              <div className="flex items-center gap-1">
                <HardDrive size={12} />
                {update.size}
              </div>
              <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border ${
                update.isLatest
                  ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                  : 'text-gray-400 bg-gray-500/10 border-gray-500/20'
              }`}>
                {update.status === 'available' && <Clock size={12} />}
                {update.status === 'stable' && <CheckCircle size={12} />}
                {update.status === 'outdated' && <AlertTriangle size={12} />}
                <span className="capitalize">{update.status}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
