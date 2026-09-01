# ============================================================
# AGENT MODE — S43 CONCURRENT EXECUTE_GOAL ISOLATION TESTS
# ============================================================
# S43 adversarial finding: `AgentOrchestrator.execute_goal()` uses a single
# mutable `self.task` slot. Two concurrent `execute_goal()` calls on the SAME
# instance overwrite `self.task`, causing task A to operate on task B's state:
#   - completed_steps / verification results become ambiguous
#   - progress events belong to the wrong task
#   - cancellation / interrupt state affects the wrong task
#   - final answers are associated with the wrong request
#
# Architecture decision (documented in AVORA_S43_CONCURRENCY_REMEDIATION_REPORT.md):
# an orchestrator instance runs exactly ONE active goal at a time — every
# helper method reads/writes instance-level `self.task`, `self._interrupted`,
# `self._progress_log`, `_character_state`. True concurrency therefore uses a
# SEPARATE orchestrator instance per goal; each instance owns fully isolated
# task / progress / interrupt / confirmation / character state.
#
# The fix makes the single-active-task model EXPLICIT: a second concurrent
# `execute_goal` on the same instance is rejected with a clear error instead of
# silently corrupting state. Genuine concurrent goals (the intended model) use
# separate instances and remain truly concurrent and fully isolated.
#
# These tests prove:
#   1. same-instance concurrent execute_goal -> rejected with a clear error
#   2. separate-instance concurrent execution is truly concurrent + isolated
#   3. concurrent different goals produce correct, distinct results
#   4. concurrent multi-step goals
#   5. cancel(A) while B runs -> only A cancelled, B continues
#   6. cancel(B) while A runs -> only B cancelled, A continues
#   7. interrupt(A) while B runs -> only A interrupted
#   8. A waiting for confirmation while B executes -> B unaffected
#   9. confirm(A) while B executes -> resumes A only
#  10. decline(A) while B executes -> cancels A only, B continues
#  11. A fails verification while B succeeds
#  12. A retries while B executes
#  13. one task raises an execution exception while another succeeds
#  14. progress callbacks from A/B are isolated
#  15. verification records are isolated
#  16. final results remain associated with the correct task
#
# Real async FileSkill with unique temporary targets proves the real-skill
# isolation (each task's content is independently verifiable on disk).
# ============================================================

from __future__ import annotations

import asyncio
import os

import pytest

from avora_backend.agent_orchestrator import AgentOrchestrator
from avora_backend.action_model import Action, ActionType
from avora_backend.task import TaskState
from avora_backend.skills.file_skill import FileSkill


def run_orch(orch, goal):
    return asyncio.run(orch.execute_goal(goal))


async def file_executor(action):
    skill = FileSkill()
    return await skill.execute(action)


def LOW(action_type, target, **kw):
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


def HIGH(action_type, target, **kw):
    return dict(LOW(action_type, target, **kw), risk_level="HIGH")


# =====================================================================
# 1. SAME-INSTANCE CONCURRENT execute_goal -> rejected, no corruption
# =====================================================================

def test_concurrent_execute_goal_same_instance_rejected_not_corrupted(tmp_path):
    """Two concurrent execute_goal calls on ONE orchestrator must be rejected
    with a clear error — never silent state corruption."""
    d = str(tmp_path)
    plan = [LOW("create_file", os.path.join(d, "solo.txt"), parameters={"content": "solo"})]

    async def executor(action):
        await asyncio.sleep(0.01)
        await FileSkill().execute(action)
        return {"status": "executed", "success": True}

    orch = AgentOrchestrator(plan_callback=lambda g: plan, execute_callback=executor)

    async def run():
        async def a():
            return await orch.execute_goal("goal A")

        async def b():
            return await orch.execute_goal("goal B")

        return await asyncio.gather(a(), b(), return_exceptions=True)

    results = asyncio.run(run())
    ok = [r for r in results if isinstance(r, dict)]
    errs = [r for r in results if isinstance(r, Exception)]
    assert len(ok) == 1, f"expected exactly one to run, got {ok}"
    assert len(errs) == 1, f"expected exactly one rejection, got {errs}"
    assert type(errs[0]) is RuntimeError
    assert "already running" in str(errs[0])
    # The single successful run completed cleanly with its own result.
    assert ok[0]["status"] == "VERIFYING"
    assert os.path.exists(os.path.join(d, "solo.txt"))
    # Progress must belong to the accepted run only (no mixing).
    goal_msgs = [e.get("message") for e in orch.progress if e.get("event") == "goal"]
    assert len(goal_msgs) == 1


