# ============================================================
# TASK STATE MODEL — AVORA AGENT MODE
# ============================================================
# Foundational task state machine for Agent Mode.
# Tracks task lifecycle from planning through completion.
# Does NOT replace existing ActionPlanner or Skill Registry.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class TaskState(Enum):
    """Supported task states for the Agent Mode task machine."""

    PLANNING = auto()
    READY = auto()
    EXECUTING = auto()
    OBSERVING = auto()
    VERIFYING = auto()
    WAITING_FOR_USER = auto()
    RECOVERING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


_TASK_STATE_NAMES = {
    TaskState.PLANNING: "PLANNING",
    TaskState.READY: "READY",
    TaskState.EXECUTING: "EXECUTING",
    TaskState.OBSERVING: "OBSERVING",
    TaskState.VERIFYING: "VERIFYING",
    TaskState.WAITING_FOR_USER: "WAITING_FOR_USER",
    TaskState.RECOVERING: "RECOVERING",
    TaskState.PAUSED: "PAUSED",
    TaskState.COMPLETED: "COMPLETED",
    TaskState.FAILED: "FAILED",
    TaskState.CANCELLED: "CANCELLED",
}


class Task:
    """
    Core task state model for AVORA Agent Mode.

    A task survives waiting for the user, supports pause/resume,
    and maintains enough context to resume exactly where it stopped.

    Attributes:
        task_id: Unique identifier for this task.
        original_goal: The user's high-level goal that started this task.
        current_state: The TaskState enum representing current lifecycle phase.
        plan: Ordered list of validated actions to execute.
        current_step: Index of the step currently being executed.
        completed_steps: Indices of steps that have completed successfully.
        observations: What the agent has observed after each action.
        verification_results: Success/failure result of each verification.
        errors: Collected errors during task execution.
        retry_count: How many times the current step has been retried.
        recovery_count: How many recovery attempts have been made.
        required_user_input: Information waiting from the user to proceed.
        created_at: Timestamp when the task was created.
        updated_at: Timestamp of the last state change.
    """

    def __init__(
        self,
        original_goal: str,
        *,
        task_id: Optional[str] = None,
        state: TaskState = TaskState.PLANNING,
        plan: Optional[List[Dict[str, Any]]] = None,
        current_step: int = 0,
        completed_steps: Optional[List[int]] = None,
        observations: Optional[List[Dict[str, Any]]] = None,
        verification_results: Optional[List[Dict[str, Any]]] = None,
        errors: Optional[List[str]] = None,
        retry_count: int = 0,
        recovery_count: int = 0,
        required_user_input: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id or self._generate_id()
        self.original_goal = original_goal
        self.current_state = state
        self.plan = plan or []
        self.current_step = current_step
        self.completed_steps = completed_steps or []
        self.observations = observations or []
        self.verification_results = verification_results or []
        self.errors = errors or []
        self.retry_count = retry_count
        self.recovery_count = recovery_count
        self.required_user_input = required_user_input or {}
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    # -----------------------------------------------------------------
    # ID generation
    # -----------------------------------------------------------------

    @staticmethod
    def _generate_id() -> str:
        import uuid

        return str(uuid.uuid4())

    # -----------------------------------------------------------------
    # State transition helpers
    # -----------------------------------------------------------------

    def can_execute(self) -> bool:
        """Return True if the task can move into EXECUTING state."""
        return self.current_state in (
            TaskState.PLANNING,
            TaskState.READY,
            TaskState.PAUSED,
        )

    def can_observe(self) -> bool:
        """Return True if the task can observe after execution."""
        return self.current_state in (
            TaskState.EXECUTING,
        )

    def can_verify(self) -> bool:
        """Return True if the task can verify after observation."""
        return self.current_state in (
            TaskState.OBSERVING,
        )

    def can_wait_user(self) -> bool:
        """Return True if the task can enter WAITING_FOR_USER state."""
        return self.current_state in (
            TaskState.PLANNING,
            TaskState.EXECUTING,
            TaskState.OBSERVING,
            TaskState.VERIFYING,
        )

    def can_recover(self) -> bool:
        """Return True if the task can attempt recovery."""
        return self.current_state in (
            TaskState.EXECUTING,
            TaskState.OBSERVING,
            TaskState.VERIFYING,
            TaskState.FAILED,
        )

    def can_pause(self) -> bool:
        """Return True if the task can be paused."""
        return self.current_state in (
            TaskState.PLANNING,
            TaskState.READY,
            TaskState.EXECUTING,
            TaskState.OBSERVING,
            TaskState.VERIFYING,
        )

    def can_cancel(self) -> bool:
        """Return True if the task can be cancelled."""
        return self.current_state not in (
            TaskState.COMPLETED,
            TaskState.CANCELLED,
        )

    # -----------------------------------------------------------------
    # State transitions
    # -----------------------------------------------------------------

    def transition_to(self, new_state: TaskState, *, reason: str = "") -> None:
        """Transition the task to a new state, updating timestamps."""
        old = self.current_state
        self.current_state = new_state
        self.updated_at = datetime.now(timezone.utc)

        # Log the transition (safe — no secrets)
        # In production this would feed into the observability log
        if old != new_state:
            pass  # Transition logged by caller if desired

    def plan_step(
        self,
        action: Dict[str, Any],
        *,
        step_index: int,
    ) -> None:
        """Record a step in the plan at the given index."""
        if step_index < 0 or step_index >= len(self.plan):
            # Extend plan if needed
            self.plan.extend(
                [None] * (step_index - len(self.plan) + 1)
            )
        self.plan[step_index] = action

    def complete_step(self, step_index: int, observation: Optional[Dict[str, Any]] = None) -> None:
        """Mark a step as completed and record observation."""
        if step_index not in self.completed_steps:
            self.completed_steps.append(step_index)
        if observation is not None:
            # Keep observations aligned with step index
            while len(self.observations) <= step_index:
                self.observations.append({})
            self.observations[step_index] = observation
        self.updated_at = datetime.now(timezone.utc)

    def add_error(self, error: str) -> None:
        """Add an error to the task's error list."""
        self.errors.append(error)
        self.updated_at = datetime.now(timezone.utc)

    def add_observation(self, observation: Dict[str, Any], step_index: int) -> None:
        """Add an observation for a given step index."""
        while len(self.observations) <= step_index:
            self.observations.append({})
        self.observations[step_index] = observation
        self.updated_at = datetime.now(timezone.utc)

    def set_current_step(self, step_index: int) -> None:
        """Set the current step index."""
        self.current_step = step_index
        self.updated_at = datetime.now(timezone.utc)

    def set_plan(self, plan: List[Dict[str, Any]]) -> None:
        """Replace the entire plan."""
        self.plan = plan
        self.updated_at = datetime.now(timezone.utc)

    def set_required_user_input(self, input_data: Dict[str, Any]) -> None:
        """Set the required user input, transitioning to WAITING_FOR_USER."""
        self.required_user_input = input_data
        self.transition_to(TaskState.WAITING_FOR_USER)

    def clear_required_user_input(self) -> None:
        """Clear user input and allow resumption."""
        self.required_user_input = {}
        # State remains WAITING_FOR_USER — caller decides when to resume

    # -----------------------------------------------------------------
    # Serialization / persistence
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the task to a dictionary for storage/transmission."""
        return {
            "task_id": self.task_id,
            "original_goal": self.original_goal,
            "current_state": _TASK_STATE_NAMES[self.current_state],
            "plan": self.plan,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "observations": self.observations,
            "verification_results": self.verification_results,
            "errors": self.errors,
            "retry_count": self.retry_count,
            "recovery_count": self.recovery_count,
            "required_user_input": self.required_user_input,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Task:
        """Deserialize a task from a dictionary."""
        state_map = {v: k for k, v in _TASK_STATE_NAMES.items()}
        state_enum = state_map.get(data["current_state"], TaskState.PLANNING)

        task = cls(
            original_goal=data["original_goal"],
            task_id=data.get("task_id"),
            state=state_enum,
            plan=data.get("plan", []),
            current_step=data.get("current_step", 0),
            completed_steps=data.get("completed_steps", []),
            observations=data.get("observations", []),
            verification_results=data.get("verification_results", []),
            errors=data.get("errors", []),
            retry_count=data.get("retry_count", 0),
            recovery_count=data.get("recovery_count", 0),
            required_user_input=data.get("required_user_input", {}),
        )
        task.created_at = (
            datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else datetime.now(timezone.utc)
        )
        task.updated_at = (
            datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) else datetime.now(timezone.utc)
        )
        return task

    # -----------------------------------------------------------------
    # Convenient checks
    # -----------------------------------------------------------------

    def is_completed(self) -> bool:
        return self.current_state == TaskState.COMPLETED

    def is_failed(self) -> bool:
        return self.current_state == TaskState.FAILED

    def is_cancelled(self) -> bool:
        return self.current_state == TaskState.CANCELLED

    def is_waiting_for_user(self) -> bool:
        return self.current_state == TaskState.WAITING_FOR_USER

    def is_recovering(self) -> bool:
        return self.current_state == TaskState.RECOVERING

    def is_paused(self) -> bool:
        return self.current_state == TaskState.PAUSED

    def has_plan(self) -> bool:
        return bool(self.plan)

    def current_step_index(self) -> Optional[int]:
        """Return the current step index, or None if no plan."""
        if not self.plan:
            return None
        if self.current_step < 0:
            return 0
        if self.current_step >= len(self.plan):
            return len(self.plan) - 1
        return self.current_step

    def next_step_available(self) -> bool:
        """Return True if there are remaining uncompleted steps."""
        return self.current_step < len(self.plan) and self.current_step not in self.completed_steps

    def has_unverified_steps(self) -> bool:
        """Return True if any step recorded an UNKNOWN verification outcome."""
        return self.highest_verification_status() == "UNKNOWN"

    def highest_verification_status(self) -> Optional[str]:
        """Return the most serious verification status recorded across steps.

        Priority: UNKNOWN (final state could not be established) >
        VERIFIED_FAILURE > VERIFIED_SUCCESS > None. Used to surface honest
        task-level messages without treating UNKNOWN as success.
        """
        statuses = [
            vr.get("status")
            for vr in self.verification_results
            if isinstance(vr, dict) and vr.get("status")
        ]
        if "UNKNOWN" in statuses:
            return "UNKNOWN"
        if "VERIFIED_FAILURE" in statuses:
            return "VERIFIED_FAILURE"
        if any(s == "VERIFIED_SUCCESS" for s in statuses):
            return "VERIFIED_SUCCESS"
        return None

    def __repr__(self) -> str:
        return (
            f"<Task id={self.task_id[:8]}... "
            f"goal={self.original_goal[:30]}... "
            f"state={self.current_state.name}>"
        )