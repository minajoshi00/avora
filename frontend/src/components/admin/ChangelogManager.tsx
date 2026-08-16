/**
 * Admin Dashboard - Changelog Manager
 */

'use client';

import { motion } from 'framer-motion';
import { FileText, Plus, Edit, Trash2, Calendar } from 'lucide-react';

// Placeholder: real changelog data comes from backend/desktop app
const entries: any[] = [];

export function ChangelogManager() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-300">Version History</h3>
          <p className="text-xs text-gray-500 mt-1">Manage release notes and changelog entries</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/20 text-blue-300 border border-blue-500/30 text-sm hover:bg-blue-500/30 transition-all">
          <Plus size={14} />
          Add Entry
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <FileText size={14} className="text-blue-400" />
            <p className="text-xs text-gray-500">Total Versions</p>
          </div>
          <p className="text-xl font-bold text-white">{entries.length}</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Calendar size={14} className="text-purple-400" />
            <p className="text-xs text-gray-500">Latest Version</p>
          </div>
          <p className="text-xl font-bold text-white">
            {entries[0]?.version || 'N/A'}
          </p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <FileText size={14} className="text-emerald-400" />
            <p className="text-xs text-gray-500">Latest Release</p>
          </div>
          <p className="text-xl font-bold text-white">
            {entries[0]?.release_date || 'N/A'}
          </p>
        </div>
      </div>

      {/* Changelog Entries */}
      <div className="space-y-3">
        {entries.length === 0 ? (
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-12 text-center">
            <FileText size={32} className="text-gray-600 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No changelog entries yet</p>
          </div>
        ) : (
          entries.map((entry: any, index: number) => (
            <motion.div
              key={entry.version}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-white">v{entry.version}</h3>
                    <span className="text-xs text-gray-500">•</span>
                    <span className="text-xs text-gray-500">{entry.release_date}</span>
                  </div>
                  <p className="text-xs text-gray-400">{entry.title || 'AVORA Desktop'}</p>
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
              
              {entry.description && (
                <p className="text-sm text-gray-300 mb-3">{entry.description}</p>
              )}
              
              {(entry.features?.length > 0 || entry.improvements?.length > 0 || entry.bug_fixes?.length > 0) && (
                <div className="space-y-2">
                  {entry.features?.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-emerald-400 mb-1">New Features</p>
                      <ul className="space-y-1">
                        {entry.features.slice(0, 3).map((feature: string, i: number) => (
                          <li key={i} className="text-xs text-gray-400 ml-4">• {feature}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {entry.improvements?.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-blue-400 mb-1">Improvements</p>
                      <ul className="space-y-1">
                        {entry.improvements.slice(0, 3).map((imp: string, i: number) => (
                          <li key={i} className="text-xs text-gray-400 ml-4">• {imp}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {entry.bug_fixes?.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-purple-400 mb-1">Bug Fixes</p>
                      <ul className="space-y-1">
                        {entry.bug_fixes.slice(0, 3).map((fix: string, i: number) => (
                          <li key={i} className="text-xs text-gray-400 ml-4">• {fix}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
