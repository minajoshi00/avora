# ============================================================
# P0 #4 REMEDIATION — TRUSTWORTHY VERIFICATION REGRESSION TESTS
# ============================================================
# Adversarial QA proved the DEFAULT verifier treated
# `observation["success"] == True` / `execution_success == True`
# as proof that the requested final state was achieved.
#
# Required semantics enforced here:
#   EXECUTION SUCCESS != VERIFIED SUCCESS.
#   Verification inspects the ACTUAL state:
#     - file content  -> reads the real file
#     - file exists   -> checks the real filesystem
#     - folder exists -> checks the real filesystem
#     - external deletion / stale success -> contradicted by real state
#     - lying observation -> never accepted as proof
#   Outcomes are tri-state:
#     VERIFIED_SUCCESS  (final state observed)
#     VERIFIED_FAILURE  (state contradicts expectation)
#     UNKNOWN           (final state cannot be established) — never success.
#
# Real safe skills are used wherever practical (FileSkill /
# WindowsSkill / BrowserSkill safe paths) — no mocks for the core
# file scenarios.
# ============================================================

from __future__ import annotations

import asyncio
import os

from avora_backend.agent_orchestrator import AgentOrchestrator
from avora_backend.skills.file_skill import FileSkill
from avora_backend.skills.windows_skill import WindowsSkill
from avora_backend.skills.browser_skill import BrowserSkill


def run_orch(orch: AgentOrchestrator, goal: str) -> dict:
    """Blocking helper that runs the async orchestrator to completion."""
    return asyncio.run(orch.execute_goal(goal))


def _engine(*, execute, observe=None, plan=None, goal="p04"):
    """Build an orchestrator that uses the DEFAULT (VerificationEngine)
    verifier — no `verify_callback`. This is the path under test."""
    return AgentOrchestrator(
        plan_callback=lambda g: plan,
        execute_callback=execute,
        observe_callback=observe,
    )


# ---------------------------------------------------------------------
# Real FileSkill executor (async, exercises the real skill path)
# ---------------------------------------------------------------------

async def file_executor(action):
    skill = FileSkill()
    return await skill.execute(action)


# ---------------------------------------------------------------------
# Test 1 — Wrong file content => VERIFICATION FAILURE (never success)
# ---------------------------------------------------------------------

def test_wrong_file_content_is_verification_failure(tmp_path):
    path = str(tmp_path / "verify_content.txt")
    requested = "AVORA_VERIFICATION_CORRECT"

    def observe(action, execution_result):
        # Adversarial: external process replaces the content AFTER execution.
        with open(path, "w") as f:
            f.write("AVORA_VERIFICATION_WRONG")
        # Lying observation as well: claims success.
        return {"success": True}

    plan = [{
        "action_type": "create_file",
        "target": path,
        "parameters": {"content": requested},
        "expected_result": "file exists with requested content",
        "retry_policy": 0,
    }]

    orch = _engine(execute=file_executor, observe=observe, plan=plan)
    result = run_orch(orch, "create file with exact content")

    status = orch.task.verification_results[0]["status"]
    assert status == "VERIFIED_FAILURE", f"expected failure, got {status}"
    assert 0 not in orch.task.completed_steps
    assert result["steps_completed"] == 0
    # Never a success: task must be FAILED or otherwise not completed.
    assert orch.task.is_failed()
    assert not orch.task.is_completed()
    assert "Failed to complete" in result["final_result"]
    # The real file really contains the wrong content.
    assert open(path).read() == "AVORA_VERIFICATION_WRONG"


# ---------------------------------------------------------------------
# Test 2 — Missing file => VERIFICATION FAILURE
# ---------------------------------------------------------------------

def test_action_claims_file_creation_but_file_missing(tmp_path):
    path = str(tmp_path / "ghost.txt")

    def lying_executor(action):
        # Reports execution success WITHOUT creating the file.
        return {"status": "created", "success": True, "exists": True}

    plan = [{
        "action_type": "create_file",
        "target": path,
        "parameters": {"content": "data"},
        "expected_result": "file exists",
        "retry_policy": 0,
    }]

    orch = _engine(execute=lying_executor, plan=plan)
    result = run_orch(orch, "create ghost file")

    status = orch.task.verification_results[0]["status"]
    assert status == "VERIFIED_FAILURE", f"expected failure, got {status}"
    assert not os.path.isfile(path)
    assert 0 not in orch.task.completed_steps
    assert orch.task.is_failed()
    assert not orch.task.is_completed()
    assert result["steps_completed"] == 0


# ---------------------------------------------------------------------
# Test 3 — Missing directory => VERIFICATION FAILURE
# ---------------------------------------------------------------------

def test_action_claims_folder_creation_but_directory_missing(tmp_path):
    target = str(tmp_path / "ghost_dir")

    def lying_executor(action):
        # Reports execution success WITHOUT creating the directory.
        return {"status": "created", "success": True, "exists": True}

    plan = [{
        "action_type": "create_folder",
        "target": target,
        "expected_result": "folder exists",
        "retry_policy": 0,
    }]

    orch = _engine(execute=lying_executor, plan=plan)
    result = run_orch(orch, "create ghost folder")

    status = orch.task.verification_results[0]["status"]
    assert status == "VERIFIED_FAILURE", f"expected failure, got {status}"
    assert not os.path.isdir(target)
    assert 0 not in orch.task.completed_steps
    assert orch.task.is_failed()
    assert result["steps_completed"] == 0


