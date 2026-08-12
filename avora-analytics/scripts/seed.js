/**
 * AVORA Analytics — Test/Seed script
 *
 * Creates a small set of *real* events so the dashboard can be verified end-to-end.
 * Uses deterministic event_key values so re-running never double-counts.
 *
 * Usage:  npm run seed   (after the server has created the DB, or standalone)
 */

import { trackEvent } from '../src/events.js';

function isoDaysAgo(days, hour = 12) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  d.setHours(hour, 0, 0, 0);
  return d.toISOString();
}

const users = ['u_aaa', 'u_bbb', 'u_ccc'];
const platforms = ['windows', 'macos', 'linux'];

let n = 0;
function emit(type, day, opts = {}) {
  trackEvent({
    event_key: `seed_${type}_${day}_${n++}`,
    type,
    user_id: opts.user_id || users[n % users.length],
    visitor_id: opts.visitor_id || `v_${n % 5}`,
    value: opts.value || 0,
    props: opts.props || {},
    created_at: isoDaysAgo(day, opts.hour ?? 12),
  });
}

// Spread events over the last 9 days so 7d / 30d ranges both have data.
for (let day = 0; day < 9; day++) {
  const views = 5 + (day % 3);
  for (let i = 0; i < views; i++) emit('pageview', day, { props: { path: '/', platform: platforms[i % 3] } });

  emit('download', day, { props: { platform: platforms[day % 3], version: '1.0.0' } });
  emit('conversation', day, {});
  emit('message', day, {});
  emit('ai_request', day, { props: { provider: day % 2 ? 'gemini' : 'groq' } });
  emit('ai_response', day, {});

  if (day % 2 === 0) emit('mission_created', day, {});
  if (day % 3 === 0) emit('mission_completed', day, {});
  if (day % 4 === 0) emit('task_completed', day, {});
  if (day === 8) emit('app_launch', day, {});
  if (day === 1) emit('error', day, { props: { kind: 'ui' } });
  if (day === 0) emit('feedback', day, { value: 5, props: { type: 'general' } });
}

// A couple of "new users" events for new-vs-returning math.
emit('new_user', 8, { user_id: 'u_aaa' });
emit('new_user', 7, { user_id: 'u_bbb' });
emit('new_user', 2, { user_id: 'u_ccc' });

console.log('[seed] inserted real test events (idempotent). Re-run safe.');
