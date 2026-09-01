# ============================================================
# AGENT MODE — HIGH-RISK CONFIRMATION GATE REGRESSION TESTS
# ============================================================
# P0 #2 remediation: a HIGH-risk action (e.g. delete_file) must
# NOT execute without explicit user confirmation. The check runs
# at the orchestrator execution boundary (backend), so it holds
# even if the frontend never surfaced a dialog.
#
# These tests prove:
#   1. HIGH-risk action without confirmation -> NOT executed,
#      task enters WAITING_FOR_USER, confirmation requested
#   2. HIGH-risk action with explicit confirmation -> executes
#      exactly once, normal observe/verify path follows
#   3. User declines confirmation -> action NOT executed, no
#      false success, task cancelled
#   4. LOW-risk action -> no confirmation, executes normally
#   5. WAITING_FOR_USER cannot execute later steps pre-confirm
#   6. Confirmation + resume does NOT restart the task from step 0
#   7. A confirmed HIGH-risk action that fails is reported as a
#      real failure, never a false success
#
# Only safe temporary test artifacts are used (never real files).
# ============================================================

from __future__ import annotations

import asyncio

import pytest

from avora_backend.agent_orchestrator import AgentOrchestrator
from avora_backend.action_model import Action, ActionType
from avora_backend.task import TaskState


def run_orch(orch, goal):
    return asyncio.run(orch.execute_goal(goal))


def HIGH(action_type="delete_file", target="do-not-delete.txt"):
    """A HIGH-risk plan action WITHOUT explicit confirmation."""
    return {
        "action_type": action_type,
        "target": target,
        "expected_result": "Confirmed deletion completed",
        "risk_level": "HIGH",
    }


def LOW(action_type="open_url", target="https://example.com"):
    return {
        "action_type": action_type,
        "target": target,
        "expected_result": "ok",
        "risk_level": "LOW",
    }


# ---------------------------------------------------------------------
# Test 1: HIGH-risk without confirmation -> NOT executed, WAITING_FOR_USER
# ---------------------------------------------------------------------

def test_high_risk_without_confirmation_does_not_execute_and_waits():
    executed = []
    requests = []

    def executor(action):
        executed.append(action.action_type.value)
        return {"success": True}

    # Callback NEVER confirms -> keeps the task waiting for user input.
    async def user_input_callback(task, required):
        requests.append(dict(required))
        # Intentionally do NOT clear input / do NOT confirm.

    orch = AgentOrchestrator(
        plan_callback=lambda g: [HIGH()],
        execute_callback=executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
        user_input_callback=user_input_callback,
    )

    result = run_orch(orch, "delete the file")

    # The HIGH-risk action was NEVER dispatched to the executor.
    assert executed == []
    assert "delete_file" not in executed
    # A confirmation request was made.
    assert len(requests) == 1
    assert requests[0]["type"] == "confirmation"
    assert requests[0]["action_type"] == "delete_file"
    # The task is waiting for user input, not silently complete.
    assert orch.task.is_waiting_for_user()
    assert orch.task.current_state == TaskState.WAITING_FOR_USER
    assert result["status"] == "WAITING_FOR_USER"
    assert result["steps_completed"] == 0


# ---------------------------------------------------------------------
# Test 2: HIGH-risk with explicit confirmation -> executes exactly once
# ---------------------------------------------------------------------

def test_high_risk_with_explicit_confirmation_executes_once():
    executed = []
    observed = []
    verified = []
    ref = {}

    def executor(action):
        executed.append(action.action_type.value)
        return {"success": True}

    def observer(action, execution_result):
        observed.append(action.action_type.value)
        return {"success": True}

    def verifier(action, observation):
        verified.append(action.action_type.value)
        return True

    # Host presents a dialog; user confirms -> resume the SAME step.
    async def user_input_callback(task, required):
        if required.get("type") == "confirmation":
            ref["orch"].confirm_current_action()

    orch = AgentOrchestrator(
        plan_callback=lambda g: [HIGH()],
        execute_callback=executor,
        observe_callback=observer,
        verify_callback=verifier,
        user_input_callback=user_input_callback,
    )
    ref["orch"] = orch

    result = run_orch(orch, "delete the file")

    # Executed exactly once (no duplicate), then observe/verify followed.
    assert executed == ["delete_file"]
    assert observed == ["delete_file"]
    assert verified == ["delete_file"]
    assert result["status"] == "VERIFYING"
    assert result["steps_completed"] == 1


# ---------------------------------------------------------------------
# Test 3: User declines confirmation -> NOT executed, task cancelled
# ---------------------------------------------------------------------

