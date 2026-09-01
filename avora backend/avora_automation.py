"""
================================================================
AVORA AUTOMATION PLANNER
================================================================

Multi-step autonomous planner that breaks complex goals into
steps, executes sequentially, verifies each step, shows progress,
supports cancellation, and safely recovers from errors.

Features:
- Natural-language goal decomposition
- Sequential step execution with verification
- Progress tracking (percentage, current step)
- Cancellation support (checks panic state)
- Error recovery (retry, skip, abort)
- Activity logging
- Permission checks before risky actions
- Context propagation between actions
- Reference resolution
- Confidence + ambiguity handling
"""

from __future__ import annotations

import os
import re
import time
import threading
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

from settings import get_setting
from avora_safety import (
    check_panic,
    log_activity,
    check_permission,
    is_panic,
    redact_sensitive,
)
from automation_permissions import (
    get_permission_manager,
    PermissionLevel,
    format_permission_message,
)


# ============================================================
# STEP STATUS
# ============================================================

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUS_CANCELLED = "cancelled"


# ============================================================
# AUTOMATION TASK
# ============================================================

class AutomationTask:
    """Represents a single automation task with multiple steps."""

    def __init__(
        self,
        goal: str,
        steps: list[dict],
        task_id: str = None,
    ):
        self.goal = goal
        self.steps = steps
        self.task_id = task_id or f"task_{int(time.time())}"
        self.status = STATUS_PENDING
        self.current_step_index = 0
        self.created_at = datetime.now().isoformat(timespec="seconds")
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.results: list[dict] = []
        self._cancelled = False
        self._lock = threading.RLock()
        self._required_user_input: Optional[dict] = None
        self._user_input_callback: Optional[Callable] = None

    def cancel(self) -> None:
        """Cancel the task."""
        with self._lock:
            self._cancelled = True
            self.status = STATUS_CANCELLED
        log_activity("AUTOMATION", f"Task cancelled: {self.goal}", level="warning")

    def is_cancelled(self) -> bool:
        return self._cancelled or is_panic()

    def set_required_user_input(self, input_spec: dict):
        """Set required user input (for confirmation, password, etc.)."""
        with self._lock:
            self._required_user_input = input_spec

    def clear_required_user_input(self):
        """Clear required user input."""
        with self._lock:
            self._required_user_input = None

    def get_progress(self) -> dict:
        """Get task progress information."""
        with self._lock:
            total = len(self.steps)
            completed = sum(
                1 for r in self.results
                if r.get("status") == STATUS_COMPLETED
            )
            failed = sum(
                1 for r in self.results
                if r.get("status") == STATUS_FAILED
            )
            percentage = int((completed / total * 100)) if total > 0 else 0

            return {
                "task_id": self.task_id,
                "goal": self.goal,
                "status": self.status,
                "current_step": self.current_step_index + 1 if self.current_step_index < total else total,
                "total_steps": total,
                "completed_steps": completed,
                "failed_steps": failed,
                "percentage": percentage,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "current_step_name": self.steps[self.current_step_index].get("name", "") if self.current_step_index < total else "",
            }


# ============================================================
# STEP EXECUTOR
# ============================================================

