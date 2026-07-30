/**
 * Admin Dashboard - Feedback Center
 * 
 * Displays all user feedback with search, filter, sort, and export.
 */

'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { 
  Search,
  Star,
  MessageSquare,
  Bug,
  Lightbulb,
  Trash2,
  Download,
  Mail,
} from 'lucide-react';
import { getFeedbackRating, getBugReports, getFeatureRequests } from '../../lib/storage';

type FeedbackType = 'general' | 'bug' | 'feature';

interface FeedbackItem {
  rating: number;
  comments: string;
  type: FeedbackType;
  app_version: string;
  timestamp: string;
}

export function FeedbackCenter() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<FeedbackType | 'all'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'rating'>('date');

  // Collect all feedback from storage
  const allFeedback = useMemo(() => {
    const items: FeedbackItem[] = [];
    
    // Add general feedback (if stored)
    const rating = getFeedbackRating();
    if (rating && rating > 0) {
      items.push({
        rating: rating,
        comments: '',
        type: 'general',
        app_version: '1.0.0',
        timestamp: new Date().toISOString(),
      });
    }
    
    // Add bug reports
    const bugReports = getBugReports();
    bugReports.forEach((report: any) => {
      items.push({
        rating: 0,
        comments: report.comments || report.error_message || '',
        type: 'bug',
        app_version: report.app_version || 'unknown',
        timestamp: report.timestamp || new Date().toISOString(),
      });
    });
    
    // Add feature requests
    const featureRequests = getFeatureRequests();
    featureRequests.forEach((request: any) => {
      items.push({
        rating: 0,
        comments: request.description || request.title || '',
        type: 'feature',
        app_version: request.app_version || 'unknown',
        timestamp: request.date || request.timestamp || new Date().toISOString(),
      });
    });
    
    return items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, []);

  // Filter and search
  const filteredFeedback = useMemo(() => {
    let items = allFeedback;
    
    // Filter by type
    if (filterType !== 'all') {
      items = items.filter(item => item.type === filterType);
    }
    
    // Search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      items = items.filter(item => 
        item.comments.toLowerCase().includes(query) ||
        item.app_version.toLowerCase().includes(query) ||
        item.type.toLowerCase().includes(query)
      );
    }
    
    // Sort
    if (sortBy === 'date') {
      items = [...items].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    } else if (sortBy === 'rating') {
      items = [...items].sort((a, b) => b.rating - a.rating);
    }
    
    return items;
  }, [allFeedback, searchQuery, filterType, sortBy]);

  const getTypeIcon = (type: FeedbackType) => {
    switch (type) {
      case 'bug': return <Bug size={14} className="text-red-400" />;
      case 'feature': return <Lightbulb size={14} className="text-yellow-400" />;
      default: return <MessageSquare size={14} className="text-blue-400" />;
    }
  };

  const getTypeColor = (type: FeedbackType) => {
    switch (type) {
      case 'bug': return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'feature': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      default: return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
    }
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleExport = () => {
    const data = filteredFeedback.map(item => ({
      ...item,
      date: item.timestamp,
    }));
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `feedback-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Actions Bar */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search feedback..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.08] text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
          />
        </div>

        {/* Filter */}
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as FeedbackType | 'all')}
          className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.08] text-sm text-gray-300 focus:outline-none focus:border-blue-500/50 transition-all"
        >
          <option value="all">All Types</option>
          <option value="general">General</option>
          <option value="bug">Bug Reports</option>
          <option value="feature">Feature Requests</option>
        </select>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as 'date' | 'rating')}
          className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.08] text-sm text-gray-300 focus:outline-none focus:border-blue-500/50 transition-all"
        >
          <option value="date">Sort by Date</option>
          <option value="rating">Sort by Rating</option>
        </select>

        {/* Export */}
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/20 text-blue-300 border border-blue-500/30 text-sm hover:bg-blue-500/30 transition-all"
        >
          <Download size={14} />
          Export
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <MessageSquare size={14} className="text-blue-400" />
            <p className="text-xs text-gray-500">Total Feedback</p>
          </div>
          <p className="text-xl font-bold text-white">{filteredFeedback.length}</p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Star size={14} className="text-yellow-400" />
            <p className="text-xs text-gray-500">Average Rating</p>
          </div>
          <p className="text-xl font-bold text-white">
            {allFeedback.length > 0 
              ? (allFeedback.reduce((sum, item) => sum + item.rating, 0) / allFeedback.filter(i => i.rating > 0).length || 0).toFixed(1)
              : '0.0'
            }
          </p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Bug size={14} className="text-red-400" />
            <p className="text-xs text-gray-500">Bug Reports</p>
          </div>
          <p className="text-xl font-bold text-white">
            {allFeedback.filter(i => i.type === 'bug').length}
          </p>
        </div>
      </div>

      {/* Feedback List */}
      <div className="space-y-3">
        {filteredFeedback.length === 0 ? (
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-12 text-center">
            <Mail size={32} className="text-gray-600 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No feedback found</p>
          </div>
        ) : (
          filteredFeedback.map((item, index) => (
            <motion.div
              key={`${item.timestamp}-${index}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg border ${getTypeColor(item.type)}`}>
                    {getTypeIcon(item.type)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white capitalize">{item.type}</p>
                    <p className="text-xs text-gray-500">v{item.app_version}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {item.rating > 0 && (
                    <div className="flex items-center gap-1">
                      <Star size={12} className="text-yellow-400 fill-yellow-400" />
                      <span className="text-xs text-gray-400">{item.rating}</span>
                    </div>
                  )}
                  <span className="text-xs text-gray-500">{formatDate(item.timestamp)}</span>
                </div>
              </div>
              
              {item.comments && (
                <p className="text-sm text-gray-300 mb-3">{item.comments}</p>
              )}
              
              <div className="flex items-center gap-2">
                <button className="text-xs text-gray-500 hover:text-gray-300 transition-colors">
                  Mark as Read
                </button>
                <span className="text-gray-600">•</span>
                <button className="text-xs text-red-400 hover:text-red-300 transition-colors flex items-center gap-1">
                  <Trash2 size={10} />
                  Delete
                </button>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}