def test_user_declines_confirmation_does_not_execute_and_cancels():
    executed = []

    def executor(action):
        executed.append(action.action_type.value)
        return {"success": True}

    async def user_input_callback(task, required):
        if required.get("type") == "confirmation":
            ref["orch"].decline_current_action()

    ref = {}
    orch = AgentOrchestrator(
        plan_callback=lambda g: [HIGH()],
        execute_callback=executor,
        user_input_callback=user_input_callback,
    )
    ref["orch"] = orch

    result = run_orch(orch, "delete the file")

    # The HIGH-risk action was never executed.
    assert executed == []
    # The task was NOT falsely reported as a success.
    assert result["status"] == "cancelled"
    assert orch.task.is_cancelled()
    assert result["steps_completed"] == 0
    assert "completed" not in result["status"]


# ---------------------------------------------------------------------
# Test 4: LOW-risk action -> no confirmation, executes normally
# ---------------------------------------------------------------------

def test_low_risk_action_executes_without_confirmation():
    executed = []
    requests = []

    def executor(action):
        executed.append(action.action_type.value)
        return {"success": True}

    async def user_input_callback(task, required):
        requests.append(dict(required))

    orch = AgentOrchestrator(
        plan_callback=lambda g: [LOW("open_url", "https://example.com")],
        execute_callback=executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
        user_input_callback=user_input_callback,
    )

    result = run_orch(orch, "open a website")

    assert executed == ["open_url"]
    # No unnecessary confirmation was requested for a LOW-risk action.
    assert requests == []
    assert result["steps_completed"] == 1


# ---------------------------------------------------------------------
# Test 5: WAITING_FOR_USER blocks later steps before confirmation
# ---------------------------------------------------------------------

def test_waiting_for_user_blocks_later_steps_before_confirmation():
    executed = []

    def executor(action):
        executed.append(action.action_type.value)
        return {"success": True}

    # Multi-step: HIGH delete first, then a LOW open_url.
    plan = [HIGH(), LOW("open_url", "https://second.example.com")]

    async def user_input_callback(task, required):
        # Never confirm -> stays waiting. No later step may run.
        pass

    orch = AgentOrchestrator(
        plan_callback=lambda g: plan,
        execute_callback=executor,
        user_input_callback=user_input_callback,
    )

    result = run_orch(orch, "delete then open site")

    # NOTHING executed: the HIGH step was blocked AND the later LOW step
    # was never reached while waiting.
    assert executed == []
    assert result["steps_completed"] == 0
    assert orch.task.is_waiting_for_user()
    assert result["status"] == "WAITING_FOR_USER"


# ---------------------------------------------------------------------
# Test 6: Confirmation + resume does NOT restart the task from step 0
# ---------------------------------------------------------------------

def test_confirmation_resume_does_not_restart_task_from_step_zero():
    executed = []

    def executor(action):
        executed.append(action.action_type.value)
        return {"success": True}

    # Step 0 = HIGH delete, step 1 = LOW open_url.
    plan = [HIGH("delete_file", "victim.txt"), LOW("open_url", "https://after.example.com")]

    async def user_input_callback(task, required):
        if required.get("type") == "confirmation" and required.get("step_index") == 0:
            ref["orch"].confirm_current_action()

    ref = {}
    orch = AgentOrchestrator(
        plan_callback=lambda g: plan,
        execute_callback=executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
        user_input_callback=user_input_callback,
    )
    ref["orch"] = orch

    result = run_orch(orch, "delete then open")

    # Both steps ran IN ORDER. The delete was confirmed and executed
    # exactly ONCE (no duplicate / no restart from step 0 re-running it).
    assert executed == ["delete_file", "open_url"]
    assert executed.count("delete_file") == 1
    assert result["steps_completed"] == 2


# ---------------------------------------------------------------------
# Test 7: Confirmed HIGH-risk action that fails => real failure, not success
# ---------------------------------------------------------------------

def test_confirmed_high_risk_that_fails_is_reported_as_real_failure():
    executed = []

    def executor(action):
        executed.append(action.action_type.value)
        return {"success": True}

    async def user_input_callback(task, required):
        if required.get("type") == "confirmation":
            ref["orch"].confirm_current_action()

    ref = {}
    orch = AgentOrchestrator(
        plan_callback=lambda g: [HIGH()],
        execute_callback=executor,
        observe_callback=lambda a, r: {"success": False},  # action did NOT achieve result
        verify_callback=lambda a, o: False,                # verification fails
        user_input_callback=user_input_callback,
    )
    ref["orch"] = orch

    result = run_orch(orch, "delete the file")

    # The confirmed action DID run, but the task must NOT report success.
    assert "delete_file" in executed
    assert result["status"] == "FAILED"
    assert "STEP_COMPLETE" not in result.get("status", "")
    # It reached the failure path, not a success-completion path.
    assert orch.task.current_state == TaskState.FAILED