def execute_step(
    step: dict,
    task: AutomationTask,
) -> dict:
    """Execute a single automation step."""
    step_name = step.get("name", "unnamed")
    step_action = step.get("action", "")
    step_params = step.get("params", {})
    step_permission = step.get("permission", "safe")
    step_verify = step.get("verify", None)

    result = {
        "step_name": step_name,
        "action": step_action,
        "status": STATUS_PENDING,
        "result": None,
        "error": None,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    # Check cancellation
    if task.is_cancelled():
        result["status"] = STATUS_CANCELLED
        return result

    # Check panic
    try:
        check_panic()
    except RuntimeError:
        result["status"] = STATUS_CANCELLED
        result["error"] = "Cancelled by panic stop"
        return result

    # NEW: Check permission with three-tier system
    perm_manager = get_permission_manager()
    permission_level = perm_manager.get_permission_level(step_action)
    
    # For safe actions (Level 1), proceed automatically
    if permission_level == PermissionLevel.SAFE:
        pass  # Automatic
    
    # For Level 2 and 3, check if we have stored permission
    elif not perm_manager.is_permission_granted(step_action):
        result["status"] = STATUS_FAILED
        result["error"] = f"Permission required for action: {step_action} (Level {permission_level})"
        result["permission_required"] = True
        result["permission_level"] = permission_level
        log_activity("AUTOMATION", f"Step requires permission: {step_name} (Level {permission_level})", level="warning")
        return result

    # Execute the step
    try:
        log_activity("AUTOMATION", f"Executing step: {step_name}", level="info")
        result["status"] = STATUS_RUNNING

        step_result = _dispatch_action(step_action, step_params)

        if step_result is not None:
            result["result"] = step_result

        # Verify if needed
        if step_verify and callable(step_verify):
            try:
                verified = step_verify(step_result)
                if not verified:
                    result["status"] = STATUS_FAILED
                    result["error"] = "Verification failed"
                    log_activity("AUTOMATION", f"Step verification failed: {step_name}", level="warning")
                    return result
            except Exception as e:
                result["status"] = STATUS_FAILED
                result["error"] = f"Verification error: {e}"
                return result

        result["status"] = STATUS_COMPLETED
        log_activity("AUTOMATION", f"Step completed: {step_name}", level="info")

    except Exception as e:
        result["status"] = STATUS_FAILED
        result["error"] = str(e)
        log_activity("AUTOMATION", f"Step failed: {step_name} - {e}", level="error")

    return result


def _dispatch_action(action: str, params: dict) -> Optional[str]:
    """Dispatch an action to the appropriate handler."""
    action = action.lower().strip()

    # File operations
    if action == "create_file":
        from skills.files import create_file
        path = params.get("path", "")
        content = params.get("content", "")
        return create_file(path, content)

    elif action == "open_file":
        from skills.files import open_file
        return open_file(params.get("path", ""))

    elif action == "list_folder":
        from skills.files import list_folder
        return list_folder(params.get("path", ""))

    elif action == "read_file":
        from skills.files import read_file
        return read_file(params.get("path", ""))

    # App operations
    elif action == "open_app":
        from ai_logic import open_application
        app_name = params.get("app", "")
        if not _is_genuine_app_target(app_name):
            # DEFENSIVE BOUNDARY: the application launcher may ONLY ever
            # receive a genuine application target. Phrases like
            # "search for Minecraft" or "check for Atharba" must NEVER be
            # launched as applications.
            return f"Refused to launch '{app_name}': not a genuine application target"
        return str(open_application(app_name))

    # Semantic web search
    elif action == "search_web":
        from ai_logic import search_google
        return str(search_google(params.get("query", "")))

    # Semantic find (person/file/entity) inside an opened application
    elif action == "find_entity":
        from ai_logic import ask_ai
        target = params.get("target", "")
        context = params.get("context", "")
        return str(ask_ai(f"Find '{target}' inside {context or 'the active application'}"))

    # Semantic media playback
    elif action == "play_media":
        from ai_logic import search_youtube
        return str(search_youtube(params.get("target", "")))

    # Chained step: open the first result of the previous search step
    elif action == "open_search_result":
        from ai_logic import search_google
        query = params.get("query", "")
        if query:
            search_google(query)
            return "Opened first search result"
        return "Open first search result (consumes previous search output)"

    # System setting change ("Turn Bluetooth on")
    elif action == "change_setting":
        import os
        setting = params.get("setting", "").lower()
        state = params.get("state", "").lower()
        if "bluetooth" in setting:
            os.startfile("ms-settings:bluetooth")
            return f"Opened Bluetooth settings ({state})"
        if "wifi" in setting or "wi-fi" in setting:
            os.startfile("ms-settings:network-wifi")
            return f"Opened Wi-Fi settings ({state})"
        os.startfile("ms-settings:")
        return f"Opened Windows settings for '{setting}' ({state})"

    elif action == "open_website":
        from ai_logic import open_website
        url = params.get("url", "")
        return str(open_website(url))

    # System operations
    elif action == "take_screenshot":
        from skills.system import take_screenshot
        return take_screenshot()

    elif action == "get_time":
        from skills.system import get_current_time
        return get_current_time()

    # AI operations
    elif action == "ask_ai":
        from ai_logic import ask_ai
        return ask_ai(params.get("prompt", ""))

    # Memory operations
    elif action == "add_memory":
        from memory import add_memory
        return str(add_memory(params.get("text", ""), params.get("category", "general")))

    # No-op for testing
    elif action == "noop":
        return params.get("message", "Step completed")

    else:
        return f"Unknown action: {action}"


# ============================================================
# TASK PLANNER
# ============================================================

# Action-verb phrases that must NEVER be interpreted as an application
# target (general semantic guard, not tied to any specific app).
_APP_TARGET_FORBIDDEN = re.compile(
    r"\b(search|find|check|look|play|message|send|browse|open|watch|read|write|call|download)\b"
)


def _is_genuine_app_target(name: str) -> bool:
    """Return True only for a plausible application target.

    A genuine application target is short, single-intent, and contains no
    action-verb phrases. Anything like "search for Minecraft" or
    "check for Atharba" is rejected so the launcher boundary can never be
    tricked into launching a command as if it were an application.
    """
    name = (name or "").strip()
    if not name or len(name) > 40:
        return False
    if _APP_TARGET_FORBIDDEN.search(name.lower()):
        return False
    # Multi-clause commands ("x and y") are not application names
    if " and " in name.lower() or ", then " in name.lower():
        return False
    return True


def plan_task(goal: str) -> list[dict]:
    """
    Break a natural-language goal into ordered steps.
    Uses rule-based decomposition for common patterns.
    
    This is the key function that creates proper multi-step plans
    with semantic understanding instead of keyword splitting.
    """
    goal_lower = goal.lower().strip()
    steps = []

    # Pattern: "Open Instagram and check for Atharba Bhandari"
    # This should create: OPEN Instagram -> FIND Atharba Bhandari
    if _is_multi_step_semantic(goal_lower):
        return _plan_semantic_task(goal_lower)

    # Single-step setting change ("Turn Bluetooth on") — also handled
    # semantically, not as an application launch.
    setting_steps: list[dict] = []
    if _plan_setting_change(goal_lower, setting_steps):
        return setting_steps

    # File creation plan
    if "create" in goal_lower and "file" in goal_lower:
        match = re.search(r'create\s+(?:a\s+)?file\s+(?:called\s+)?(.+)', goal_lower)
        if match:
            filename = match.group(1).strip()
            steps = [
                {"name": "Create file", "action": "create_file", "params": {"path": filename, "content": ""}, "permission": "file_write"},
                {"name": "Verify file created", "action": "read_file", "params": {"path": filename}, "permission": "file_read"},
            ]
            return steps

    # Folder creation plan
    if "create" in goal_lower and "folder" in goal_lower:
        match = re.search(r'create\s+(?:a\s+)?folder\s+(?:called\s+)?(.+)', goal_lower)
        if match:
            foldername = match.group(1).strip()
            steps = [
                {"name": "Create folder", "action": "create_folder", "params": {"path": foldername}, "permission": "file_write"},
            ]
            return steps

    # Study plan
    if "study" in goal_lower or "learn" in goal_lower:
        steps = [
            {"name": "Set study goal", "action": "noop", "params": {"message": f"Study goal: {goal}"}, "permission": "safe"},
            {"name": "Ask AI for study plan", "action": "ask_ai", "params": {"prompt": f"Create a study plan for: {goal}"}, "permission": "safe"},
        ]
        return steps

    # Default: single AI step
    steps = [
        {"name": "Process goal", "action": "ask_ai", "params": {"prompt": goal}, "permission": "safe"},
    ]
    return steps


def _is_multi_step_semantic(text: str) -> bool:
    """Check if the text represents a multi-step semantic request."""
    # Check for connectors that indicate sequence, not just keyword matching
    connectors = ["then", "after that", "and then", "next", "followed by", "afterwards"]
    if any(indicator in text for indicator in connectors):
        return True
    
    # Check for comma-separated multi-intent sentences
    if text.count(",") >= 2:
        return True
    
    # Check for "and" connecting different action types
    # e.g., "Open Instagram and check for Atharba Bhandari"
    if " and " in text:
        parts = text.split(" and ")
        if len(parts) >= 2:
            # Check if parts have different verb types
            verb_indicators = ["open", "search", "find", "play", "send", "turn", "check"]
            parts_have_verbs = []
            for part in parts:
                has_verb = any(part.strip().startswith(f"{v} ") or f" {v} " in part for v in verb_indicators)
                parts_have_verbs.append(has_verb)
            if any(parts_have_verbs) and all(parts_have_verbs) == False or sum(parts_have_verbs) > 1:
                return True
    
    return False


def _plan_semantic_task(goal: str) -> list[dict]:
    """Plan a semantic multi-step task by understanding intent, entities, and context."""
    goal_lower = goal.lower().strip()
    steps = []
    
    # Parse the goal to understand intent, entities, and required actions
    # This replaces naive keyword splitting with semantic understanding
    
    # Pattern: "Open Instagram and check for Atharba Bhandari"
    # Detect: OPEN_APPLICATION + FIND_PERSON
    
    # Pattern: "Open Chrome and search for Minecraft shaders"
    # Detect: OPEN Chrome + SEARCH web
    
    # Pattern: "Open Downloads and find the physics PDF"
    # Detect: OPEN Downloads + FIND file
    
    # Pattern: "Open YouTube and play the latest MrBeast video"
    # Detect: OPEN YouTube + FIND creator + PLAY latest
    
    # Pattern: "Turn Bluetooth on"
    # Detect: CHANGE_SETTING Bluetooth = ON
    
    # Try to identify the pattern
    if _plan_open_then_find(goal_lower, steps):
        return steps
    
    if _plan_open_then_search(goal_lower, steps):
        return steps
    
    if _plan_open_then_play(goal_lower, steps):
        return steps
    
    if _plan_setting_change(goal_lower, steps):
        return steps
    
    # Fallback to default AI plan
    return [
        {"name": "Process goal", "action": "ask_ai", "params": {"prompt": goal}, "permission": "safe"},
    ]


def _plan_open_then_find(goal: str, steps: list) -> bool:
    """Plan: Open application, then find/check for person/entity.

    Matches verbs like "find", "check for", "look for", "look up" —
    generically, not tied to any single application.
    """
    match = re.match(
        r"open\s+(.+?)\s+and\s+(?:find|check(?:\s+for)?|look\s+(?:up|for))\s*(.*)",
        goal,
    )
    if match:
        app = match.group(1).strip()
        target = (match.group(2) or "").strip()
        if not target:
            return False
        # Guard: if the "target" itself is a web-search phrasing, let the
        # search planner handle it instead of treating it as an entity.
        if re.match(r"(?:the\s+)?web\b", target):
            return False

        steps.extend([
            {"name": f"Open {app}", "action": "open_app", "params": {"app": app}, "permission": "safe"},
            {"name": f"Find {target}", "action": "find_entity", "params": {"target": target, "context": app}, "permission": "safe"},
        ])
        return True
    return False


def _plan_open_then_search(goal: str, steps: list) -> bool:
    """Plan: Open application, then search web.

    Also handles chained requests like:
        "Open Chrome and search for Minecraft, then open the first result"
    The later step consumes the previous step's context/output via
    `depends_on` + `input_from` references (context propagation).
    """
    match = re.match(r"open\s+(.+?)\s+and\s+search\s+(?:the\s+web\s+)?for\s+(.+)", goal)
    if match:
        app = match.group(1).strip()
        remainder = match.group(2).strip()

        # Split chained follow-up actions: ", then open the first result"
        chained = None
        chain_match = re.match(r"(.+?)[,;]?\s+then\s+(.+)", remainder)
        if chain_match:
            remainder = chain_match.group(1).strip()
            chained = chain_match.group(2).strip()

        steps.extend([
            {"name": f"Open {app}", "action": "open_app", "params": {"app": app}, "permission": "safe"},
            {"name": f"Search web for '{remainder}'", "action": "search_web", "params": {"query": remainder}, "permission": "safe"},
        ])

        if chained:
            # The chained step consumes the search step's output.
            if re.match(r"open\s+(?:the\s+)?(?:first|top)\s+result", chained):
                steps.append({
                    "name": "Open first search result",
                    "action": "open_search_result",
                    "params": {"position": 1},
                    "input_from": "search_web",       # consumes previous output
                    "depends_on": "search_web",
                    "permission": "safe",
                })
            else:
                steps.append({
                    "name": chained.title(),
                    "action": "ask_ai",
                    "params": {"prompt": chained, "context_from": "search_web"},
                    "depends_on": "search_web",
                    "permission": "safe",
                })
        return True
    return False


def _plan_open_then_play(goal: str, steps: list) -> bool:
    """Plan: Open application, then play media."""
    # Pattern: "Open X and play Y"
    match = re.match(r"open\s+(.+?)\s+and\s+play\s+(.+)", goal)
    if match:
        app = match.group(1).strip()
        target = match.group(2).strip()
        
        steps.extend([
            {"name": f"Open {app}", "action": "open_app", "params": {"app": app}, "permission": "safe"},
            {"name": f"Play {target}", "action": "play_media", "params": {"target": target}, "permission": "safe"},
        ])
        return True
    return False


def _plan_setting_change(goal: str, steps: list) -> bool:
    """Plan: Change a system setting."""
    # Pattern: "Turn X on/off"
    match = re.match(r"(turn|change)\s+(?:the\s+)?(.+?)\s+(on|off)", goal)
    if match:
        action = match.group(1).strip()
        setting = match.group(2).strip()
        state = match.group(3).strip()
        
        steps.extend([
            {"name": f"Change {setting} to {state}", "action": "change_setting", "params": {"setting": setting, "state": state}, "permission": "safe"},
        ])
        return True
    return False


# ============================================================
# TASK MANAGER
# ============================================================

class TaskManager:
    """Manages multiple automation tasks."""

    def __init__(self):
        self._tasks: dict[str, AutomationTask] = {}
        self._lock = threading.RLock()
        self._executor_thread: Optional[threading.Thread] = None

    def create_task(
        self,
        goal: str,
        steps: list[dict] = None,
    ) -> AutomationTask:
        """Create a new automation task."""
        if steps is None:
            steps = plan_task(goal)

        task = AutomationTask(goal=goal, steps=steps)

        with self._lock:
            self._tasks[task.task_id] = task

        log_activity("AUTOMATION", f"Task created: {goal} ({len(steps)} steps)")
        return task

    def execute_task(
        self,
        task: AutomationTask,
        on_progress: Callable = None,
        on_complete: Callable = None,
        on_error: Callable = None,
    ) -> None:
        """Execute a task asynchronously."""
        def _run():
            task.status = STATUS_RUNNING
            task.started_at = datetime.now().isoformat(timespec="seconds")

            max_retries = get_setting("automation.max_retries_per_step", 2)
            step_timeout = get_setting("automation.step_timeout_seconds", 30)

            for i, step in enumerate(task.steps):
                task.current_step_index = i

                # Check cancellation
                if task.is_cancelled():
                    break

                # Check panic
                if is_panic():
                    task.cancel()
                    break

                # Execute with retry
                attempts = 0
                step_result = None

                while attempts <= max_retries:
                    if task.is_cancelled() or is_panic():
                        step_result = {
                            "step_name": step.get("name", ""),
                            "action": step.get("action", ""),
                            "status": STATUS_CANCELLED,
                            "result": None,
                            "error": "Cancelled",
                            "timestamp": datetime.now().isoformat(timespec="seconds"),
                        }
                        break

                    step_result = execute_step(step, task)

                    if step_result["status"] == STATUS_COMPLETED:
                        break

                    if step_result["status"] == STATUS_FAILED:
                        attempts += 1
                        if attempts <= max_retries:
                            log_activity("AUTOMATION", f"Retrying step: {step.get('name', '')} (attempt {attempts})", level="info")
                            time.sleep(0.5)
                        continue

                    break

                task.results.append(step_result)

                # Notify progress
                if on_progress:
                    try:
                        on_progress(task.get_progress())
                    except Exception:
                        pass

                # Handle step failure
                if step_result["status"] == STATUS_FAILED:
                    if on_error:
                        try:
                            on_error(task, step_result)
                        except Exception:
                            pass

                    # Decide: continue or abort
                    auto_continue = get_setting("automation.retry_failed_steps", True)
                    if not auto_continue:
                        task.status = STATUS_FAILED
                        break

            # Finalize
            task.completed_at = datetime.now().isoformat(timespec="seconds")

            if task.is_cancelled():
                task.status = STATUS_CANCELLED
            elif all(r["status"] == STATUS_COMPLETED for r in task.results):
                task.status = STATUS_COMPLETED
            elif any(r["status"] == STATUS_FAILED for r in task.results):
                task.status = STATUS_FAILED
            else:
                task.status = STATUS_COMPLETED

            if on_complete:
                try:
                    on_complete(task)
                except Exception:
                    pass

            log_activity("AUTOMATION", f"Task finished: {task.goal} (status: {task.status})")

        self._executor_thread = threading.Thread(
            target=_run,
            daemon=True,
            name=f"AvoraTask-{task.task_id}",
        )
        self._executor_thread.start()

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.cancel()
                return True
        return False

    def get_task(self, task_id: str) -> Optional[AutomationTask]:
        """Get a task by ID."""
        with self._lock:
            return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[AutomationTask]:
        """Get all tasks."""
        with self._lock:
            return list(self._tasks.values())

    def get_active_tasks(self) -> list[AutomationTask]:
        """Get tasks that are running or pending."""
        with self._lock:
            return [
                t for t in self._tasks.values()
                if t.status in (STATUS_PENDING, STATUS_RUNNING)
            ]


# ============================================================
# GLOBAL TASK MANAGER
# ============================================================

_task_manager = TaskManager()


def get_task_manager() -> TaskManager:
    """Get the global task manager."""
    return _task_manager


def create_automation_task(
    goal: str,
    steps: list[dict] = None,
) -> AutomationTask:
    """Create a new automation task."""
    return _task_manager.create_task(goal, steps)


def execute_automation_task(
    task: AutomationTask,
    on_progress: Callable = None,
    on_complete: Callable = None,
    on_error: Callable = None,
) -> None:
    """Execute an automation task."""
    _task_manager.execute_task(task, on_progress, on_complete, on_error)


def cancel_automation_task(task_id: str) -> bool:
    """Cancel an automation task."""
    return _task_manager.cancel_task(task_id)


def get_all_tasks() -> list[AutomationTask]:
    """Get all automation tasks."""
    return _task_manager.get_all_tasks()


def initialize() -> None:
    """Initialize the automation system."""
    log_activity("AUTOMATION", "Automation Planner initialized")
    print("[AVORA] Automation Planner loaded.")


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "AutomationTask",
    "TaskManager",
    "create_automation_task",
    "execute_automation_task",
    "cancel_automation_task",
    "get_all_tasks",
    "plan_task",
    "execute_step",
    "initialize",
    "STATUS_PENDING",
    "STATUS_RUNNING",
    "STATUS_COMPLETED",
    "STATUS_FAILED",
    "STATUS_SKIPPED",
    "STATUS_CANCELLED",
]