# ---------------------------------------------------------------------
# Test 4 — External deletion => VERIFICATION FAILURE (stale success)
# ---------------------------------------------------------------------

def test_external_deletion_before_verification_is_failure(tmp_path):
    target = str(tmp_path / "externally_deleted")

    def observe(action, execution_result):
        # The harmless artifact was truly created; now delete it externally
        # BEFORE verification inspects the real state.
        if os.path.isdir(target):
            os.rmdir(target)
        return {"success": True, "folder_exists": True}  # stale/lying claim

    plan = [{
        "action_type": "create_folder",
        "target": target,
        "expected_result": "folder exists",
        "retry_policy": 0,
    }]

    orch = _engine(execute=file_executor, observe=observe, plan=plan)
    result = run_orch(orch, "create then verify folder")

    status = orch.task.verification_results[0]["status"]
    assert status == "VERIFIED_FAILURE", f"expected failure, got {status}"
    assert not os.path.isdir(target)
    assert 0 not in orch.task.completed_steps
    assert orch.task.is_failed()
    assert not orch.task.is_completed()


# ---------------------------------------------------------------------
# Test 5 — Lying observation {"success": True} => NOT VERIFIED (UNKNOWN)
# ---------------------------------------------------------------------

def test_lying_observation_success_true_is_not_accepted(tmp_path):
    def execute(action):
        return {"status": "executed"}

    def observe(action, execution_result):
        # The adversarial lying observation — success with NO evidence and
        # the requested final state cannot be established from any source.
        return {"success": True}

    plan = [{
        "action_type": "open_url",
        "target": "https://docs.example.com",
        "expected_result": "docs page loaded",
        "retry_policy": 0,
    }]

    orch = _engine(execute=execute, observe=observe, plan=plan)
    result = run_orch(orch, "open docs page")

    status = orch.task.verification_results[0]["status"]
    assert status == "UNKNOWN", f"expected NOT VERIFIED (UNKNOWN), got {status}"
    # Never automatic success.
    assert 0 not in orch.task.completed_steps
    assert result["steps_completed"] == 0
    assert not orch.task.is_completed()
    # Honest user-facing message — no "Done!" claim.
    assert "could not independently verify" in result["final_result"]
    assert not result["final_result"].lower().startswith("completed")


# ---------------------------------------------------------------------
# Test 6 — Genuine success => VERIFIED_SUCCESS
# ---------------------------------------------------------------------

def test_genuine_success_is_verified_success(tmp_path):
    path = str(tmp_path / "real_success.txt")
    content = "AVORA_VERIFICATION_CORRECT"

    plan = [{
        "action_type": "create_file",
        "target": path,
        "parameters": {"content": content},
        "expected_result": "file exists with requested content",
        "retry_policy": 0,
    }]

    orch = _engine(execute=file_executor, plan=plan)
    result = run_orch(orch, "create a real file")

    status = orch.task.verification_results[0]["status"]
    assert status == "VERIFIED_SUCCESS", f"expected success, got {status}"
    assert 0 in orch.task.completed_steps
    assert result["steps_completed"] == 1
    assert orch.task.errors == []
    assert not orch.task.is_failed()
    # Independently confirm the real state matches.
    assert os.path.isfile(path)
    assert open(path).read() == content


# ---------------------------------------------------------------------
# Test 7 — Unverifiable action => UNVERIFIABLE / UNKNOWN, no completion
# ---------------------------------------------------------------------

def test_unverifiable_action_reports_unknown_not_complete(tmp_path):
    def execute(action):
        # The executor ran, but no independent observation of the final
        # state is available and the architecture has no state-based
        # checker that can confirm the message was actually sent.
        return {"status": "sent", "success": True}

    plan = [{
        "action_type": "send_message",
        "target": "slack",
        "parameters": {"message": "hi"},
        "expected_result": "message sent",
        "retry_policy": 0,
    }]

    orch = _engine(execute=execute, plan=plan)
    result = run_orch(orch, "send a message")

    status = orch.task.verification_results[0]["status"]
    assert status == "UNKNOWN", f"expected UNKNOWN, got {status}"
    assert 0 not in orch.task.completed_steps
    assert result["steps_completed"] == 0
    assert not orch.task.is_completed()
    # The system must NOT claim the goal is definitely complete.
    assert "could not independently verify" in result["final_result"]


# ---------------------------------------------------------------------
# Test 8 — Multi-step: verified success => VERIFIED_FAILURE => STOP
# (P0 #3 integration: failed step blocks later steps, no false success)
# ---------------------------------------------------------------------