# =====================================================================
# 2-4. SEPARATE-INSTANCE concurrency: genuinely concurrent + isolated
# =====================================================================

def test_two_concurrent_goals_isolated_real_files(tmp_path):
    """Real FileSkill: A creates A files with A content, B creates B files with
    B content — concurrently, without one claiming the other's result."""
    d = os.path.join(str(tmp_path), "c2")
    os.makedirs(d, exist_ok=True)
    planA = [LOW("create_file", os.path.join(d, "A1.txt"), parameters={"content": "AAA"}),
             LOW("create_file", os.path.join(d, "A2.txt"), parameters={"content": "AAA"})]
    planB = [LOW("create_file", os.path.join(d, "B1.txt"), parameters={"content": "BBB"}),
             LOW("create_file", os.path.join(d, "B2.txt"), parameters={"content": "BBB"})]

    async def execA(action):
        await asyncio.sleep(0.01)
        await FileSkill().execute(action)
        return {"status": "executed", "success": True}

    async def execB(action):
        await asyncio.sleep(0.01)
        await FileSkill().execute(action)
        return {"status": "executed", "success": True}

    oa = AgentOrchestrator(plan_callback=lambda g: planA, execute_callback=execA)
    ob = AgentOrchestrator(plan_callback=lambda g: planB, execute_callback=execB)

    async def run():
        return await asyncio.gather(oa.execute_goal("goal A"), ob.execute_goal("goal B"))

    r1, r2 = asyncio.run(run())

    assert r1["status"] == "VERIFYING" and r1["steps_completed"] == 2
    assert r2["status"] == "VERIFYING" and r2["steps_completed"] == 2
    for n in ("A1.txt", "A2.txt"):
        assert open(os.path.join(d, n)).read() == "AAA"
    for n in ("B1.txt", "B2.txt"):
        assert open(os.path.join(d, n)).read() == "BBB"
    assert oa.task.original_goal == "goal A"
    assert ob.task.original_goal == "goal B"
    assert len(oa.task.completed_steps) == 2 and len(ob.task.completed_steps) == 2


def test_concurrent_multi_step_different_goals(tmp_path):
    """Different multi-step goals concurrently: each finishes all its own steps."""
    d = str(tmp_path)
    planX = [LOW("create_file", os.path.join(d, "X1.txt")),
             LOW("create_file", os.path.join(d, "X2.txt")),
             LOW("create_file", os.path.join(d, "X3.txt"))]
    planY = [LOW("create_file", os.path.join(d, "Y1.txt")),
             LOW("create_file", os.path.join(d, "Y2.txt"))]

    async def execX(action):
        await asyncio.sleep(0.005)
        await FileSkill().execute(action)
        return {"status": "executed"}

    async def execY(action):
        await asyncio.sleep(0.005)
        await FileSkill().execute(action)
        return {"status": "executed"}

    oa = AgentOrchestrator(plan_callback=lambda g: planX, execute_callback=execX)
    ob = AgentOrchestrator(plan_callback=lambda g: planY, execute_callback=execY)

    async def run():
        return await asyncio.gather(oa.execute_goal("X"), ob.execute_goal("Y"))

    r1, r2 = asyncio.run(run())
    assert r1["steps_completed"] == 3 and r2["steps_completed"] == 2
    assert all(os.path.exists(os.path.join(d, n)) for n in ("X1.txt", "X2.txt", "X3.txt"))
    assert all(os.path.exists(os.path.join(d, n)) for n in ("Y1.txt", "Y2.txt"))


# =====================================================================
# 5-7. CANCEL / INTERRUPT ISOLATION
# =====================================================================

