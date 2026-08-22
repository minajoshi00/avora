"""
============================================================
AVORA V2 - Permission-Aware Context Provider
============================================================

Unified, permission-based current-context provider.

Aggregates context ONLY from sources the user has explicitly
enabled in Settings:

  * Activity awareness   -> current application / task
                            (gated by activity_awareness.enabled,
                             titles hidden by privacy_mode)
  * Screen awareness     -> screen analysis summary
                            (gated by screen_awareness.enabled)
  * Companion session    -> mood, user state, active goals
                            (local only, no external data)
  * Journey memory       -> recent meaningful memories
                            (gated by memory.enabled)

Design rules:
  - Every source is checked against its permission setting.
  - Missing or unavailable sources are skipped silently.
  - The result degrades gracefully: with everything disabled,
    only local time/session info is returned.
  - No hidden surveillance: nothing is collected without an
    explicit opt-in setting.

Public API:
    get_current_context()        -> dict
    get_context_summary_text()   -> str  (for AI prompt injection)
"""

import logging
from datetime import datetime

logger = logging.getLogger("ContextProvider")


def _get_setting(path, default):
    try:
        from settings import get_setting

        return get_setting(path, default)

    except Exception:
        return default


def _safe(fn, *args, **kwargs):
    """Run a source function; swallow and log any failure."""
    try:
        return fn(*args, **kwargs)

    except Exception as e:
        logger.debug(f"Context source error: {e}")
        return None


# =============================================================
# SOURCE COLLECTORS (each independently permission-gated)
# =============================================================


def _collect_activity_context(context):
    """Current application / task from the activity monitor."""
    if not _get_setting("activity_awareness.enabled", True):
        return

    privacy_mode = _get_setting("activity_awareness.privacy_mode", False)

    try:
        from companion_intelligence import get_companion_intelligence

        companion = get_companion_intelligence()

        if companion is not None:
            snapshot = companion.context.get_snapshot()
            context["current_activity"] = snapshot.activity_type
            context["user_state"] = (
                snapshot.user_state.value
                if hasattr(snapshot.user_state, "value")
                else str(snapshot.user_state)
            )
            context["session_minutes"] = round(snapshot.session_duration_minutes, 1)
            context["idle_minutes"] = round(snapshot.idle_minutes, 1)

            # Window/process names are personal - respect privacy mode
            if not privacy_mode:
                if snapshot.window_title:
                    context["window_title"] = snapshot.window_title[:100]
                if snapshot.process_name:
                    context["process_name"] = snapshot.process_name[:60]

    except Exception as e:
        logger.debug(f"Activity context unavailable: {e}")


def _collect_screen_context(context):
    """Screen analysis summary from screen awareness (opt-in)."""
    if not _get_setting("screen_awareness.enabled", False):
        return

    def _read():
        from screen_awareness import ScreenAwareness

        # Only use a running instance owned by the main window;
        # never start collection just to read context.
        instance = getattr(ScreenAwareness, "_instance", None)
        if instance is None or not instance.is_available():
            return None

        summary = instance.get_context_summary()
        if not isinstance(summary, dict) or not summary:
            return None

        return {
            "screen_activity": summary.get("current_activity", ""),
            "screen_analysis": str(summary.get("analysis", ""))[:200],
        }

    screen = _safe(_read)
    if screen:
        context.update(screen)


def _collect_goal_context(context):
    """Active goals from the companion goal tracker (local data)."""
    try:
        from companion_intelligence import get_companion_intelligence

        companion = get_companion_intelligence()

        if companion is not None:
            goals = companion.goals.get_active_goals()
            if goals:
                context["active_goals"] = [
                    {
                        "description": g.get("description", ""),
                        "progress": round(float(g.get("progress", 0.0)), 2),
                    }
                    for g in goals[:3]
                ]

    except Exception as e:
        logger.debug(f"Goal context unavailable: {e}")


def _collect_memory_context(context):
    """Recent journey memories (gated by memory.enabled)."""
    if not _get_setting("memory.enabled", True):
        return

    def _read():
        from memory import get_journey_memories

        memories = get_journey_memories(min_importance=0.5)[:3]
        if not memories:
            return None

        return [str(m.get("text", ""))[:100] for m in memories]

    recent = _safe(_read)
    if recent:
        context["recent_journey"] = recent


def _collect_local_context(context):
    """Always-available local context (no permissions needed)."""
    now = datetime.now()
    context["time_of_day"] = now.strftime("%H:%M")
    context["day_of_week"] = now.strftime("%A")


# =============================================================
# PUBLIC API
# =============================================================


def get_current_context() -> dict:
    """
    Build the unified current-context dict.

    Only includes data from sources the user has enabled.
    Never raises - always returns at least local time info.
    """
    context = {}

    _collect_local_context(context)

    for collector in (
        _collect_activity_context,
        _collect_screen_context,
        _collect_goal_context,
        _collect_memory_context,
    ):
        _safe(collector, context)

    return context


def get_context_summary_text(max_lines: int = 12) -> str:
    """
    Human/AI-readable summary of the current context.
    Returns empty string when there is nothing beyond local time.
    """
    context = get_current_context()

    lines = []

    if "current_activity" in context:
        activity = context["current_activity"]
        line = f"- Current activity: {activity}"
        if "window_title" in context:
            line += f" ({context['window_title']})"
        elif "process_name" in context:
            line += f" ({context['process_name']})"
        lines.append(line)

    if "user_state" in context:
        lines.append(f"- User appears to be: {context['user_state']}")

    if "screen_activity" in context:
        lines.append(f"- Screen shows: {context['screen_activity']}")

    if "active_goals":
        goals = context.get("active_goals", [])
        for goal in goals:
            progress = int(float(goal.get("progress", 0.0)) * 100)
            lines.append(f"- Active goal: {goal.get('description', '')} ({progress}%)")

    if "recent_journey" in context:
        for item in context["recent_journey"]:
            lines.append(f"- Recent context: {item}")

    if "idle_minutes" in context and context["idle_minutes"] > 5:
        lines.append(f"- User has been idle for {context['idle_minutes']} minutes")

    lines.append(f"- Local time: {context.get('time_of_day', '')}")

    return chr(10).join(lines[:max_lines])


__all__ = [
    "get_context_summary_text",
    "get_current_context",
]
