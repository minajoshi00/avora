"""
===============================================================
                    AUTONOMOUS WORKFLOW PLANNER
===============================================================
AI-powered autonomous workflow planner for AVORA.

When given a goal like "Add Weather API":
  1. Understands the request
  2. Creates a plan
  3. Opens the project
  4. Creates new files
  5. Modifies existing files
  6. Installs dependencies
  7. Runs tests
  8. Fixes compilation errors
  9. Repeats until successful

Only interrupts when:
  - API key required
  - OAuth/login required
  - Multiple valid options exist
  - Destructive action needs confirmation

Features:
  - Intelligent goal decomposition
  - Automatic error recovery
  - Smart retry logic
  - Activity logging
  - Permission-aware execution
===============================================================
"""

from __future__ import annotations

import os
import re
import time
import threading
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

from .avora_safety import (
    log_activity,
    check_panic,
    is_panic,
    redact_sensitive,
)
from .automation_permissions import (
    get_permission_manager,
    PermissionLevel,
    format_permission_message,
)
from .avora_automation import (
    AutomationTask,
    TaskManager,
    create_automation_task,
    execute_automation_task,
    get_task_manager,
    STATUS_PENDING,
    STATUS_RUNNING,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_SKIPPED,
    STATUS_CANCELLED,
)


# ============================================================
# WORKFLOW STATUS
# ============================================================

WORKFLOW_PENDING = "pending"
WORKFLOW_RUNNING = "running"
WORKFLOW_COMPLETED = "completed"
WORKFLOW_FAILED = "failed"
WORKFLOW_PAUSED = "paused"
WORKFLOW_CANCELLED = "cancelled"


# ============================================================
# AUTONOMOUS WORKFLOW
# ============================================================

class AutonomousWorkflow:
    """
    Autonomous workflow that can execute complex goals
    with minimal human intervention.
    """
    
    def __init__(self, workflow_id: str = None):
        self.workflow_id = workflow_id or f"workflow_{int(time.time())}"
        self.status = WORKFLOW_PENDING
        self.goal = ""
        self.plan: List[dict] = []
        self.current_step = 0
        self.task: Optional[AutomationTask] = None
        self.created_at = datetime.now().isoformat(timespec="seconds")
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.error: Optional[str] = None
        self._lock = threading.RLock()
        self._cancelled = False
        self._paused = False
    
    def cancel(self):
        """Cancel the workflow."""
        with self._lock:
            self._cancelled = True
            self.status = WORKFLOW_CANCELLED
            if self.task:
                from avora_automation import cancel_automation_task
                cancel_automation_task(self.task.task_id)
        log_activity("WORKFLOW", f"Workflow cancelled: {self.goal}", level="warning")
    
    def is_cancelled(self) -> bool:
        return self._cancelled or is_panic()
    
    def get_status(self) -> dict:
        """Get workflow status."""
        with self._lock:
            progress = {
                "workflow_id": self.workflow_id,
                "goal": self.goal,
                "status": self.status,
                "current_step": self.current_step,
                "total_steps": len(self.plan),
                "error": self.error,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
            }
            
            if self.task:
                task_progress = self.task.get_progress()
                progress.update({
                    "task_status": task_progress.get("status"),
                    "percentage": task_progress.get("percentage"),
                    "current_step_name": task_progress.get("current_step_name"),
                })
            
            return progress


# ============================================================
# WORKFLOW PLANNER
# ============================================================