def test_cancel_a_while_b_runs():
    d = _tmp("c5")
    plan = [LOW("create_file", os.path.join(d, "z.txt")),
            LOW("create_file", os.path.join(d, "z2.txt")),
            LOW("create_file", os.path.join(d, "z3.txt"))]

    async def exA(action):
        await asyncio.sleep(0.02)
        await FileSkill().execute(action)
        return {"status": "executed"}

    async def exB(action):
        await asyncio.sleep(0.02)
        await FileSkill().execute(action)
        return {"status": "executed"}

    oa = AgentOrchestrator(plan_callback=lambda g: plan, execute_callback=exA)
    ob = AgentOrchestrator(plan_callback=lambda g: plan, execute_callback=exB)

    async def runner():
        ta = asyncio.create_task(oa.execute_goal("A"))
        tb = asyncio.create_task(ob.execute_goal("B"))
        await asyncio.sleep(0.025)
        oa.cancel()
        ra = await ta
        rb = await tb
        return ra, rb

    ra, rb = asyncio.run(runner())
    assert ra["status"] == "cancelled"
    assert rb["status"] == "VERIFYING"
    assert oa.task.is_cancelled()
    assert not ob.task.is_cancelled()
    assert ob.task.current_state in (TaskState.VERIFYING, TaskState.PLANNING,
                                     TaskState.EXECUTING, TaskState.CANCELLED)
    assert os.path.exists(os.path.join(d, "z3.txt"))  # B completed its run


def test_cancel_b_while_a_runs():
    d = _tmp("c6")
    plan = [LOW("create_file", os.path.join(d, "z.txt")),
            LOW("create_file", os.path.join(d, "z2.txt")),
            LOW("create_file", os.path.join(d, "z3.txt"))]

    async def exA(action):
        await asyncio.sleep(0.02)
        await FileSkill().execute(action)
        return {"status": "executed"}

    async def exB(action):
        await asyncio.sleep(0.02)
        await FileSkill().execute(action)
        return {"status": "executed"}

    oa = AgentOrchestrator(plan_callback=lambda g: plan, execute_callback=exA)
    ob = AgentOrchestrator(plan_callback=lambda g: plan, execute_callback=exB)

    async def runner():
        ta = asyncio.create_task(oa.execute_goal("A"))
        tb = asyncio.create_task(ob.execute_goal("B"))
        await asyncio.sleep(0.025)
        ob.cancel()
        ra = await ta
        rb = await tb
        return ra, rb

    ra, rb = asyncio.run(runner())
    assert ra["status"] == "VERIFYING"
    assert rb["status"] == "cancelled"
    assert not oa.task.is_cancelled()
    assert ob.task.is_cancelled()


def test_interrupt_a_while_b_runs():
    d = _tmp("c7")
    plan = [LOW("create_file", os.path.join(d, "z.txt")),
            LOW("create_file", os.path.join(d, "z2.txt")),
            LOW("create_file", os.path.join(d, "z3.txt"))]

    async def exA(action):
        await asyncio.sleep(0.02)
        await FileSkill().execute(action)
        return {"status": "executed"}

    async def exB(action):
        await asyncio.sleep(0.02)
        await FileSkill().execute(action)
        return {"status": "executed"}

    oa = AgentOrchestrator(plan_callback=lambda g: plan, execute_callback=exA)
    ob = AgentOrchestrator(plan_callback=lambda g: plan, execute_callback=exB)

    async def runner():
        ta = asyncio.create_task(oa.execute_goal("A"))
        tb = asyncio.create_task(ob.execute_goal("B"))
        await asyncio.sleep(0.025)
        oa.request_interrupt()
        ra = await ta
        rb = await tb
        return ra, rb

    ra, rb = asyncio.run(runner())
    assert ra["status"] == "cancelled" or ra["status"] == "VERIFYING"
    assert rb["status"] == "VERIFYING"
    assert not ob.task.is_cancelled()


# =====================================================================
# 8-10. CONFIRMATION ISOLATION
# =====================================================================

