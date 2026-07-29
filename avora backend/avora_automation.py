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
- Activity logging for all steps
- Permission checks before risky actions
================================================================
"""

from __future__ import annotations

import os
import re
import time
import threading
from datetime import datetime
from typing import Optional, Callable

from settings import get_setting
from avora_safety import (
    check_panic,
    log_activity,
    check_permission,
    is_panic,
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

    def cancel(self) -> None:
        """Cancel the task."""
        with self._lock:
            self._cancelled = True
            self.status = STATUS_CANCELLED
        log_activity("AUTOMATION", f"Task cancelled: {self.goal}", level="warning")

    def is_cancelled(self) -> bool:
        return self._cancelled or is_panic()

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

    # Check permission
    if not check_permission(step_permission, step_name):
        result["status"] = STATUS_FAILED
        result["error"] = f"Permission denied for action: {step_permission}"
        log_activity("AUTOMATION", f"Step failed (permission): {step_name}", level="warning")
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
        return str(open_application(params.get("app", "")))

    elif action == "open_website":
        from ai_logic import open_website
        return str(open_website(params.get("url", "")))

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

def plan_task(goal: str) -> list[dict]:
    """
    Break a natural-language goal into ordered steps.
    Uses rule-based decomposition for common patterns.
    """
    goal_lower = goal.lower().strip()
    steps = []

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