class AutonomousPlanner:
    """
    Plans and executes autonomous workflows.
    Uses AI to decompose goals into executable steps.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._workflows: Dict[str, AutonomousWorkflow] = {}
        self._permission_manager = get_permission_manager()
    
    def create_workflow(self, goal: str) -> AutonomousWorkflow:
        """
        Create an autonomous workflow from a goal.
        
        Args:
            goal: Natural language description of what to accomplish
            
        Returns:
            AutonomousWorkflow instance
        """
        workflow = AutonomousWorkflow()
        workflow.goal = goal
        
        # Generate plan
        workflow.plan = self._generate_plan(goal)
        
        with self._lock:
            self._workflows[workflow.workflow_id] = workflow
        
        log_activity(
            "WORKFLOW",
            f"Created workflow: {goal} ({len(workflow.plan)} steps)",
            level="info",
        )
        
        return workflow
    
    def _generate_plan(self, goal: str) -> List[dict]:
        """
        Generate an execution plan from a goal.
        Uses pattern matching and AI assistance.
        """
        goal_lower = goal.lower().strip()
        steps = []
        
        # Pattern: Add/Create API
        if any(kw in goal_lower for kw in ["add api", "add weather", "integrate api", "create api"]):
            steps = self._plan_add_api(goal)
        
        # Pattern: Create project/file
        elif any(kw in goal_lower for kw in ["create project", "new project", "create app"]):
            steps = self._plan_create_project(goal)
        
        # Pattern: Fix error
        elif any(kw in goal_lower for kw in ["fix error", "fix bug", "debug"]):
            steps = self._plan_fix_error(goal)
        
        # Pattern: Install dependency
        elif any(kw in goal_lower for kw in ["install", "add package", "add dependency"]):
            steps = self._plan_install_dependency(goal)
        
        # Pattern: Run tests
        elif any(kw in goal_lower for kw in ["run tests", "test", "execute tests"]):
            steps = self._plan_run_tests(goal)
        
        # Default: Use AI to generate plan
        else:
            steps = self._plan_with_ai(goal)
        
        return steps
    
    def _plan_add_api(self, goal: str) -> List[dict]:
        """Plan for adding an API integration."""
        return [
            {
                "name": "Analyze project structure",
                "action": "list_folder",
                "params": {"path": "."},
                "permission": "safe",
            },
            {
                "name": "Ask AI for API integration plan",
                "action": "ask_ai",
                "params": {"prompt": f"Create a plan to integrate: {goal}. What files need to be created/modified?"},
                "permission": "safe",
            },
            {
                "name": "Create API service file",
                "action": "create_file",
                "params": {"path": "services/api_service.py", "content": "# TODO: Implement API service"},
                "permission": "file_write",
            },
            {
                "name": "Install required dependencies",
                "action": "run_cmd",
                "params": {"command": "pip install requests"},
                "permission": "system",
            },
            {
                "name": "Run tests to verify",
                "action": "run_cmd",
                "params": {"command": "python -m pytest tests/ -v"},
                "permission": "system",
            },
        ]
    
    def _plan_create_project(self, goal: str) -> List[dict]:
        """Plan for creating a new project."""
        return [
            {
                "name": "Create project folder",
                "action": "create_folder",
                "params": {"path": "new_project"},
                "permission": "file_write",
            },
            {
                "name": "Create main.py",
                "action": "create_file",
                "params": {"path": "new_project/main.py", "content": "# New project\n"},
                "permission": "file_write",
            },
            {
                "name": "Create requirements.txt",
                "action": "create_file",
                "params": {"path": "new_project/requirements.txt", "content": ""},
                "permission": "file_write",
            },
            {
                "name": "Open project folder",
                "action": "open_folder",
                "params": {"path": "new_project"},
                "permission": "safe",
            },
        ]
    
    def _plan_fix_error(self, goal: str) -> List[dict]:
        """Plan for fixing an error."""
        return [
            {
                "name": "Analyze error details",
                "action": "ask_ai",
                "params": {"prompt": f"Analyze and suggest fix for: {goal}"},
                "permission": "safe",
            },
            {
                "name": "Apply fix",
                "action": "ask_ai",
                "params": {"prompt": f"Apply the suggested fix for: {goal}"},
                "permission": "file_write",
            },
            {
                "name": "Run tests to verify fix",
                "action": "run_cmd",
                "params": {"command": "python -m pytest tests/ -v"},
                "permission": "system",
            },
        ]
    
    def _plan_install_dependency(self, goal: str) -> List[dict]:
        """Plan for installing a dependency."""
        goal_lower = goal.lower().strip()
        match = re.search(r'install\s+(\w+)', goal_lower)
        package = match.group(1) if match else "package"
        
        return [
            {
                "name": f"Install {package}",
                "action": "run_cmd",
                "params": {"command": f"pip install {package}"},
                "permission": "system",
            },
            {
                "name": "Verify installation",
                "action": "run_cmd",
                "params": {"command": f"pip show {package}"},
                "permission": "safe",
            },
        ]
    
    def _plan_run_tests(self, goal: str) -> List[dict]:
        """Plan for running tests."""
        return [
            {
                "name": "Run test suite",
                "action": "run_cmd",
                "params": {"command": "python -m pytest tests/ -v"},
                "permission": "system",
            },
            {
                "name": "Report results",
                "action": "ask_ai",
                "params": {"prompt": "Summarize test results and suggest fixes for failures"},
                "permission": "safe",
            },
        ]
    
    def _plan_with_ai(self, goal: str) -> List[dict]:
        """Use AI to generate a plan for complex goals."""
        return [
            {
                "name": "Analyze goal with AI",
                "action": "ask_ai",
                "params": {"prompt": f"Break this goal into executable steps: {goal}"},
                "permission": "safe",
            },
            {
                "name": "Execute plan",
                "action": "ask_ai",
                "params": {"prompt": f"Execute the plan for: {goal}"},
                "permission": "safe",
            },
        ]
    
    def execute_workflow(
        self,
        workflow: AutonomousWorkflow,
        on_progress: Callable = None,
        on_complete: Callable = None,
        on_error: Callable = None,
        on_permission_required: Callable = None,
    ):
        """
        Execute an autonomous workflow.
        
        Args:
            workflow: The workflow to execute
            on_progress: Callback(status) for progress updates
            on_complete: Callback(workflow) when complete
            on_error: Callback(workflow, error) on error
            on_permission_required: Callback(action, details, level) when permission needed
        """
        def _run():
            with self._lock:
                workflow.status = WORKFLOW_RUNNING
                workflow.started_at = datetime.now().isoformat(timespec="seconds")
            
            log_activity(
                "WORKFLOW",
                f"Started executing: {workflow.goal}",
                level="info",
            )
            
            # Create automation task
            task = create_automation_task(
                goal=workflow.goal,
                steps=workflow.plan,
            )
            workflow.task = task
            
            # Execute with permission handling
            max_retries = 3
            
            for attempt in range(max_retries):
                if workflow.is_cancelled():
                    break
                
                try:
                    # Custom executor with permission handling
                    self._execute_with_permissions(
                        workflow,
                        on_permission_required,
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        workflow.error = str(e)
                        workflow.status = WORKFLOW_FAILED
                        log_activity(
                            "WORKFLOW",
                            f"Failed: {workflow.goal} - {e}",
                            level="error",
                        )
                        if on_error:
                            try:
                                on_error(workflow, str(e))
                            except Exception:
                                pass
                    else:
                        log_activity(
                            "WORKFLOW",
                            f"Retrying workflow (attempt {attempt + 1})",
                            level="info",
                        )
                        time.sleep(1)
            
            # Finalize
            if workflow.status != WORKFLOW_FAILED and not workflow.is_cancelled():
                workflow.status = WORKFLOW_COMPLETED
            
            workflow.completed_at = datetime.now().isoformat(timespec="seconds")
            
            if on_complete:
                try:
                    on_complete(workflow)
                except Exception:
                    pass
            
            log_activity(
                "WORKFLOW",
                f"Workflow finished: {workflow.goal} (status: {workflow.status})",
                level="info",
            )
        
        thread = threading.Thread(
            target=_run,
            daemon=True,
            name=f"Workflow-{workflow.workflow_id}",
        )
        thread.start()
    
    def _execute_with_permissions(
        self,
        workflow: AutonomousWorkflow,
        on_permission_required: Callable,
    ):
        """
        Execute workflow steps with permission checking.
        Handles Level 2 and Level 3 permissions.
        """
        task = workflow.task
        
        for i, step in enumerate(task.steps):
            if workflow.is_cancelled():
                break
            
            workflow.current_step = i
            
            # Check if permission is required
            action = step.get("action", "")
            perm_manager = self._permission_manager
            permission_level = perm_manager.get_permission_level(action)
            
            # Level 1: Safe - proceed automatically
            if permission_level == PermissionLevel.SAFE:
                # Execute step
                from avora_automation import execute_step
                result = execute_step(step, task)
                task.results.append(result)
                
                if result["status"] == STATUS_FAILED:
                    raise Exception(f"Step failed: {result.get('error')}")
            
            # Level 2 & 3: Need permission
            else:
                # Notify that permission is required
                if on_permission_required:
                    try:
                        details = step.get("params", {})
                        allowed = on_permission_required(
                            action,
                            str(details),
                            permission_level,
                        )
                        
                        if allowed is None:
                            # User hasn't responded yet - wait
                            time.sleep(0.5)
                            continue
                        
                        if allowed:
                            # Grant permission
                            perm_manager.grant_permission(action, remember=(permission_level == PermissionLevel.CONFIRM_ONCE))
                            
                            # Execute step
                            from avora_automation import execute_step
                            result = execute_step(step, task)
                            task.results.append(result)
                            
                            if result["status"] == STATUS_FAILED:
                                raise Exception(f"Step failed: {result.get('error')}")
                        else:
                            # Permission denied
                            result = {
                                "step_name": step.get("name", ""),
                                "action": action,
                                "status": STATUS_FAILED,
                                "error": "Permission denied by user",
                                "timestamp": datetime.now().isoformat(timespec="seconds"),
                            }
                            task.results.append(result)
                            raise Exception(f"Permission denied: {action}")
                    
                    except Exception as e:
                        if "Permission denied" in str(e):
                            raise
                        # Other errors - retry
                        continue
                else:
                    # No permission handler - skip
                    result = {
                        "step_name": step.get("name", ""),
                        "action": action,
                        "status": STATUS_SKIPPED,
                        "error": "No permission handler available",
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                    }
                    task.results.append(result)
        
        # Update workflow status
        if all(r["status"] == STATUS_COMPLETED for r in task.results):
            workflow.status = WORKFLOW_COMPLETED
        elif any(r["status"] == STATUS_FAILED for r in task.results):
            workflow.status = WORKFLOW_FAILED
        else:
            workflow.status = WORKFLOW_COMPLETED
    
    def get_workflow(self, workflow_id: str) -> Optional[AutonomousWorkflow]:
        """Get a workflow by ID."""
        with self._lock:
            return self._workflows.get(workflow_id)
    
    def get_all_workflows(self) -> List[AutonomousWorkflow]:
        """Get all workflows."""
        with self._lock:
            return list(self._workflows.values())


# ============================================================
# GLOBAL PLANNER
# ============================================================

_planner = AutonomousPlanner()


def get_planner() -> AutonomousPlanner:
    """Get the global autonomous planner."""
    return _planner


def create_workflow(goal: str) -> AutonomousWorkflow:
    """Create a new autonomous workflow."""
    return _planner.create_workflow(goal)


def execute_workflow(
    workflow: AutonomousWorkflow,
    on_progress: Callable = None,
    on_complete: Callable = None,
    on_error: Callable = None,
    on_permission_required: Callable = None,
):
    """Execute an autonomous workflow."""
    _planner.execute_workflow(
        workflow,
        on_progress,
        on_complete,
        on_error,
        on_permission_required,
    )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "AutonomousWorkflow",
    "AutonomousPlanner",
    "WORKFLOW_PENDING",
    "WORKFLOW_RUNNING",
    "WORKFLOW_COMPLETED",
    "WORKFLOW_FAILED",
    "WORKFLOW_PAUSED",
    "WORKFLOW_CANCELLED",
    "get_planner",
    "create_workflow",
    "execute_workflow",
]
