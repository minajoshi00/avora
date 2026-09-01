# ============================================================
# AGENT EXECUTION LOOP — AVORA AGENT MODE
# ============================================================
# Core loop: USER GOAL → UNDERSTAND → PLAN → VALIDATE → EXECUTE →
# OBSERVE → VERIFY → NEXT STEP → COMPLETE
#
# Integrates with existing AVORA systems:
# - Task (state machine from Phase 1)
# - Action (validated action model from Phase 2)
# - Skill Registry (capability layer — not replaced)
# - Intelligence Engine (LLM intent understanding)
# - Recovery Manager (failure handling)
# - Health Monitor (system state)
# ============================================================

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Callable, Awaitable

from avora_backend.action_model import Action, ActionType
from avora_backend.task import Task, TaskState
from avora_backend.verification import (
    VerificationEngine,
    VerificationResult,
    VerificationStatus,
)


# -----------------------------------------------------------------
# Agent Orchestrator — the core execution loop
# -----------------------------------------------------------------

class AgentOrchestrator:
    """
    Core agent execution loop for AVORA Agent Mode.

    Coordinates the full lifecycle of a user goal:
    - Understand the goal
    - Create a task with a plan
    - Execute steps one at a time
    - Observe results after each action
    - Verify expected outcomes
    - Handle failures / recovery
    - Ask user when input is required
    - Pause / resume support
    - Complete / cancel the task

    Does NOT replace ActionPlanner or Skill Registry.
    Uses them as the capability selection layer.

    Tasks are stored by task_id to enable cross-call resume.
    """

    def __init__(
        self,
        *,
        task: Optional[Task] = None,
        # Callables injected by the host application
        understand_callback: Optional[Callable[[str], Any]] = None,
        plan_callback: Optional[Callable[[str], List[Dict[str, Any]]]] = None,
        execute_callback: Optional[Callable[[Action], Any]] = None,
        observe_callback: Optional[Callable[[Action, Any], Dict[str, Any]]] = None,
        verify_callback: Optional[Callable[[Action, Dict[str, Any]], bool]] = None,
        recovery_callback: Optional[Callable[[Task, Exception], Any]] = None,
        user_input_callback: Optional[Callable[[Task, Dict[str, Any]], Any]] = None,
        screen_observer: Optional[Callable[[], Dict[str, Any]]] = None,
        character_callback: Optional[Callable[[Dict[str, Any]], Any]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ):
        self.task = task or Task(original_goal="")
        self._goal_execution_active: bool = False
        self._understand = understand_callback
        self._plan = plan_callback
        self._execute = execute_callback
        self._observe = observe_callback
        self._verify = verify_callback
        self._recovery = recovery_callback
        self._user_input = user_input_callback
        self._screen_observer = screen_observer
        self._character_callback = character_callback
        self._progress_callback = progress_callback
        self._interrupted = False
        self._character_state: Any = None
        self._progress_log: List[Dict[str, Any]] = []
        self._default_verifier: Optional[VerificationEngine] = None
        self._tasks: Dict[str, Task] = {}  # task_id -> Task for resume support

    # -----------------------------------------------------------------
    # Character / emotion integration
    # -----------------------------------------------------------------

    def _get_character_state(self) -> Any:
        """Lazily build the CharacterState used to drive companion emotion."""
        if self._character_state is None:
            from avora_backend.character import CharacterState
            self._character_state = CharacterState()
        return self._character_state

    def _emit_character(self) -> None:
        """Notify the host UI of the current character emotion (if wired)."""
        state = self._get_character_state()
        if self._character_callback:
            try:
                result = self._character_callback(state.snapshot())
                self._run_fire_and_forget(result)
            except Exception:
                pass  # character surfacing is non-blocking

    @property
    def character_state(self) -> Any:
        """Expose the current character/emotion state (snapshot dict)."""
        return self._get_character_state().snapshot()

    # -----------------------------------------------------------------
    # Helper: dispatch callback result (sync or async)
    # -----------------------------------------------------------------

    async def _dispatch_callback(self, coro_or_value: Any) -> Any:
        """Dispatch a callback result that may be a coroutine or a plain value.

        If the callback returned a coroutine, await it and return its actual
        result. If it returned a plain value, return it unchanged. Exceptions
        raised inside the awaited coroutine propagate to the async caller so
        they are handled by that caller's normal error path.

        Must be awaited from an async method. Use `_run_fire_and_forget` only
        for best-effort (non-blocking) emit helpers that cannot await.
        """
        if asyncio.iscoroutine(coro_or_value):
            return await coro_or_value
        return coro_or_value

    @staticmethod
    def _run_fire_and_forget(coro_or_value: Any) -> None:
        """Run a best-effort callback coroutine without blocking the loop.

        Used by synchronous emit helpers (progress / character surfacing) that
        are intentionally non-blocking and must not `await`. A coroutine
        returned by the callback is scheduled on the currently running loop and
        its exceptions are retrieved (and dropped) so it is never left as an
        orphaned task. Plain (non-coroutine) values are ignored here.
        """
        if not asyncio.iscoroutine(coro_or_value):
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        task = loop.create_task(coro_or_value)

        def _consume_result(done_task: "asyncio.Task") -> None:
            try:
                done_task.exception()
            except (asyncio.CancelledError, Exception):
                pass

        task.add_done_callback(_consume_result)

    # -----------------------------------------------------------------
    # Chat progress streaming
    # -----------------------------------------------------------------

    def _emit_progress(self, event: str, message: str, **extra: Any) -> None:
        """Emit a structured progress event streamed to the host chat UI.

        Every event is recorded in `self._progress_log` and (if a
        `progress_callback` is wired) forwarded to the host.
        """
        entry: Dict[str, Any] = {
            "event": event,
            "message": message,
            **extra,
        }
        self._progress_log.append(entry)
        if self._progress_callback:
            try:
                result = self._progress_callback(entry)
                self._run_fire_and_forget(result)
            except Exception:
                pass  # progress surfacing is non-blocking

    @property
    def progress(self) -> List[Dict[str, Any]]:
        """Return the progress events emitted during the run (for chat/history)."""
        return list(self._progress_log)

    # -----------------------------------------------------------------
    # High-level entry point
    # -----------------------------------------------------------------

    async def execute_goal(self, user_goal: str) -> Dict[str, Any]:
        """
        Execute a user goal end-to-end.

        Returns a result dict with:
        - status: "completed" | "failed" | "cancelled" | "waiting_for_user"
        - task_id: the task identifier
        - final_result: natural language result message
        - steps_completed: number of steps finished

        Concurrency model: an orchestrator instance runs exactly ONE active
        goal at a time. `self.task`, the progress log, interrupt flag and
        character state are instance-level mutable state shared by every
        helper method, so a second `execute_goal` racing on the SAME instance
        would overwrite `self.task`, corrupt progress/steps/verification and
        mix results between goals. A concurrent re-entry is therefore rejected
        with a clear error instead of silently corrupting state.

        For genuinely concurrent goals, use a SEPARATE orchestrator instance
        per goal — each instance holds fully isolated task/progress/interrupt/
        confirmation/character state and runs truly concurrently.

        If a task_id is included in the goal string (format: "GOAL:#task_id"),
        the orchestrator will attempt to resume an existing task with that ID
        instead of creating a new one.
        """
        if self._goal_execution_active:
            raise RuntimeError(
                "execute_goal is already running on this orchestrator. An "
                "AgentOrchestrator runs one active goal at a time; create a "
                "separate AgentOrchestrator instance for concurrent goals."
            )
        
        # Check if user_goal contains a task_id for resume
        task_id = None
        if ":" in user_goal and user_goal.count(":") == 1:
            parts = user_goal.split(":")
            if parts[0].startswith("GOAL") or not parts[0].startswith("RESUME"):
                # Maybe it's just a goal with a colon; don't confuse with resume format
                pass
            # Check for RESUME:task_id format
            if user_goal.startswith("RESUME:"):
                task_id = user_goal.split(":", 1)[1]
        
        if task_id:
            # Attempt to resume existing task
            if task_id in self._tasks:
                self.task = self._tasks[task_id]
                # Clear interrupted flag and user input for resume
                self._interrupted = False
                self.task.required_user_input = {}
                self._emit_progress("resume", f"Resuming task {task_id}")
            else:
                # Task not found, create new
                task_id = None
        
        if not task_id:
            self.task = Task(original_goal=user_goal)
            self._tasks[self.task.task_id] = self.task
        
        self._goal_execution_active = True
        try:
            return await self._execute_goal_impl(user_goal)
        finally:
            self._goal_execution_active = False

    async def _execute_goal_impl(self, user_goal: str) -> Dict[str, Any]:
        self.task = Task(original_goal=user_goal)
        self._interrupted = False
        self._progress_log = []

        result: Dict[str, Any] = {
            "status": "processing",
            "task_id": self.task.task_id,
            "final_result": "",
            "steps_completed": 0,
        }

        self._emit_progress("goal", f"New task: {user_goal}")

        try:
            # 1. Understand the goal
            self._emit_progress("understand", "Understanding your goal...")
            await self._understand_goal(user_goal)

            # 2. Plan the work
            self._emit_progress("plan", "Planning the steps...")
            plan = await self._create_plan()
            self.task.set_plan(plan)
            self._emit_progress("planned", f"Planned {len(plan)} step(s).")

            # 3. Execute steps in loop
            if self.task.has_plan() and self.task.next_step_available():
                await self._execute_loop()

            # If interrupted mid-flow, normalize to a cancelled result
            if self._interrupted:
                self.task.transition_to(TaskState.CANCELLED)
                result["status"] = "cancelled"
                result["final_result"] = f"Interrupted: {self.task.original_goal}"
            else:
                result["status"] = self.task.current_state.name
                result["final_result"] = self._generate_final_result()

            # Drive character emotion from the terminal outcome
            self._apply_outcome_emotion(result["status"])
            result["steps_completed"] = len(self.task.completed_steps)
            result["character"] = self._get_character_state().snapshot()
            self._emit_progress("done", result["final_result"], status=result["status"])
            result["progress"] = self.progress

        except KeyboardInterrupt:
            self.task.transition_to(TaskState.CANCELLED)
            result["status"] = "cancelled"
            result["final_result"] = "Task cancelled by user."
            self._apply_outcome_emotion("cancelled")
            result["character"] = self._get_character_state().snapshot()
            self._emit_progress("cancelled", result["final_result"])
            result["progress"] = self.progress
        except Exception as error:
            # Final fallback — attempt recovery, then fail safely
            await self._handle_unexpected_error(error)
            result["status"] = "failed"
            result["final_result"] = f"I encountered an error: {str(error)[:100]}"
            self._apply_outcome_emotion("failed")
            result["character"] = self._get_character_state().snapshot()
            self._emit_progress("error", result["final_result"])
            result["progress"] = self.progress

        return result

    def _apply_outcome_emotion(self, status: str) -> None:
        """Map a terminal status to a companion emotion and notify the host."""
        state = self._get_character_state()
        # A task that finished every plan step is a successful completion even
        # though its last reported state may be VERIFYING.
        all_steps_done = (
            self.task.has_plan()
            and len(self.task.completed_steps) >= len(self.task.plan)
        ) or (not self.task.has_plan() and self.task.is_completed())

        status = (status or "").upper()
        if "FAIL" in status or "ERROR" in status:
            state.on_task_failed()
        elif "CANCEL" in status:
            state.on_task_cancelled()
        elif status == "WAITING_FOR_USER":
            state.on_task_waiting()
        elif all_steps_done:
            # A task that finished every plan step is a successful completion
            # even though its last reported state may be VERIFYING (a
            # transient state that is never promoted automatically).
            state.on_task_completed()
        # else: leave the existing emotion unchanged
        self._emit_character()

    # -----------------------------------------------------------------
    # Step 1 — Understand the user goal
    # -----------------------------------------------------------------

    async def _understand_goal(self, user_goal: str) -> None:
        """Parse and interpret the user's high-level goal."""
        if self._understand:
            result = self._understand(user_goal)
            if asyncio.iscoroutine(result):
                # Await the coroutine so a genuinely async understand
                # callback runs to completion and propagates exceptions.
                result = await result
        else:
            # Default: simple storage; real implementation passes to LLM
            self.task.original_goal = user_goal

    # -----------------------------------------------------------------
    # Step 2 — Create a plan
    # -----------------------------------------------------------------

    async def _create_plan(self) -> List[Dict[str, Any]]:
        """Generate a structured plan from the user goal."""
        if self._plan:
            raw_plan = self._plan(self.task.original_goal)
            if asyncio.iscoroutine(raw_plan):
                raw_plan = await raw_plan
            return self._normalize_plan(raw_plan)
        else:
            # Default minimal plan — the orchestrator can function
            # without a plan callback if the host provides actions directly
            return []

    @staticmethod
    def _normalize_plan(raw_plan: List[Any]) -> List[Dict[str, Any]]:
        """Normalize a raw plan into action dictionaries."""
        normalized: List[Dict[str, Any]] = []
        for i, item in enumerate(raw_plan):
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str):
                # Simple string action — try to infer type
                normalized.append({
                    "action_type": item,
                    "target": f"step_{i}",
                    "expected_result": f"Complete: {item}",
                })
            else:
                normalized.append({
                    "action_type": "open_url",
                    "target": str(item),
                    "expected_result": f"Complete: {item}",
                })
        return normalized

    # -----------------------------------------------------------------
    # Step 3 — Execute loop: EXECUTE → OBSERVE → VERIFY → NEXT STEP
    # -----------------------------------------------------------------

    async def _execute_loop(self) -> None:
        """Execute plan steps one at a time until completion or block.

        Cancellation is terminal for a task: once CANCELLED, the loop must not
        execute another action (whether surfaced through the ephemeral
        `_interrupted` flag or directly via the task's own CANCELLED state on a
        resume/re-entry path). A CANCELLED task may only be replaced by a
        documented, explicit new lifecycle on the same orchestrator.
        """
        while (
            self.task.next_step_available()
            and not self._interrupted
            and not self.task.is_failed()
            and not self.task.is_cancelled()
        ):
            # --- BLOCK ON WAITING_FOR_USER ---
            if self.task.is_waiting_for_user():
                # Call user input callback if provided, allowing host to present UI
                if self._user_input:
                    result = self._user_input(self.task, self.task.required_user_input)
                    if asyncio.iscoroutine(result):
                        result = await result
                # If still waiting after callback, exit the loop so the host
                # retains control (state persists as WAITING_FOR_USER; a host
                # can resume by clearing input and re-running).
                if self.task.is_waiting_for_user():
                    return
                # If no longer waiting, continue to normal step execution

            step_index = self.task.current_step_index()
            action_dict = self.task.plan[step_index]

            # Parse the action from the plan dict
            from avora_backend.action_model import Action as ActionClass
            action = ActionClass.from_dict(action_dict)

            # --- CONFIRMATION GATE (backend enforcement) ---
            # A HIGH-risk action (e.g. delete_file) MUST NOT execute until the
            # user has explicitly confirmed it. This check runs at the
            # orchestrator execution boundary — before the executor is invoked —
            # so it is enforced even if the frontend never surfaced a dialog.
            # LOW/MEDIUM risk behavior is preserved unchanged.
            if self._high_risk_unconfirmed(action, step_index):
                await self._request_confirmation(action, step_index)
                # Re-evaluate AFTER the request + callback. If a host action
                # (via user-input callback or a separate call) confirmed the
                # step, its metadata now carries `explicit_confirmation` and we
                # proceed to execute. If the step is STILL unconfirmed we must
                # NOT execute it — either the host declined (task will cancel),
                # left it pending (we block on WAITING_FOR_USER), or did not act.
                if self._high_risk_unconfirmed(action, step_index):
                    if not self.task.is_waiting_for_user() and not self._interrupted:
                        # Defensive: regardless of state, an unconfirmed
                        # HIGH-risk action is never executed. Block on
                        # WAITING_FOR_USER so later steps cannot race forward.
                        self.task.set_required_user_input(
                            {"type": "confirmation",
                             "prompt": f"Confirm {action.action_type.value} on {action.target}?",
                             "action_type": action.action_type.value,
                             "target": action.target,
                             "step_index": step_index,
                             "risk_level": "HIGH"})
                        try:
                            self.task.transition_to(TaskState.WAITING_FOR_USER)
                        except Exception:
                            pass
                    return
                # Resumed and confirmed: re-parse the action before executing.
                action = ActionClass.from_dict(self.task.plan[step_index])

            self._emit_progress(
                "step_start",
                f"Step {step_index + 1}/{len(self.task.plan)}: {action.action_type.value}",
                step=step_index,
                action=action.action_type.value,
            )

            # --- EXECUTE ---
            self.task.transition_to(TaskState.EXECUTING)
            self.task.set_current_step(step_index)

            # Bounded retry for execution exceptions.
            # The INITIAL attempt always runs — retry_policy bounds only the
            # additional re-executions, never the first execution itself.
            # Retries are bounded by the action's retry_policy and preserve
            # confirmation requirements (enforced inside _execute_action()),
            # cancellation, and task state.
            execution_succeeded = False
            for retry_attempt in range(1, max(action.retry_policy, 1) + 1):
                try:
                    execution_result = await self._execute_action(action)
                    execution_succeeded = True
                    break
                except Exception as error:
                    self.task.retry_count = retry_attempt
                    _bounded = max(action.retry_policy, 1)
                    self.task.add_error(
                        f"Execution error, retry {retry_attempt}/{_bounded}: {str(error)[:100]}"
                    )
                    # If cancelled during retry, stop immediately
                    if self._interrupted or self.task.is_cancelled():
                        execution_succeeded = False
                        break
                    # If this was a HIGH-risk unconfirmed action, the
                    # _execute_action method already raised RuntimeError
                    # — do not retry automatically.
                    if retry_attempt >= action.retry_policy:
                        break

            if not execution_succeeded:
                # All execution retries exhausted — the action genuinely did
                # NOT execute. Observing/verifying now could only produce an
                # untrustworthy (UNKNOWN) or fabricated outcome, so fail the
                # task truthfully instead of proceeding.
                raise RuntimeError(
                    f"Execution failed for {action.action_type.value} on "
                    f"{action.target}"
                )

            # --- BLOCK ON WAITING_FOR_USER (triggered by execution) ---
            # If the action required user input, pause here BEFORE observing/
            # verifying — otherwise the observe/verify transitions would
            # overwrite the WAITING_FOR_USER state and the loop would race past.
            if self.task.is_waiting_for_user():
                if self._user_input:
                    result = self._user_input(self.task, self.task.required_user_input)
                    if asyncio.iscoroutine(result):
                        result = await result
                # Still waiting after callback -> exit so a host can resume.
                if self.task.is_waiting_for_user():
                    return
                # Resumed: proceed to observe/verify this step below.

            # --- OBSERVE ---
            self.task.transition_to(TaskState.OBSERVING)
            observation = await self._observe_action(action, execution_result)
            self.task.add_observation(observation, step_index)

            # --- VERIFY ---
            self.task.transition_to(TaskState.VERIFYING)
            verification = await self._verify_action(action, observation)
            self._record_verification_result(step_index, verification)

            # --- CHARACTER VISIBILITY: re-raise/activate character after
            # external app launches so the mascot isn't hidden behind new windows.
            if self._character_callback and action.action_type in (
                ActionType.OPEN_APPLICATION,
                ActionType.OPEN_URL,
            ):
                # Notify the host UI that the character should be re-raised
                # after an external application/browser window opens.
                try:
                    state = self._get_character_state()
                    self._character_callback(state.snapshot())
                except Exception:
                    pass  # non-blocking; host UI handles re-raise

            if verification.status == VerificationStatus.VERIFIED_SUCCESS:
                # Success — mark step complete and move to next
                self.task.complete_step(step_index, observation)
                self.task.retry_count = 0  # reset retry on success
                self._emit_progress(
                    "step_done",
                    f"Step {step_index + 1} complete.",
                    step=step_index,
                )
                # Advance to next step for the next iteration
                next_step = step_index + 1
                if next_step < len(self.task.plan):
                    self.task.set_current_step(next_step)
            elif verification.status == VerificationStatus.VERIFIED_FAILURE:
                # Verification failed — bounded retry, then recovery.
                # A step is resolved ONLY when a retry actually succeeds and
                # verifies. If it cannot be recovered the task is FAILED and
                # the loop must NOT advance past the failed step.
                recovered = await self._handle_verification_failure(
                    action, step_index, observation
                )
                if not recovered:
                    break
                # Retry/recovery succeeded — advance to the next step
                next_step = step_index + 1
                if next_step < len(self.task.plan):
                    self.task.set_current_step(next_step)
            else:
                # UNKNOWN — the action may have executed, but the final state
                # could not be established. Never claim verified success.
                self._handle_unverifiable(action, step_index, observation)
                return

    # -----------------------------------------------------------------
    # Confirmation gate helpers — backend-enforced user confirmation for
    # HIGH-risk actions (P0 #2).
    # -----------------------------------------------------------------

    def _is_high_risk(self, action: Any) -> bool:
        """Return True if the action is classified HIGH risk and therefore
        requires explicit user confirmation before it may execute."""
        from avora_backend.action_model import RiskLevel
        try:
            return action.risk_level == RiskLevel.HIGH
        except Exception:
            return False

    def _high_risk_unconfirmed(self, action: Any, step_index: int) -> bool:
        """Return True if this HIGH-risk action is pending and has NOT yet
        been explicitly confirmed by the user.

        Mirrors the existing safety rule in `Action.validate_for_execution`
        (requires `metadata["explicit_confirmation"]` for HIGH risk) so the
        orchestrator and the action model agree on the same confirmation
        contract.
        """
        if not self._is_high_risk(action):
            return False
        if action.metadata.get("explicit_confirmation"):
            return False
        # If this step already holds a user grant on the plan, treat it as
        # confirmed (covers the same-task resume path).
        plan_meta = (self.task.plan[step_index] or {}).get("metadata", {}) or {}
        if plan_meta.get("explicit_confirmation"):
            return False
        return True

    async def _request_confirmation(self, action: Any, step_index: int) -> None:
        """Request explicit user confirmation for a HIGH-risk action.

        Records the pending action context on the task, transitions to
        WAITING_FOR_USER, and invokes the user-input callback so the host can
        present a confirmation dialog. Does NOT execute the action and does NOT
        advance past the step.

        The host resolves confirmation by calling `confirm_current_action` /
        `decline_current_action` (which also resumes the SAME step), or by
        marking `explicit_confirmation` on the step and clearing input.
        """
        self.task.set_required_user_input({
            "type": "confirmation",
            "prompt": f"Confirm {action.action_type.value} on {action.target}?",
            "action_type": action.action_type.value,
            "target": action.target,
            "step_index": step_index,
            "risk_level": "HIGH",
        })

        if self._user_input:
            result = self._user_input(self.task, self.task.required_user_input)
            if asyncio.iscoroutine(result):
                await result

    def confirm_current_action(self) -> Dict[str, Any]:
        """Explicitly confirm the currently pending HIGH-risk action.

        Marks the pending step as confirmed and clears the confirmation
        request so the loop can resume and execute the SAME action (the step
        index is preserved — the task is NOT restarted from step 0). Safe to
        call once; idempotent. Does not execute anything itself.
        """
        if self.task.has_plan():
            idx = self.task.current_step_index()
            if idx is not None and idx < len(self.task.plan) and self.task.plan[idx]:
                self.task.plan[idx].setdefault("metadata", {})
                self.task.plan[idx]["metadata"]["explicit_confirmation"] = True
        self.task.required_user_input = {}
        if self.task.is_waiting_for_user():
            self.task.transition_to(TaskState.PLANNING)
        return {"confirmed": True, "message": "Action confirmed by user."}

    def decline_current_action(self) -> Dict[str, Any]:
        """Record that the user DECLINED the pending HIGH-risk action.

        The action is NOT executed, no further actions run, and the task is
        cancelled (never falsely reported as a completed success). Returns a
        descriptive result for the host to surface.
        """
        self.task.required_user_input = {}
        self._interrupted = True
        if self.task and not self.task.is_cancelled():
            try:
                self.task.transition_to(TaskState.CANCELLED)
            except Exception:
                pass
        return {"confirmed": False, "message": "Action declined by user."}

    async def _execute_action(self, action: Action) -> Any:
        """Execute a single validated action through the execution callback.

        Enforces the HIGH-risk confirmation gate at the execution boundary —
        even if this method is called through retry, recovery, resume, or
        callback paths, the confirmation requirement cannot be bypassed.
        """
        # --- CONFIRMATION GATE (defense-in-depth) ---
        # This check runs at the execution boundary inside _execute_action
        # so it cannot be bypassed by retry, recovery, resume, or callback
        # paths that might skip the main loop's confirmation gate.
        if self._high_risk_unconfirmed(action, self.task.current_step_index() if self.task else 0):
            await self._request_confirmation(action, self.task.current_step_index() if self.task else 0)
            # Re-check after the request + callback. If still unconfirmed,
            # NEVER execute the action.
            if self._high_risk_unconfirmed(action, self.task.current_step_index() if self.task else 0):
                raise RuntimeError(
                    f"HIGH-risk action '{action.action_type.value}' requires explicit user confirmation. "
                    "Action blocked at execution boundary."
                )
        if self._execute:
            try:
                result = self._execute(action)
                return await self._dispatch_callback(result)
            except Exception as error:
                # Isolate execution errors — surface them for bounded retry/
                # recovery instead of killing the whole run.
                self.task.add_error(f"Execution error: {str(error)[:200]}")
                raise
        # No executor provided — action is validated but not executed.
        # The orchestrator can still proceed to observation/verification
        # with a mock/synthetic result for testing purposes.
        return {"status": "executed", "action": str(action)}

    async def _observe_action(self, action: Action, execution_result: Any) -> Dict[str, Any]:
        """Observe the result of an action execution."""
        if self._observe:
            try:
                result = self._observe(action, execution_result)
                return await self._dispatch_callback(result)
            except Exception:
                # Observation is best-effort — fall back to a truthful record.
                # Never fabricate success; verification inspects actual state.
                return await self._build_default_observation(action, execution_result)
        return await self._build_default_observation(action, execution_result)

    async def _build_default_observation(
        self, action: Action, execution_result: Any
    ) -> Dict[str, Any]:
        """Build a default observation WITHOUT inventing success.

        Records what the action intended and what execution actually returned.
        No `success` flag is fabricated here — nothing claims the goal was
        achieved. The verifier decides success from actual state/evidence.
        """
        # Default observation — record what the action intended
        # Optionally include screen awareness if a screen observer is set
        observation: Dict[str, Any] = {
            "action_type": action.action_type.value,
            "target": action.target,
            "execution_result": execution_result,
        }
        if self._screen_observer:
            try:
                screen_info = await self._screen_observer()
                if screen_info:
                    observation["screen_awareness"] = screen_info
            except Exception:
                pass  # Screen observation is optional, don't block
        return observation

    async def _verify_action(self, action: Action, observation: Dict[str, Any]) -> VerificationResult:
        """Verify that the action ACTUALLY achieved its expected result.

        Uses the injected `verify_callback` when provided, otherwise the
        VerificationEngine. Returns a tri-state VerificationResult:

          VERIFIED_SUCCESS — the expected final state was actually observed.
          VERIFIED_FAILURE — the observed state contradicts the expectation.
          UNKNOWN          — the action may have executed, but the final state
                             could not be established reliably. UNKNOWN is
                             NEVER converted into success.

        A custom verifier only decides the tri-state; execution success alone
        (e.g. `observation["success"]`) is evidence, NOT final verification.
        """
        if self._verify:
            try:
                result = self._verify(action, observation)
                dispatched = await self._dispatch_callback(result)
                return self._coerce_verification(dispatched)
            except Exception:
                # A failing verifier means the action is NOT verified — do not
                # fabricate success.
                return VerificationResult(
                    status=VerificationStatus.UNKNOWN,
                    error=(
                        "Verifier raised an exception; "
                        "final state could not be verified"
                    ),
                )
        return self._get_verification_engine().verify(action, observation)

    def _get_verification_engine(self) -> VerificationEngine:
        """Return the shared default VerificationEngine (created lazily)."""
        if self._default_verifier is None:
            self._default_verifier = VerificationEngine()
        return self._default_verifier

    @staticmethod
    def _coerce_verification(result: Any) -> VerificationResult:
        """Normalize a custom verifier result into a tri-state VerificationResult."""
        if isinstance(result, VerificationResult):
            return result
        if bool(result):
            return VerificationResult(status=VerificationStatus.VERIFIED_SUCCESS)
        return VerificationResult(status=VerificationStatus.VERIFIED_FAILURE)

    def _record_verification_result(
        self, step_index: int, verification: VerificationResult
    ) -> None:
        """Record a serializable verification outcome aligned with the step."""
        from datetime import datetime, timezone

        while len(self.task.verification_results) <= step_index:
            self.task.verification_results.append({})
        self.task.verification_results[step_index] = verification.to_dict()
        self.task.updated_at = datetime.now(timezone.utc)

    def _handle_unverifiable(
        self, action: Action, step_index: int, observation: Dict[str, Any]
    ) -> None:
        """Handle an action whose final state could not be established.

        The action may have executed, but AVORA cannot prove the requested
        final state. The step is NOT marked as a verified completion, the
        outcome is surfaced honestly, and the run stops so the host never
        claims definite completion without evidence.
        """
        note = (
            "Action executed, but I could not independently verify the "
            "requested final state."
        )
        self.task.add_error(f"Step {step_index + 1}: {note}")
        self._emit_progress(
            "step_unverified",
            f"Step {step_index + 1}: {note}",
            step=step_index,
        )

    # -----------------------------------------------------------------
    # Failure handling / recovery
    # -----------------------------------------------------------------

    async def _handle_verification_failure(
        self,
        action: Action,
        step_index: int,
        observation: Dict[str, Any],
    ) -> bool:
        """Handle when an action's verification fails.

        Returns True only when the step becomes genuinely complete (a retry
        re-executed the action, it was observed, and verification succeeded).
        In that case the step is marked completed and the retry counter reset.

        If every retry is exhausted (or the step cannot be recovered), the
        task transitions to FAILED and False is returned. The failed step is
        NEVER marked completed — the caller must not advance past it.
        """
        from avora_backend.action_model import Action as ActionClass

        retry_policy = ActionClass.from_dict(
            self.task.plan[step_index]
        ).retry_policy

        # Bounded retries: genuinely re-execute -> observe -> verify.
        for attempt in range(1, retry_policy + 1):
            # Cancellation is terminal — do not re-execute for a retry.
            if self._interrupted or self.task.is_cancelled():
                return False
            # --- CONFIRMATION GATE (defense-in-depth) ---
            # HIGH-risk actions must not be re-executed without explicit
            # confirmation, even during retry after verification failure.
            if self._high_risk_unconfirmed(action, step_index):
                await self._request_confirmation(action, step_index)
                # Re-check after the request + callback. If still unconfirmed,
                # do NOT retry the HIGH-risk action.
                if self._high_risk_unconfirmed(action, step_index):
                    # Host did not confirm — do not retry, proceed to exhaustion
                    break
            self.task.retry_count = attempt
            self.task.add_error(
                f"Verification failed, retry {attempt}/{retry_policy}"
            )
            retry_observation = await self._execute_loop_step_resume(
                action, step_index
            )
            # Cancellation may have been requested during the retry execution.
            if self._interrupted or self.task.is_cancelled():
                return False
            # A retry may legitimately block on user input — preserve the
            # WAITING_FOR_USER state for the host instead of failing/halting.
            if self.task.is_waiting_for_user():
                return False
            retry_verification = await self._verify_action(action, retry_observation)
            self._record_verification_result(step_index, retry_verification)
            if retry_verification.status == VerificationStatus.VERIFIED_SUCCESS:
                # Retry actually succeeded AND verified — step is complete.
                self.task.complete_step(step_index, retry_observation)
                self.task.retry_count = 0  # reset retry on success
                self._emit_progress(
                    "step_done",
                    f"Step {step_index + 1} complete.",
                    step=step_index,
                )
                return True

        # If cancelled, never overwrite the CANCELLED state with FAILED or
        # attempt recovery — a cancelled task must not execute further.
        if self._interrupted or self.task.is_cancelled():
            return False

        # Exhausted retries — try recovery
        self.task.recovery_count += 1
        self.task.add_error(f"Verification failed after {retry_policy} retries")

        if self._recovery:
            result = self._recovery(
                self.task, Exception("Verification failed after retries")
            )
            await self._dispatch_callback(result)

        # The required step never succeeded — fail the task truthfully.
        self.task.transition_to(TaskState.FAILED)
        return False

    async def _execute_loop_step_resume(self, action: Action, step_index: int) -> Dict[str, Any]:
        """Re-execute a failed step for a retry and observe the retry result.

        Mirrors the main loop's EXECUTE -> OBSERVE flow (including the
        WAITING_FOR_USER block) so a retry uses the real new observation.

        **Defense-in-depth**: enforces the HIGH-risk confirmation gate so
        that retry/resume paths cannot bypass the safety check.
        """
        # --- CONFIRMATION GATE (defense-in-depth) ---
        # HIGH-risk actions must not be re-executed without explicit
        # confirmation, even during retry/resume after verification failure.
        if self._high_risk_unconfirmed(action, step_index):
            await self._request_confirmation(action, step_index)
            # Re-parse after the request + callback if confirmation was given.
            # If still unconfirmed, the caller (retry loop) will break.
            if self._high_risk_unconfirmed(action, step_index):
                return {"success": False, "blocked": "unconfirmed_high_risk"}
        # A cancelled task must not re-execute even through the retry/resume
        # path (defense-in-depth alongside the primary loop guard).
        if self.task.is_cancelled():
            return {"success": False, "blocked": "cancelled"}
        self.task.transition_to(TaskState.EXECUTING)
        execution_result = await self._execute_action(action)

        # If cancelled/interrupted during the retry execution, stop immediately
        # and preserve the CANCELLED state (do NOT clobber it with OBSERVING/
        # VERIFYING) so the caller recognises the retry must not continue.
        if self._interrupted or self.task.is_cancelled():
            return {"success": False, "blocked": "cancelled", "cancelled": True}

        # --- BLOCK ON WAITING_FOR_USER (triggered by retry execution) ---
        # Preserve the WAITING_FOR_USER state instead of racing through
        # observe/verify, which would overwrite it.
        if self.task.is_waiting_for_user():
            if self._user_input:
                result = self._user_input(self.task, self.task.required_user_input)
                if asyncio.iscoroutine(result):
                    result = await result
            # Still waiting after callback -> leave the task waiting; the
            # caller aborts the retry loop and does not fail the task.
            if self.task.is_waiting_for_user():
                return {"success": False, "blocked": "waiting_for_user"}

        self.task.transition_to(TaskState.OBSERVING)
        observation = await self._observe_action(action, execution_result)
        self.task.add_observation(observation, step_index)
        self.task.transition_to(TaskState.VERIFYING)
        return observation

    async def _handle_unexpected_error(self, error: Exception) -> None:
        """Handle an unexpected error raised outside the normal flow.

        Records the error on the task, attempts a one-time recovery
        callback if configured, then transitions the task to FAILED.
        """
        self.task.add_error(f"Unexpected error: {str(error)[:200]}")

        if self._recovery:
            try:
                result = self._recovery(self.task, error)
                await self._dispatch_callback(result)
            except Exception:
                # Recovery itself failed — still fail safely
                pass

        try:
            self.task.transition_to(TaskState.FAILED)
        except Exception:
            # State may already be terminal; that's acceptable
            pass

    # -----------------------------------------------------------------
    # Post-verification
    # -----------------------------------------------------------------

    def _generate_final_result(self) -> str:
        """Generate a natural-language result based on task state."""
        if self.task.highest_verification_status() == VerificationStatus.UNKNOWN.name:
            # The action(s) may have executed, but AVORA could not independently
            # verify the requested final state. Prefer honesty over "Done!".
            return (
                "I completed the action(s), but I could not independently "
                f"verify the requested final state: {self.task.original_goal}"
            )
        if self.task.is_completed():
            return f"Completed: {self.task.original_goal}"
        if self.task.is_failed():
            return f"Failed to complete: {self.task.original_goal}"
        if self.task.is_cancelled():
            return f"Cancelled: {self.task.original_goal}"
        if self.task.is_waiting_for_user():
            return f"Waiting for input to continue: {self.task.original_goal}"
        return f"Task {self.task.current_state.name.lower()}: {self.task.original_goal}"

