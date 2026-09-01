# ============================================================
# P0 #3 REMEDIATION — SILENT FAILED-STEP / FALSE SUCCESS
# REGRESSION TESTS
# ============================================================
# Adversarial QA: a multi-step task with a failing step could advance
# past the failed step even though the retry never succeeded, ending in
# a success-adjacent state (VERIFYING, recovery_count=0, errors=[]) and
# could even inflate `completed_steps`.
#
# Required semantics enforced here:
#   - A step is completed ONLY when it actually succeeds AND verifies.
#   - A failed step must NEVER be skipped, counted as completed, or
#     advance later steps.
#   - After retry exhaustion the task MUST be FAILED and truthfully
#     reported as failed.
#   - Retries re-execute -> observe -> verify (bounded).
# ============================================================

from __future__ import annotations

import asyncio

from avora_backend.agent_orchestrator import AgentOrchestrator
from avora_backend.task import TaskState


def run_orch(orch: AgentOrchestrator, goal: str) -> dict:
    """Blocking helper that runs the async orchestrator to completion."""
    return asyncio.run(orch.execute_goal(goal))


def _plan_for(goal: str) -> list:
    if goal == "fail_middle":
        return [
            {"action_type": "open_url", "target": "s0.com", "expected_result": "opened"},
            {"action_type": "open_url", "target": "s1.com", "expected_result": "opened", "retry_policy": 1},
            {"action_type": "click", "target": "s2", "expected_result": "clicked"},
        ]
    if goal == "retry_succeeds":
        return [
            {"action_type": "open_url", "target": "s0.com", "expected_result": "opened"},
            {"action_type": "open_url", "target": "fails-once.com", "expected_result": "opened", "retry_policy": 1},
            {"action_type": "open_url", "target": "s2.com", "expected_result": "opened"},
        ]
    if goal == "retry_exhaust":
        return [
            {"action_type": "open_url", "target": "s0.com", "expected_result": "opened"},
            {"action_type": "open_url", "target": "always-fails.com", "expected_result": "opened", "retry_policy": 3},
            {"action_type": "open_url", "target": "s2.com", "expected_result": "opened"},
        ]
    if goal == "exec_boom":
        return [
            {"action_type": "open_url", "target": "s0.com", "expected_result": "opened"},
            {"action_type": "open_url", "target": "boom.com", "expected_result": "opened"},
            {"action_type": "open_url", "target": "s2.com", "expected_result": "opened"},
        ]
    if goal == "mixed_accuracy":
        return [
            {"action_type": "open_url", "target": "ok.com", "expected_result": "opened"},
            {"action_type": "open_url", "target": "bad.com", "expected_result": "opened"},
            {"action_type": "open_url", "target": "tail.com", "expected_result": "opened"},
        ]
    if goal == "false_success_qa":
        return [
            {"action_type": "open_url", "target": "https://a.com", "expected_result": "opened"},
            {"action_type": "open_url", "target": "https://b.com", "expected_result": "opened", "retry_policy": 1},
            {"action_type": "click", "target": "btn", "expected_result": "clicked"},
        ]
    return []


def _executor(action) -> dict:
    return {"status": "executed", "target": action.target}


# ---------------------------------------------------------------------
# Test 1 — A failed step cannot be skipped; later steps do not run.
# ---------------------------------------------------------------------

def test_failed_step_cannot_be_skipped_and_later_steps_blocked():
    executed = []

    def tracker(action):
        executed.append(action.target)
        return {"status": "executed"}

    # Step index 1 (s1.com) fails verification every time.
    def verify(action, observation):
        if action.target == "s1.com":
            return False
        return True

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_for("fail_middle"),
        execute_callback=tracker,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=verify,
    )
    result = run_orch(orch, "fail_middle")

    assert result["status"] == "FAILED"
    assert orch.task.is_failed()
    assert not orch.task.is_completed()
    assert orch.task.completed_steps == [0]
    assert result["steps_completed"] == 1
    # Step 3 (s2) must NOT execute after the unrecoverable failure.
    assert "s2" not in executed
    # The failed step executed initially, then exactly one retry, no more.
    assert executed.count("s1.com") == 2


# ---------------------------------------------------------------------
# Test 2 — A retry that succeeds completes the step and the task continues.
# ---------------------------------------------------------------------

def test_retry_succeeds_then_step_counts_as_completed_and_flow_continues():
    executed = []
    verify_counts = {"fails_once": 0, "total": 0}

    def tracker(action):
        executed.append(action.target)
        return {"status": "executed", "target": action.target}

    def observe(action, execution_result):
        return {"success": True, "target": action.target}

    def verify(action, observation):
        verify_counts["total"] += 1
        if action.target == "fails-once.com":
            n = verify_counts["fails_once"]
            verify_counts["fails_once"] = n + 1
            # First attempt fails; the retry (re-executed step) succeeds.
            return n >= 1
        return True

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_for("retry_succeeds"),
        execute_callback=tracker,
        observe_callback=observe,
        verify_callback=verify,
    )
    result = run_orch(orch, "retry_succeeds")

    # Step 2 (fails-once.com) genuinely completed via retry -> step 3 ran.
    assert executed == ["s0.com", "fails-once.com", "fails-once.com", "s2.com"]
    assert orch.task.completed_steps == [0, 1, 2]
    assert result["steps_completed"] == 3
    assert orch.task.retry_count == 0  # reset after a verified success
    assert verify_counts["fails_once"] == 2
    assert not orch.task.is_failed()
    assert result["status"] == "VERIFYING"  # full loop completed normally