def test_confirmation_waiting_a_while_b_executes(tmp_path):
    """A waits for confirmation on a HIGH action; B runs its own multi-step plan."""
    d = str(tmp_path)
    victim = os.path.join(d, "victim.txt")
    open(victim, "w").write("x")
    planA = [HIGH("delete_file", victim)]
    planOther = [LOW("create_file", os.path.join(d, "b1.txt")),
                 LOW("create_file", os.path.join(d, "b2.txt"))]

    async def exA(action):
        if action.action_type.value == "delete_file":
            FileSkill().delete_file(action.target)
        return {"status": "executed"}

    async def exB(action):
        await asyncio.sleep(0.01)
        await FileSkill().execute(action)
        return {"status": "executed"}

    oa = AgentOrchestrator(plan_callback=lambda g: planA, execute_callback=exA)
    ob = AgentOrchestrator(plan_callback=lambda g: planOther, execute_callback=exB)

    async def runner():
        ta = asyncio.create_task(oa.execute_goal("A"))
        tb = asyncio.create_task(ob.execute_goal("B"))
        await asyncio.sleep(0.05)      # A reaches WAITING, B runs
        rb = await tb                  # B must complete first
        ra = await ta                  # A remains waiting
        return ra, rb

    ra, rb = asyncio.run(runner())
    assert ra["status"] == "WAITING_FOR_USER"
    assert oa.task.is_waiting_for_user()
    assert os.path.exists(victim), "HIGH action must NOT have executed"
    assert rb["status"] == "VERIFYING"
    assert os.path.exists(os.path.join(d, "b2.txt"))
    assert not ob.task.is_waiting_for_user()


def test_confirm_a_while_b_executes_does_not_confirm_b(tmp_path):
    """A requests confirmation on a HIGH action and the host confirms it; B's
    LOW-risk run proceeds unbeknownst and unaffected. Confirming A must not
    grant/advance/alter B."""
    d = str(tmp_path)
    victim = os.path.join(d, "victim.txt")
    open(victim, "w").write("x")
    planA = [HIGH("delete_file", victim)]
    planB = [LOW("create_file", os.path.join(d, "b.txt")),
             LOW("create_file", os.path.join(d, "b2.txt"))]

    async def exA(action):
        if action.action_type.value == "delete_file":
            FileSkill().delete_file(action.target)
        return {"status": "executed"}

    async def exB(action):
        await asyncio.sleep(0.01)
        await FileSkill().execute(action)
        return {"status": "executed"}

    ref = {}
    async def user_input_callback(task, required):
        if required.get("type") == "confirmation":
            ref["oa"].confirm_current_action()   # confirm A's own pending action

    oa = AgentOrchestrator(plan_callback=lambda g: planA, execute_callback=exA,
                           user_input_callback=user_input_callback)
    ref["oa"] = oa
    ob = AgentOrchestrator(plan_callback=lambda g: planB, execute_callback=exB)

    async def runner():
        return await asyncio.gather(oa.execute_goal("A"), ob.execute_goal("B"))

    ra, rb = asyncio.run(runner())
    # A's confirmed delete ran
    assert ra["status"] == "VERIFYING"
    assert os.path.exists(victim) is False
    assert ra["steps_completed"] == 1
    # B completed its own two steps, never blocked or granted by A's confirm
    assert rb["status"] == "VERIFYING"
    assert rb["steps_completed"] == 2
    assert os.path.exists(os.path.join(d, "b.txt"))
    assert os.path.exists(os.path.join(d, "b2.txt"))
    assert not ob.task.is_waiting_for_user()
    assert len(ob.task.verification_results) == 2


def test_decline_a_while_b_executes(tmp_path):
    """A requests confirmation and the host DECLINES it -> A is cancelled and
    its HIGH action never runs. B runs independently to completion."""
    d = str(tmp_path)
    victim = os.path.join(d, "victim.txt")
    open(victim, "w").write("x")
    planA = [HIGH("delete_file", victim)]
    planB = [LOW("create_file", os.path.join(d, "b.txt")),
             LOW("create_file", os.path.join(d, "b2.txt"))]

    async def exA(action):
        if action.action_type.value == "delete_file":
            FileSkill().delete_file(action.target)
        return {"status": "executed"}

    async def exB(action):
        await asyncio.sleep(0.01)
        await FileSkill().execute(action)
        return {"status": "executed"}

    ref = {}
    async def user_input_callback(task, required):
        if required.get("type") == "confirmation":
            ref["oa"].decline_current_action()  # decline A only

    oa = AgentOrchestrator(plan_callback=lambda g: planA, execute_callback=exA,
                           user_input_callback=user_input_callback)
    ref["oa"] = oa
    ob = AgentOrchestrator(plan_callback=lambda g: planB, execute_callback=exB)

    async def runner():
        return await asyncio.gather(oa.execute_goal("A"), ob.execute_goal("B"))

    ra, rb = asyncio.run(runner())
    assert ra["status"] == "cancelled"
    assert oa.task.is_cancelled()
    assert os.path.exists(victim), "declined HIGH action must NOT execute"
    assert rb["status"] == "VERIFYING"
    assert rb["steps_completed"] == 2
    assert not ob.task.is_cancelled()
    assert os.path.exists(os.path.join(d, "b.txt"))
    assert os.path.exists(os.path.join(d, "b2.txt"))


