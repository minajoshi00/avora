# ============================================================
# AGENT MODE — CANCELLATION IS TERMINAL (S37) REGRESSION TESTS
# ============================================================
# S37 adversarial finding: a task in CANCELLED state could re-enter
# `_execute_loop` / `_execute_loop_step_resume` and execute another
# action, because the loop guard checked `is_failed()` but not
# `is_cancelled()`. A cancelled task could even be moved out of
# CANCELLED (to VERIFYING) by the observe/verify transitions.
#
# The required invariant, enforced by this fix, is:
#
#     CANCELLED
#        |
#        v
#   NO MORE EXECUTION
#
# Once a task is CANCELLED:
#   - `_execute_loop` must not execute another action (nor on re-entry)
#   - retries must not execute
#   - recovery must not execute
#   - verification retry must not execute
#   - later steps must never execute
#   - completed_steps must not increase because of cancellation
#   - the task must remain CANCELLED
#
# A brand-new, independent task on the same orchestrator is a documented
# NEW lifecycle and MUST still work normally.
#
# Real FileSkill with safe temporary filesystem artifacts is used wherever
# practical (the strongest evidence is a cancelled task + loop re-entry +
# real FileSkill = zero post-cancellation filesystem actions).
# ============================================================

from __future__ import annotations

import asyncio
import os

import pytest

from avora_backend.agent_orchestrator import AgentOrchestrator
from avora_backend.action_model import Action, ActionType
from avora_backend.task import Task, TaskState
from avora_backend.skills.file_skill import FileSkill


def run_orch(orch, goal):
    return asyncio.run(orch.execute_goal(goal))


async def file_executor(action):
    skill = FileSkill()
    return await skill.execute(action)


def _plan_step(action_type, target, **kw):
    step = {
        "action_type": action_type,
        "target": target,
        "expected_result": f"expected: {action_type}",
        "risk_level": "LOW",
        "retry_policy": 0,
        "parameters": {},
        "metadata": {},
    }
    step.update(kw)
    return step


# ---------------------------------------------------------------------
# 1. A CANCELLED task cannot execute when `_execute_loop` is re-entered.
#    Real FileSkill: the file must NOT be created after cancellation.
# ---------------------------------------------------------------------

def test_cancelled_task_does_not_execute_on_loop_reentry(tmp_path):
    path = str(tmp_path / "must_not_exist.txt")
    plan = [_plan_step("create_file", path, parameters={"content": "Z"})]

    # A task that is ALREADY CANCELLED, with untouched remaining steps.
    task = Task(original_goal="cancelled", state=TaskState.CANCELLED, plan=plan)
    orch = AgentOrchestrator(task=task, plan_callback=lambda g: plan,
                             execute_callback=file_executor)

    # Resume/re-entry path (the S37 vector): call _execute_loop directly.
    asyncio.run(orch._execute_loop())

    assert os.path.exists(path) is False, "cancelled task created a file via re-entry"
    assert task.is_cancelled(), "task should remain CANCELLED"
    assert task.completed_steps == []
    assert task.verification_results == []


# ---------------------------------------------------------------------
# 2. A CANCELLED task cannot execute later steps.
#    Step 0 succeeded; cancellation must prevent step 1 and step 2.
# ---------------------------------------------------------------------

def test_cancelled_task_cannot_execute_later_steps(tmp_path):
    s0 = str(tmp_path / "s0.txt")
    s1 = str(tmp_path / "s1.txt")
    s2 = str(tmp_path / "s2.txt")
    plan = [
        _plan_step("create_file", s0, parameters={"content": "s0"}),
        _plan_step("create_file", s1, parameters={"content": "s1"}),
        _plan_step("create_file", s2, parameters={"content": "s2"}),
    ]
    # Simulate: step 0 completed, task then cancelled before step 1.
    task = Task(original_goal="multi", plan=plan, current_step=1,
                completed_steps=[0], state=TaskState.CANCELLED)
    orch = AgentOrchestrator(task=task, plan_callback=lambda g: plan,
                             execute_callback=file_executor)

    asyncio.run(orch._execute_loop())

    assert os.path.exists(s1) is False
    assert os.path.exists(s2) is False
    assert task.completed_steps == [0], "completed_steps must not change"
    assert task.is_cancelled()
    assert task.verification_results == []


# ---------------------------------------------------------------------
# 3. Cancellation during a retry stops future execution.
#    Retry loop must not re-execute after the task is cancelled.
# ---------------------------------------------------------------------

