'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  hasFeedbackBeenPrompted, 
  markFeedbackPrompted, 
  isFeedbackDismissed, 
  dismissFeedback,
  saveFeedback 
} from '../../lib/storage';
import { trackFeedback, trackEvent } from '../../lib/analytics';
import { Button } from '../ui/Button';
import { Star, MessageSquare, Bug, Lightbulb, X } from 'lucide-react';

type FeedbackType = 'general' | 'bug' | 'feature';

/**
 * FeedbackPrompt
 * 
 * Optional feedback collection shown after several uses.
 * Never interrupts the user while they're busy.
 */
export function FeedbackPrompt() {
  const [show, setShow] = useState(false);
  const [rating, setRating] = useState(0);
  const [comments, setComments] = useState('');
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('general');
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    // Don't prompt if already dismissed or completed
    if (hasFeedbackBeenPrompted() || isFeedbackDismissed()) return;

    // Show after 30 seconds of page load (not during active use)
    const timer = setTimeout(() => {
      // Only show if user is idle (not interacting)
      setShow(true);
    }, 30000);

    return () => clearTimeout(timer);
  }, []);

  const handleSubmit = () => {
    if (rating === 0) return;

    // Save feedback
    saveFeedback(rating, comments, feedbackType);
    markFeedbackPrompted();
    
    // Track event (real, server-side)
    trackFeedback(rating, feedbackType, comments.length > 0);

    setSubmitted(true);
    
    // Auto-hide after showing thank you
    setTimeout(() => {
      setShow(false);
    }, 2500);
  };

  const handleDismiss = () => {
    dismissFeedback();
    setShow(false);
    trackEvent('Feedback', { action: 'dismissed' });
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed bottom-6 right-6 z-[150] max-w-md"
        >
          <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 50, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 24 }}
            className="relative rounded-2xl border border-white/[0.08] bg-[#0f0f14] backdrop-blur-xl p-6 shadow-2xl"
          >
            {!submitted ? (
              <>
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">How is AVORA working for you?</h3>
                  <button
                    onClick={handleDismiss}
                    className="w-6 h-6 rounded-full bg-white/[0.06] flex items-center justify-center hover:bg-white/[0.1] transition-colors"
                  >
                    <X size={12} className="text-gray-400" />
                  </button>
                </div>

                {/* Star Rating */}
                <div className="flex items-center justify-center gap-2 mb-4">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setRating(star)}
                      className="transition-transform hover:scale-110"
                    >
                      <Star
                        size={28}
                        className={
                          star <= rating
                            ? 'text-yellow-400 fill-yellow-400'
                            : 'text-gray-600'
                        }
                      />
                    </button>
                  ))}
                </div>

                {/* Feedback Type Tabs */}
                <div className="flex gap-2 mb-4">
                  {[
                    { type: 'general' as FeedbackType, icon: MessageSquare, label: 'General' },
                    { type: 'bug' as FeedbackType, icon: Bug, label: 'Bug' },
                    { type: 'feature' as FeedbackType, icon: Lightbulb, label: 'Feature' },
                  ].map(({ type, icon: Icon, label }) => (
                    <button
                      key={type}
                      onClick={() => setFeedbackType(type)}
                      className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs transition-all ${
                        feedbackType === type
                          ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                          : 'bg-white/[0.02] text-gray-400 border border-white/[0.08] hover:bg-white/[0.04]'
                      }`}
                    >
                      <Icon size={12} />
                      {label}
                    </button>
                  ))}
                </div>

                {/* Comments */}
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder={
                    feedbackType === 'bug' 
                      ? 'Tell us what went wrong...' 
                      : feedbackType === 'feature' 
                      ? 'Tell us what you would like to see...'
                      : 'Tell us what you think...'
                  }
                  className="w-full px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.08] text-sm text-white placeholder-gray-600 resize-none focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
                  rows={3}
                />

                {/* Actions */}
                <div className="flex gap-2 mt-4">
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={handleSubmit}
                    disabled={rating === 0}
                    className="flex-1"
                  >
                    Submit Feedback
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleDismiss}
                  >
                    Later
                  </Button>
                </div>
              </>
            ) : (
              /* Thank You State */
              <div className="text-center py-6">
                <div className="text-4xl mb-3">🙏</div>
                <h3 className="text-lg font-semibold text-white mb-2">Thank you!</h3>
                <p className="text-sm text-gray-400">Your feedback helps us improve AVORA.</p>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default FeedbackPrompt;