# -----------------------------------------------------------------
# Interruption / cancellation
# -----------------------------------------------------------------

    def request_interrupt(self) -> None:
        """Request the agent to stop/cancel the current task."""
        self._interrupted = True
        if self.task:
            # Preserve state — task state survives interruption
            # If currently executing, mark as cancelled
            if self.task.current_state in (
                TaskState.EXECUTING,
                TaskState.OBSERVING,
                TaskState.VERIFYING,
            ):
                self.task.transition_to(TaskState.CANCELLED)

    def is_interrupted(self) -> bool:
        return self._interrupted

    def cancel(self) -> Dict[str, Any]:
        """STOP/CANCEL — request cancellation of the current operation.

        Aligns with the AVORA task-management convention (cancel /
        is_cancelled). Sets the cancellation flag, transitions the task
        to a cancelled state when applicable, and returns a descriptive
        result for the host to surface to the user.
        """
        self._interrupted = True
        if self.task and not self.task.is_cancelled():
            try:
                self.task.transition_to(TaskState.CANCELLED)
            except Exception:
                pass
        return {
            "success": True,
            "cancelled": True,
            "message": "Task cancelled by user.",
        }

    def resume(self, task_id: str) -> Optional[Task]:
        """Resume a previously paused or waiting task by its task_id.

        Retrieves the task from the internal task store and restores it
        as the current task. The task retains all its state: plan, current
        step, completed steps, confirmation state, verification results,
        retries, errors, progress, goal, and execution context.

        Does NOT restart step 0. Safe to call multiple times.

        Returns the resumed Task, or None if no task with the given ID
        exists in the store.
        """
        task = self._tasks.get(task_id)
        if task is None:
            return None
        # Restore the task as the current task
        self.task = task
        self._interrupted = False
        # Clear user input so the loop can proceed (host controls resumption)
        self.task.required_user_input = {}
        # Transition out of WAITING_FOR_USER if stuck, allowing progression
        if self.task.is_waiting_for_user():
            try:
                self.task.transition_to(TaskState.PLANNING)
            except Exception:
                pass
        self._emit_progress("resume", f"Resumed task {task_id}")
        return self.task

    def is_cancelled(self) -> bool:
        """Return True if cancellation has been requested."""
        return self._interrupted

    def stop(self) -> Dict[str, Any]:
        """STOP command — immediate halt alias for cancel()."""
        return self.cancel()


