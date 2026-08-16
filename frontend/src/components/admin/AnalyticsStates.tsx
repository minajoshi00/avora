/**
 * Shared UI states for the real analytics dashboard.
 * Loading / Error / Empty — no fake data is ever rendered here.
 */

import { AlertCircle, Loader2, Inbox } from 'lucide-react';

export function LoadingState({ label = 'Loading real analytics…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-gray-400">
      <Loader2 size={18} className="animate-spin text-blue-400" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6 text-center">
      <AlertCircle size={28} className="text-red-400 mx-auto mb-3" />
      <p className="text-base font-semibold text-white mb-2">Analytics temporarily unavailable</p>
      <p className="text-sm text-red-200 mb-4">{message}</p>
      <p className="text-xs text-gray-400 mb-4">
        AVORA couldn't reach the analytics service. No fake numbers are shown while the real dashboard is offline.
      </p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center justify-center rounded-full bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/15"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({ label = 'No data yet' }: { label?: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-12 text-center">
      <Inbox size={32} className="text-gray-600 mx-auto mb-3" />
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-xs text-gray-600 mt-2">
        Real events will appear here once visitors use AVORA.
      </p>
    </div>
  );
}