def test_multi_step_verified_success_then_failure_blocks_later_steps(tmp_path):
    ok_path = str(tmp_path / "ok.txt")
    fail_path = str(tmp_path / "fail.txt")
    tail_path = str(tmp_path / "tail.txt")
    executed = []

    async def tracker(action):
        executed.append(action.target)
        skill = FileSkill()
        return await skill.execute(action)

    def observe(action, execution_result):
        # Step 0 verifies genuine success. Step 1 gets adversarially
        # corrupted on EVERY attempt so verification keeps failing.
        if action.target == fail_path:
            with open(fail_path, "w") as f:
                f.write("AVORA_VERIFICATION_WRONG")
        return {"success": True}

    plan = [
        {"action_type": "create_file", "target": ok_path,
         "parameters": {"content": "AVORA_VERIFICATION_CORRECT"},
         "expected_result": "ok", "retry_policy": 0},
        {"action_type": "create_file", "target": fail_path,
         "parameters": {"content": "AVORA_VERIFICATION_CORRECT"},
         "expected_result": "fail if content wrong", "retry_policy": 1},
        {"action_type": "create_file", "target": tail_path,
         "parameters": {"content": "AVORA_VERIFICATION_CORRECT"},
         "expected_result": "must not run", "retry_policy": 0},
    ]

    orch = _engine(execute=tracker, observe=observe, plan=plan)
    result = run_orch(orch, "multi-step verify")

    # Step 1 (ok.txt) genuinely verified.
    assert orch.task.verification_results[0]["status"] == "VERIFIED_SUCCESS"
    # Step 2 (fail.txt) failed verification and stayed failed after retry.
    assert orch.task.verification_results[1]["status"] == "VERIFIED_FAILURE"
    # Step 1 counted completed; step 2 NOT counted completed.
    assert orch.task.completed_steps == [0]
    assert result["steps_completed"] == 1
    # Step 3 (tail.txt) never executed after the unrecoverable failure.
    assert tail_path not in executed
    assert fail_path in executed  # the failing step did run (initial + retry)
    # Task does NOT report success.
    assert orch.task.is_failed()
    assert not orch.task.is_completed()
    assert result["status"] == "FAILED"
    assert "Failed to complete" in result["final_result"]


# ---------------------------------------------------------------------
# Real WindowsSkill integration (safe, non-destructive) — default verifier
# ---------------------------------------------------------------------

def test_real_windows_skill_get_process_list_verified(tmp_path):
    async def win_execute(action):
        skill = WindowsSkill()
        return await skill.execute(action)

    plan = [{
        "action_type": "get_process_list",
        "target": "",
        "expected_result": "process list",
        "retry_policy": 0,
    }]

    orch = _engine(execute=win_execute, plan=plan)
    result = run_orch(orch, "list processes")

    status = orch.task.verification_results[0]["status"]
    assert status == "VERIFIED_SUCCESS", f"expected success, got {status}"
    assert 0 in orch.task.completed_steps
    assert result["steps_completed"] == 1
    assert orch.task.errors == []


# ---------------------------------------------------------------------
# Real BrowserSkill safe path (no browser needed) — default verifier
# ---------------------------------------------------------------------

def test_real_browser_skill_safe_path_verified(tmp_path):
    async def browser_execute(action):
        skill = BrowserSkill(headless=True)
        return await skill.execute(action)

    plan = [{
        "action_type": "get_process_list",
        "target": "",
        "expected_result": "process list",
        "retry_policy": 0,
    }]

    orch = _engine(execute=browser_execute, plan=plan)
    result = run_orch(orch, "list browser processes")

    status = orch.task.verification_results[0]["status"]
    assert status == "VERIFIED_SUCCESS", f"expected success, got {status}"
    assert 0 in orch.task.completed_steps
    assert result["steps_completed"] == 1
    assert orch.task.errors == []


# ---------------------------------------------------------------------
# Engine-level semantics tri-state (direct VerificationEngine checks)
# ---------------------------------------------------------------------

def test_engine_semantics_tri_state():
    from avora_backend.action_model import Action, ActionType
    from avora_backend.verification import VerificationEngine, VerificationStatus

    engine = VerificationEngine()

    # Filesystem authoritative
    action = Action(action_type=ActionType.CREATE_FOLDER, target="/definitely/not/a/real/folder/avora_xyz")
    assert engine.verify(action, {"success": True}).status == VerificationStatus.VERIFIED_FAILURE
    # Lying observation, no evidence -> UNKNOWN (never success)
    action = Action(action_type=ActionType.OPEN_URL, target="https://example.com")
    assert engine.verify(action, {"success": True}).status == VerificationStatus.UNKNOWN
    # Real evidence -> VERIFIED_SUCCESS
    action = Action(action_type=ActionType.OPEN_URL, target="https://example.com")
    assert engine.verify(action, {"success": True, "page_title": "Example Domain"}).status == VerificationStatus.VERIFIED_SUCCESS
    # UNKNOWN must never be truthy
    result = engine.verify(
        Action(action_type=ActionType.SEND_MESSAGE, target="x"),
        {"success": True},
    )
    assert result.status == VerificationStatus.UNKNOWN
    assert bool(result) is False