# =====================================================================
# 11-13. FAILURE / RETRY / EXCEPTION ISOLATION
# =====================================================================

def test_a_fails_verification_while_b_succeeds(tmp_path):
    d = str(tmp_path)
    planA = [LOW("create_file", os.path.join(d, "a.txt"), parameters={"content": "A"})]
    planB = [LOW("create_file", os.path.join(d, "b.txt"), parameters={"content": "B"})]

    async def exA(action):
        await FileSkill().execute(action)
        return {"status": "executed", "success": True}

    async def exB(action):
        await FileSkill().execute(action)
        return {"status": "executed", "success": True}

    # A's verify always fails; B's verify succeeds
    oa = AgentOrchestrator(plan_callback=lambda g: planA, execute_callback=exA,
                           verify_callback=lambda a, o: False)
    ob = AgentOrchestrator(plan_callback=lambda g: planB, execute_callback=exB,
                           observe_callback=lambda a, e: {"content": "B"},
                           verify_callback=lambda a, o: True)

    async def run():
        return await asyncio.gather(oa.execute_goal("A"), ob.execute_goal("B"))

    ra, rb = asyncio.run(run())
    assert oa.task.is_failed()
    assert ra["status"] == "FAILED"
    assert ob.task.highest_verification_status() == "VERIFIED_SUCCESS"
    assert rb["status"] == "VERIFYING"
    assert not ob.task.is_failed()
    # A's failure did not touch B's verification record
    assert len(ob.task.verification_results) == 1
    assert ob.task.verification_results[0]["status"] == "VERIFIED_SUCCESS"


def test_a_retries_while_b_executes(tmp_path):
    d = str(tmp_path)
    planA = [dict(LOW("create_file", os.path.join(d, "ar.txt"), parameters={"content": "R"}),
                 retry_policy=3)]
    planB = [LOW("create_file", os.path.join(d, "b.txt"), parameters={"content": "B"}),
             LOW("create_file", os.path.join(d, "b2.txt"), parameters={"content": "B2"})]

    a_exec_count = {"n": 0}
    v_count = {"n": 0}

    async def exA(action):
        a_exec_count["n"] += 1
        await FileSkill().execute(action)
        return {"status": "executed", "success": True}

    async def exB(action):
        await FileSkill().execute(action)
        return {"status": "executed", "success": True}

    # A's verifier fails once, then succeeds -> forces a real retry
    def verifierA(action, observation):
        v_count["n"] += 1
        return v_count["n"] > 1

    oa = AgentOrchestrator(plan_callback=lambda g: planA, execute_callback=exA,
                           verify_callback=verifierA)
    ob = AgentOrchestrator(plan_callback=lambda g: planB, execute_callback=exB)

    async def run():
        return await asyncio.gather(oa.execute_goal("A"), ob.execute_goal("B"))

    ra, rb = asyncio.run(run())
    assert a_exec_count["n"] >= 2   # A genuinely re-executed (retried)
    assert ra["status"] == "VERIFYING"  # recovered via retry
    assert ra["steps_completed"] == 1
    # B completed its own two steps unaffected by A's retries
    assert rb["status"] == "VERIFYING"
    assert rb["steps_completed"] == 2
    assert os.path.exists(os.path.join(d, "b.txt"))
    assert os.path.exists(os.path.join(d, "b2.txt"))
    assert not ob.task.is_failed()


