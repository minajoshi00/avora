/**
 * useAnalyticsSummary — shared hook for the real analytics dashboard.
 *
 * Handles loading / error / ready / empty states in one place so every admin
 * section behaves consistently and never falls back to fake numbers.
 */

import { useEffect, useState, useCallback } from 'react';
import {
  fetchAnalyticsSummary,
  type AnalyticsState,
  type AnalyticsSummary,
  type Range,
} from '../lib/analytics-client';

export function useAnalyticsSummary(range: Range = '7d') {
  const [state, setState] = useState<AnalyticsState>({ status: 'loading' });

  const load = useCallback(() => {
    const controller = new AbortController();
    setState({ status: 'loading' });
    fetchAnalyticsSummary(range, controller.signal)
      .then((data: AnalyticsSummary) => setState({ status: 'ready', data }))
      .catch((err: Error) => {
        if (controller.signal.aborted) return;
        setState({ status: 'error', message: err.message || 'Failed to load analytics' });
      });
    return controller;
  }, [range]);

  useEffect(() => {
    const controller = load();
    return () => controller.abort();
  }, [load]);

  return { state, reload: load };
}
