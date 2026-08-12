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

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center">
      <AlertCircle size={28} className="text-red-400 mx-auto mb-3" />
      <p className="text-sm text-red-300">{message}</p>
      <p className="text-xs text-gray-500 mt-2">
        The analytics server must be running and reachable. Check the AVORA analytics service.
      </p>
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