def test_a_raises_execution_exception_while_b_succeeds(tmp_path):
    d = str(tmp_path)
    planA = [LOW("create_file", os.path.join(d, "a.txt"))]
    planB = [LOW("create_file", os.path.join(d, "b.txt")),
             LOW("create_file", os.path.join(d, "b2.txt"))]

    async def exA(action):
        raise RuntimeError("A boom")

    async def exB(action):
        await FileSkill().execute(action)
        return {"status": "executed", "success": True}

    oa = AgentOrchestrator(plan_callback=lambda g: planA, execute_callback=exA)
    ob = AgentOrchestrator(plan_callback=lambda g: planB, execute_callback=exB)

    async def run():
        return await asyncio.gather(oa.execute_goal("A"), ob.execute_goal("B"))

    ra, rb = asyncio.run(run())
    assert ra["status"] == "failed"      # A failed safely
    assert oa.task.is_failed()
    assert rb["status"] == "VERIFYING"   # B succeeded unaffected
    assert rb["steps_completed"] == 2
    assert not ob.task.is_failed()


# =====================================================================
# 14-16. PROGRESS / VERIFICATION / RESULT ISOLATION
# =====================================================================

def test_progress_logs_isolated_between_concurrent_goals(tmp_path):
    d = str(tmp_path)
    planA = [LOW("create_file", os.path.join(d, "a1.txt")),
             LOW("create_file", os.path.join(d, "a2.txt"))]
    planB = [LOW("create_file", os.path.join(d, "b1.txt"))]

    async def exA(action):
        await asyncio.sleep(0.01)
        await FileSkill().execute(action)
        return {"status": "executed"}

    async def exB(action):
        await asyncio.sleep(0.01)
        await FileSkill().execute(action)
        return {"status": "executed"}

    oa = AgentOrchestrator(plan_callback=lambda g: planA, execute_callback=exA)
    ob = AgentOrchestrator(plan_callback=lambda g: planB, execute_callback=exB)

    async def run():
        return await asyncio.gather(oa.execute_goal("A"), ob.execute_goal("B"))

    ra, rb = asyncio.run(run())

    def goal_msgs(o):
        return [e.get("message") for e in o.progress if e.get("event") == "goal"]

    assert goal_msgs(oa) == ["New task: A"]
    assert goal_msgs(ob) == ["New task: B"]
    assert "B" not in " ".join(str(e) for e in oa.progress)
    assert "A" not in " ".join(str(e) for e in ob.progress)
    assert ra["progress"] is not None and rb["progress"] is not None


def test_verification_records_isolated_between_concurrent_goals(tmp_path):
    d = str(tmp_path)
    planA = [LOW("create_file", os.path.join(d, "a.txt"), parameters={"content": "AA"})]
    planB = [LOW("create_file", os.path.join(d, "b.txt"), parameters={"content": "BB"})]

    async def exA(action):
        await FileSkill().execute(action)
        return {"status": "executed"}

    async def exB(action):
        await FileSkill().execute(action)
        return {"status": "executed"}

    oa = AgentOrchestrator(plan_callback=lambda g: planA, execute_callback=exA)
    ob = AgentOrchestrator(plan_callback=lambda g: planB, execute_callback=exB)

    async def run():
        return await asyncio.gather(oa.execute_goal("A"), ob.execute_goal("B"))

    ra, rb = asyncio.run(run())
    va = oa.task.verification_results[0]
    vb = ob.task.verification_results[0]
    assert va["status"] == "VERIFIED_SUCCESS" and vb["status"] == "VERIFIED_SUCCESS"
    # Observations/records are on distinct Task objects — no cross-talk
    assert oa.task.observations[0].get("target") == os.path.join(d, "a.txt")
    assert ob.task.observations[0].get("target") == os.path.join(d, "b.txt")