# ---------------------------------------------------------------------
# Test 3 — Retry exhaustion fails the task; bounded, no false success.
# ---------------------------------------------------------------------

def test_retry_exhaustion_fails_task_bounded_and_blocks_later_steps():
    executed = []
    retry_errors = []

    def tracker(action):
        executed.append(action.target)
        return {"status": "executed"}

    def verify(action, observation):
        if action.target == "always-fails.com":
            return False
        return True

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_for("retry_exhaust"),
        execute_callback=tracker,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=verify,
        recovery_callback=lambda t, e: None,
    )
    result = run_orch(orch, "retry_exhaust")

    # Exactly retry_policy=3 retries were attempted, then recovery.
    retry_errors = [e for e in orch.task.errors if "retry" in e]
    assert len(retry_errors) == 3
    assert orch.task.recovery_count == 1
    assert any("failed after" in e for e in orch.task.errors)

    # Bounded: initial attempt + 3 retries for the failing step, then STOP.
    assert executed.count("always-fails.com") == 4
    assert "s2.com" not in executed  # later steps must NOT run

    # The failed step is NOT counted as completed — no inflation, no success.
    assert orch.task.completed_steps == [0]
    assert result["steps_completed"] == 1
    assert orch.task.is_failed()
    assert result["status"] == "FAILED"
    assert not orch.task.is_completed()


# ---------------------------------------------------------------------
# Test 4 — An execution exception is recorded, not completed, not success.
# ---------------------------------------------------------------------

def test_execution_exception_recorded_not_completed_not_success():
    executed = []

    def tracker(action):
        executed.append(action.target)
        if action.target == "boom.com":
            raise ValueError("controlled boom")
        return {"status": "executed"}

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_for("exec_boom"),
        execute_callback=tracker,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "exec_boom")

    # Recorded and surfaced as a real failure.
    assert any("controlled boom" in e for e in orch.task.errors)
    assert any("Execution error" in e for e in orch.task.errors)
    assert result["status"] == "failed"
    assert orch.task.is_failed()
    assert not orch.task.is_completed()
    # The failed step was never marked completed; later steps never ran.
    assert orch.task.completed_steps == [0]
    assert "s2.com" not in executed


# ---------------------------------------------------------------------
# Test 5 — completed_steps reflects ONLY genuinely completed/verified steps.
# ---------------------------------------------------------------------

def test_completed_steps_accuracy_success_fail_success():
    executed = []

    def tracker(action):
        executed.append(action.target)
        return {"status": "executed"}

    # Explicit verifier scored from observations: "bad.com" reports failure.
    def observe(action, execution_result):
        return {"success": action.target != "bad.com", "target": action.target}

    def verify(action, observation):
        return bool(observation.get("success"))

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_for("mixed_accuracy"),
        execute_callback=tracker,
        observe_callback=observe,
        verify_callback=verify,
    )
    result = run_orch(orch, "mixed_accuracy")

    # Only step 0 genuinely completed; the failing middle step never inflated
    # the counter and the trailing "SUCCESS" step never executed.
    assert executed == ["ok.com", "bad.com"]
    assert orch.task.completed_steps == [0]
    assert result["steps_completed"] == 1
    assert orch.task.is_failed()
    assert result["status"] == "FAILED"


# ---------------------------------------------------------------------
# Test 6 — Exact adversarial QA scenario: corrected to a truthful failure.
# ---------------------------------------------------------------------
# Before the fix the result was effectively `VERIFYING / recovery_count=0 /
# errors=[]` with the last step executed even though a required step failed.
# The corrected result must explicitly indicate the task failed.

def test_false_success_regression_explicit_failure():
    executed = []

    def tracker(action):
        executed.append(action.target)
        return {"status": "executed"}

    # P0 #4 change: the DEFAULT verifier no longer treats an observation with
    # `success=True` as proof for an open_url action (there is no page/url
    # evidence). Its contract changed to truthful state-based verification.
    # This P0 #3 test targets FAILED-STEP handling, so — like its sibling
    # tests — it wires an explicit verifier: the middle step's requested
    # final state genuinely fails verification, the others succeed.
    def verify(action, observation):
        return action.target != "https://b.com"

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_for("false_success_qa"),
        execute_callback=tracker,
        observe_callback=lambda a, r: {"success": a.target != "https://b.com"},
        verify_callback=verify,
    )
    result = run_orch(orch, "false_success_qa")

    # Step 3 must NOT have executed after the failed required step.
    assert executed == ["https://a.com", "https://b.com", "https://b.com"]

    # Task is truthfully FAILED — never success/success-adjacent.
    assert result["status"] == "FAILED"
    assert orch.task.is_failed()
    assert not orch.task.is_completed()
    assert orch.task.completed_steps == [0]
    assert result["steps_completed"] == 1
    # Recovery was exercised once after retry exhaustion.
    assert orch.task.recovery_count == 1
    assert orch.task.errors  # failure reasons retained
    assert any("failed after" in e for e in orch.task.errors)
    # The user-facing result explicitly says the task failed.
    assert "Failed to complete" in result["final_result"]
    assert "Task verifying" not in result["final_result"]