# -----------------------------------------------------------------
# Phase 6 — User Input Manager
# -----------------------------------------------------------------

class UserInputManager:
    """
    Handles user input requirements for the agent loop.

    Supports: password, OTP, CAPTCHA, permission, confirmation,
    ambiguous choice, and missing information.

    Does NOT guess, expose, or bypass credentials.
    All credential handling is user-controlled via the host UI.
    """

    def __init__(self, task: Task, user_input_callback: Optional[Callable[[Task, Dict[str, Any]], Any]] = None):
        self.task = task
        self._user_input = user_input_callback

    # ————————————————————————————————————————————————————————
    # Password input — user provides a password for authentication
    # ————————————————————————————————————————————————————————

    def request_password(self, prompt: str = 'Enter password') -> str:
        """Request a password from the user.

        Returns a descriptive message for the host UI to display.
        The host should present a password dialog and call user_input_callback
        with the entered password.
        """
        self.task.set_required_user_input({
            'type': 'password',
            'prompt': prompt,
        })
        return f'Authentication required: {prompt}'

    # ————————————————————————————————————————————————————————
    # OTP input — one-time password / 2FA
    # ————————————————————————————————————————————————————————

    def request_otp(self, prompt: str = 'Enter OTP') -> str:
        """Request an one-time password from the user.

        Returns a descriptive message for the host UI to display.
        The host should present an OTP dialog and call user_input_callback
        with the entered OTP.
        """
        self.task.set_required_user_input({
            'type': 'otp',
            'prompt': prompt,
        })
        return f'Two-factor authentication required: {prompt}'

    # ————————————————————————————————————————————————————————
    # CAPTCHA input — user solves a CAPTCHA
    # ————————————————————————————————————————————————————————

    def request_captcha(self, prompt: str = 'Complete CAPTCHA') -> str:
        """Request CAPTCHA completion from the user.

        Returns a descriptive message for the host UI to display.
        The host should present a CAPTCHA and call user_input_callback
        when the user has solved it.
        """
        self.task.set_required_user_input({
            'type': 'captcha',
            'prompt': prompt,
        })
        return f'CAPTCHA verification required: {prompt}'

    # ————————————————————————————————————————————————————————
    # Permission input — user grants/denies permission
    # ————————————————————————————————————————————————————————

    def request_permission(self, action: str, resource: str, prompt: Optional[str] = None) -> str:
        """Request user permission for an action on a resource.

        Returns a descriptive message for the host UI to display.
        The host should present a yes/no dialog and call user_input_callback
        with the user's response.
        """
        if prompt is None:
            prompt = f'Allow {action} on {resource}?'
        self.task.set_required_user_input({
            'type': 'permission',
            'prompt': prompt,
            'action': action,
            'resource': resource,
        })
        return f'Permission required: {prompt}'

    # ————————————————————————————————————————————————————————
    # Confirmation input — yes/no confirmation
    # ————————————————————————————————————————————————————————

    def request_confirmation(self, prompt: str = 'Confirm') -> str:
        """Request yes/no confirmation from the user.

        Returns a descriptive message for the host UI to display.
        The host should present a confirmation dialog and call user_input_callback
        with True (yes) or False (no).
        """
        self.task.set_required_user_input({
            'type': 'confirmation',
            'prompt': prompt,
        })
        return f'Confirmation required: {prompt}'

    # ————————————————————————————————————————————————————————
    # Ambiguous choice — user selects from multiple options
    # ————————————————————————————————————————————————————————

    def request_choice(self, prompt: str, options: List[str]) -> str:
        """Request user choice from multiple options.

        Returns a descriptive message for the host UI to display.
        The host should present the options and call user_input_callback
        with the selected option label or index.
        """
        self.task.set_required_user_input({
            'type': 'choice',
            'prompt': prompt,
            'options': options,
        })
        return f'Choose an option: {prompt}'

    # ————————————————————————————————————————————————————————
    # Missing information — ask user for required info
    # ————————————————————————————————————————————————————————

    def request_information(self, prompt: str, field_name: str = 'information') -> str:
        """Request missing information from the user.

        Returns a descriptive message for the host UI to display.
        The host should present a input dialog and call user_input_callback
        with the provided information.
        """
        self.task.set_required_user_input({
            'type': 'information',
            'prompt': prompt,
            'field_name': field_name,
        })
        return f'Information required: {prompt}'

    # ————————————————————————————————————————————————————————
    # Clear user input — call when user has completed the task
    # ————————————————————————————————————————————————————————

    def clear_input(self) -> None:
        """Clear the required user input and reset task state."""
        self.task.clear_required_user_input()


# -----------------------------------------------------------------
# Interruption / cancellation
# -----------------------------------------------------------------

    def request_interrupt(self) -> None:
        """Request the agent to stop/cancel the current task."""
        self._interrupted = True
        if self.task:
            # Preserve state — task state survives interruption
            # If currently executing, mark as cancelled
            if self.task.current_state in (
                TaskState.EXECUTING,
                TaskState.OBSERVING,
                TaskState.VERIFYING,
            ):
                self.task.transition_to(TaskState.CANCELLED)

    def is_interrupted(self) -> bool:
        return self._interrupted


# -----------------------------------------------------------------
# Convenience: synchronous wrapper for host environments
# -----------------------------------------------------------------

class SyncAgentOrchestrator:
    """
    Synchronous wrapper for the async AgentOrchestrator.
    Adapts callback-based or threaded host environments.
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
    ):
        self.orchestrator = orchestrator

    def execute_goal_sync(self, user_goal: str) -> Dict[str, Any]:
        """Run the agent loop synchronously (blocks until complete)."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.orchestrator.execute_goal(user_goal)
        )