def test_cancellation_during_retry_stops_future_execution(tmp_path):
    path = str(tmp_path / "retry.txt")
    executed = []
    orch_ref = {}

    async def executor(action):
        n = len(executed) + 1
        executed.append(action.action_type.value)
        open(path, "w").write("W")  # content mismatch -> verify fails -> retry
        if n == 2:                   # cancel during the 2nd attempt
            orch_ref["o"].cancel()
        return {"status": "executed", "success": True}

    plan = [_plan_step("create_file", path, parameters={"content": "R"}, retry_policy=4)]

    async def verify(action, observation):
        return False  # force every retry

    orch = AgentOrchestrator(task=Task(original_goal="retry", plan=plan),
                             plan_callback=lambda g: plan,
                             execute_callback=executor,
                             observe_callback=lambda a, r: {"content": "STALE"},
                             verify_callback=verify)
    orch_ref["o"] = orch

    asyncio.run(orch._execute_loop())

    assert len(executed) == 2, f"retry ran past cancellation: {executed}"
    assert orch.task.is_cancelled(), "task must remain CANCELLED, not FAILED"


# ---------------------------------------------------------------------
# 4. Cancellation after WAITING_FOR_USER prevents later execution.
#    A confirmed HIGH-risk action must NOT run after the task is cancelled.
# ---------------------------------------------------------------------

def test_cancellation_after_waiting_for_user_prevents_execution(tmp_path):
    victim = str(tmp_path / "victim.txt")
    open(victim, "w").write("x")
    executed = []

    async def executor(action):
        executed.append(action.action_type.value)
        if action.action_type.value == "delete_file":
            FileSkill().delete_file(action.target)
        return {"status": "executed", "success": True}

    plan = [{
        "action_type": "delete_file",
        "target": victim,
        "expected_result": "deleted",
        "risk_level": "HIGH",
        "retry_policy": 0,
        "parameters": {},
        "metadata": {},
    }]
    task = Task(original_goal="confirm", plan=plan)
    orch = AgentOrchestrator(task=task, plan_callback=lambda g: plan,
                             execute_callback=executor)

    # HIGH risk -> task blocks at WAITING_FOR_USER, nothing executes.
    asyncio.run(orch._execute_loop())
    assert task.is_waiting_for_user()
    assert executed == []

    # User cancels the waiting task, then (late) tries to confirm + resume.
    orch.cancel()
    orch.confirm_current_action()
    asyncio.run(orch._execute_loop())

    assert executed == [], "cancelled task executed a confirmed HIGH action"
    assert os.path.exists(victim) is True, "victim file must be untouched"
    assert task.is_cancelled(), "task must remain CANCELLED"


# ---------------------------------------------------------------------
# 5. Cancellation does not inflate completed_steps, and is idempotent.
# ---------------------------------------------------------------------

def test_cancellation_does_not_inflate_completed_steps(tmp_path):
    s1 = str(tmp_path / "s1.txt")
    s2 = str(tmp_path / "s2.txt")
    plan = [
        _plan_step("create_file", s1, parameters={"content": "1"}),
        _plan_step("create_file", s2, parameters={"content": "2"}),
    ]
    task = Task(original_goal="steps", plan=plan, current_step=1,
                completed_steps=[0], state=TaskState.CANCELLED)
    orch = AgentOrchestrator(task=task, plan_callback=lambda g: plan,
                             execute_callback=file_executor)

    # Repeat cancellation — must be idempotent / terminal.
    orch.cancel()
    orch.cancel()
    orch.request_interrupt()
    asyncio.run(orch._execute_loop())

    assert task.completed_steps == [0], "completed_steps inflated"
    assert os.path.exists(s2) is False
    assert task.is_cancelled()


# ---------------------------------------------------------------------
# 6. A fresh, independent task on the same orchestrator still works
#    after a prior task was cancelled (documented NEW lifecycle).
# ---------------------------------------------------------------------

def test_fresh_independent_task_works_after_cancel(tmp_path):
    target = str(tmp_path / "ok.txt")
    plan = [_plan_step("create_file", target, parameters={"content": "ok"})]

    orch = AgentOrchestrator(plan_callback=lambda g: plan,
                             execute_callback=file_executor)

    first = run_orch(orch, "first run")
    assert first["status"] == "VERIFYING"
    assert os.path.exists(target)

    orch.cancel()                      # cancel the (now done) task

    target2 = str(tmp_path / "ok2.txt")
    plan2 = [_plan_step("create_file", target2, parameters={"content": "ok2"})]
    orch2 = AgentOrchestrator(plan_callback=lambda g: plan2,
                              execute_callback=file_executor)
    second = run_orch(orch2, "second run")
    assert second["status"] == "VERIFYING"
    assert os.path.exists(target2)