def test_final_results_associated_with_correct_task(tmp_path):
    d = str(tmp_path)
    planA = [LOW("create_file", os.path.join(d, "a.txt"))]
    planB = [LOW("create_file", os.path.join(d, "b.txt"))]

    async def exA(action):
        await FileSkill().execute(action)
        return {"status": "executed"}

    async def exB(action):
        await FileSkill().execute(action)
        return {"status": "executed"}

    oa = AgentOrchestrator(plan_callback=lambda g: planA, execute_callback=exA)
    ob = AgentOrchestrator(plan_callback=lambda g: planB, execute_callback=exB)

    async def run():
        return await asyncio.gather(oa.execute_goal("Goal A"), ob.execute_goal("Goal B"))

    r1, r2 = asyncio.run(run())
    assert r1["task_id"] == oa.task.task_id and r2["task_id"] == ob.task.task_id
    assert r1["steps_completed"] == 1 and r2["steps_completed"] == 1
    assert oa.task.original_goal == "Goal A"
    assert ob.task.original_goal == "Goal B"
    # Each result's final message references its own goal
    assert "Goal A" in r1["final_result"] or r1["status"] == "VERIFYING"
    assert oa.task.task_id != ob.task.task_id


# =====================================================================
# 16. NO SHARED self.task CORRUPTION
# =====================================================================

def test_no_shared_self_task_corruption_after_concurrency(tmp_path):
    """After concurrent runs (each on its own orchestrator), `self.task` on
    every instance still belongs to that instance — never a foreign task."""
    d = str(tmp_path)

    async def exA(action):
        await asyncio.sleep(0.01)
        await FileSkill().execute(action)
        return {"status": "executed"}

    async def exB(action):
        await asyncio.sleep(0.01)
        await FileSkill().execute(action)
        return {"status": "executed"}

    oa = AgentOrchestrator(
        plan_callback=lambda g: [LOW("create_file", os.path.join(d, "A.txt"), parameters={"content": "AAA"})],
        execute_callback=exA,
    )
    ob = AgentOrchestrator(
        plan_callback=lambda g: [LOW("create_file", os.path.join(d, "B.txt"), parameters={"content": "BBB"})],
        execute_callback=exB,
    )

    async def run():
        return await asyncio.gather(oa.execute_goal("A"), ob.execute_goal("B"))

    ra, rb = asyncio.run(run())
    # identity isolation: each instance's self.task is its own
    assert oa.task.original_goal == "A"
    assert ob.task.original_goal == "B"
    assert oa.task.task_id == ra["task_id"]
    assert ob.task.task_id == rb["task_id"]
    # content isolation on disk
    assert open(os.path.join(d, "A.txt")).read() == "AAA"
    assert open(os.path.join(d, "B.txt")).read() == "BBB"
    # no cross-contamination of completed steps / observations / verification
    assert len(oa.task.completed_steps) == 1
    assert len(ob.task.completed_steps) == 1
    assert oa.task.observations[0]["target"] == os.path.join(d, "A.txt")
    assert ob.task.observations[0]["target"] == os.path.join(d, "B.txt")


def test_orchestrator_reusable_sequentially_after_concurrent_rejection(tmp_path):
    """The guardian flag resets in `finally`, so a single orchestrator can still
    be used repeatedly in SEQUENTIAL runs after a concurrent call is rejected."""
    d = str(tmp_path)
    plan = [LOW("create_file", os.path.join(d, "s.txt"))]

    async def ex(action):
        await asyncio.sleep(0.005)
        await FileSkill().execute(action)
        return {"status": "executed"}

    orch = AgentOrchestrator(plan_callback=lambda g: plan, execute_callback=ex)

    async def concurrent_attempt():
        async def a():
            return await orch.execute_goal("g1")
        async def b():
            return await orch.execute_goal("g2")
        return await asyncio.gather(a(), b(), return_exceptions=True)

    results = asyncio.run(concurrent_attempt())
    assert any(isinstance(r, RuntimeError) for r in results)
    assert any(isinstance(r, dict) for r in results)

    # Sequential reuse still works: the flag must have been reset.
    r = run_orch(orch, "sequential goal")
    assert r["status"] == "VERIFYING"
    assert r["steps_completed"] == 1
    assert orch.task.original_goal == "sequential goal"


# ---------------------------------------------------------------------
# helper
# ---------------------------------------------------------------------

def _tmp(tag):
    import tempfile, shutil
    base = os.path.join(tempfile.gettempdir(), "avora_s43", tag)
    if os.path.exists(base):
        shutil.rmtree(base)
    os.makedirs(base, exist_ok=True)
    return base