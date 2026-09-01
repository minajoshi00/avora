# ============================================================
# AGENT MODE — ASYNC DISPATCH REGRESSION TESTS
# ============================================================
# P0 #1 remediation: `_dispatch_callback` previously used
# `asyncio.ensure_future(coro).result()`, which raised
# `InvalidStateError: Result is not set` for genuinely async
# callbacks (all real skills are async). These tests prove:
#
#   1. a real async callback executes successfully
#   2. the async callback's actual return value reaches the orchestrator
#   3. an exception raised by an async callback is handled correctly
#   4. existing synchronous callbacks still work
#   5. a real FileSkill.execute integration path works (async, real)
#   6. a safe/testable WindowsSkill.execute integration path works (async)
#
# The async callbacks here are genuine async functions — NOT sync mocks.
# ============================================================

from __future__ import annotations

import asyncio
import os

import pytest

from avora_backend.agent_orchestrator import AgentOrchestrator
from avora_backend.action_model import Action, ActionType
from avora_backend.skills.file_skill import FileSkill
from avora_backend.skills.windows_skill import WindowsSkill


def run_orch(orch, goal):
    return asyncio.run(orch.execute_goal(goal))


# ---------------------------------------------------------------------
# Test 1: A real async callback executes successfully
# ---------------------------------------------------------------------

def test_async_execute_callback_executes_successfully():
    executed = []

    async def async_execute(action):
        # genuinely async: yields control, e.g. like a real skill would
        await asyncio.sleep(0)
        executed.append(action.action_type.value)
        return {"status": "executed", "success": True}

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "https://example.com", "expected_result": "opened"},
        ],
        execute_callback=async_execute,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "open")

    assert result["status"] == "VERIFYING"
    assert result["steps_completed"] == 1
    assert orch.task.errors == []
    assert executed == ["open_url"]


# ---------------------------------------------------------------------
# Test 2: The async callback's actual return value reaches the orchestrator
# ---------------------------------------------------------------------

def test_async_callback_return_value_reaches_orchestrator():
    # The executor returns a value that the OBSERVE callback must actually
    # receive; if async dispatch lost the value, observation would see None.
    seen = {}

    async def async_execute(action):
        await asyncio.sleep(0)
        return {"status": "executed", "magic": "SENTINEL_73921"}

    async def async_observe(action, execution_result):
        seen["got"] = execution_result.get("magic") if execution_result else None
        await asyncio.sleep(0)
        return {"success": True, "magic": seen["got"]}

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "x", "expected_result": "opened"},
        ],
        execute_callback=async_execute,
        observe_callback=async_observe,
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "v")

    # The executor's actual return value must have propagated to observe.
    assert seen["got"] == "SENTINEL_73921"
    assert result["steps_completed"] == 1
    assert orch.task.observations[0]["magic"] == "SENTINEL_73921"


# ---------------------------------------------------------------------
# Test 3: An exception raised by the async callback is handled correctly
# ---------------------------------------------------------------------

def test_async_callback_exception_is_handled():
    async def async_execute(action):
        await asyncio.sleep(0)
        raise RuntimeError("async boom")

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "x", "expected_result": "opened"},
        ],
        execute_callback=async_execute,
        recovery_callback=lambda t, e: None,
    )
    result = run_orch(orch, "boom")

    # The async exception must NOT crash, and must not produce a fake success.
    assert result["status"] == "failed"
    assert not orch.task.is_completed()
    assert any("boom" in e or "Execution error" in e for e in orch.task.errors)


# ---------------------------------------------------------------------
# Test 4: Existing synchronous callbacks still work
# ---------------------------------------------------------------------

def test_synchronous_callback_still_works():
    executed = []

    def sync_execute(action):
        executed.append(action.action_type.value)
        return {"status": "executed"}

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "x", "expected_result": "opened"},
            {"action_type": "click", "target": "btn", "expected_result": "clicked"},
        ],
        execute_callback=sync_execute,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "sync")
    assert result["steps_completed"] == 2
    assert executed == ["open_url", "click"]


# ---------------------------------------------------------------------
# Test 5: Real FileSkill.execute integration path works (async)
# ---------------------------------------------------------------------

def test_real_file_skill_async_integration(tmp_path):
    target = str(tmp_path / "async_folder")

    async def async_file_execute(action):
        skill = FileSkill()
        return await skill.execute(action)

    def verify(action, observation):
        return os.path.isdir(target)

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "create_folder", "target": target,
             "expected_result": "folder exists", "retry_policy": 1},
        ],
        execute_callback=async_file_execute,
        verify_callback=verify,
    )
    result = run_orch(orch, "create folder")

    assert result["status"] == "VERIFYING"
    assert result["steps_completed"] == 1
    assert orch.task.errors == []
    assert os.path.isdir(target)


# ---------------------------------------------------------------------
# Test 6: Safe/testable WindowsSkill.execute integration path (async)
# ---------------------------------------------------------------------

def test_real_windows_skill_async_integration_safe_path():
    captured = {}

    async def async_win_execute(action):
        skill = WindowsSkill()
        return await skill.execute(action)

    def observe(action, execution_result):
        captured["execution_result"] = execution_result
        return {"success": True}

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            # GET_PROCESS_LIST is safe and non-destructive.
            {"action_type": "get_process_list", "target": "", "expected_result": "list"},
        ],
        execute_callback=async_win_execute,
        observe_callback=observe,
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "list processes")

    assert result["status"] == "VERIFYING"
    assert result["steps_completed"] == 1
    assert orch.task.errors == []
    assert captured["execution_result"] is not None
    # The real WindowsSkill returned its process list through the async path.
    assert captured["execution_result"].get("success") is True
    assert "applications" in captured["execution_result"]
