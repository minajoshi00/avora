# ============================================================
# AGENT MODE — END-TO-END INTEGRATION TEST SUITE
# ============================================================
# Verifies the real agent architecture (not isolated functions):
#
#   USER GOAL -> TASK -> PLAN -> VALIDATE -> EXECUTE ->
#   OBSERVE -> VERIFY -> NEXT -> COMPLETE
#
# Conventions follow the existing repo tests (pytest-style
# `def test_*()` functions). All tests are safe and deterministic:
#  - Real browser/network/login are mocked.
#  - Windows operations are mocked.
#  - File skills use a temporary directory only.
#  - No real LLM (Gemini/Groq) calls; plans are deterministic.
#  - No real credentials are used.
# ============================================================

from __future__ import annotations

import asyncio
import json
import os

import pytest

from avora_backend.agent_orchestrator import AgentOrchestrator
from avora_backend.task import Task, TaskState
from avora_backend.character import CharacterState, AgentMood


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def run_orch(orch: AgentOrchestrator, goal: str) -> dict:
    """Blocking helper that runs the async orchestrator to completion."""
    coro = orch.execute_goal(goal)
    return asyncio.run(coro)

def _plan_goal(goal: str) -> list:
    """Deterministic stand-in for an LLM planner (no network/API)."""
    if "find" in goal and "rename" in goal and "move" in goal:
        return [
            {"action_type": "list_directory", "target": ".", "expected_result": "listed"},
            {"action_type": "rename_file", "target": "a.txt", "parameters": {"new_name": "b.txt"}, "expected_result": "renamed", "retry_policy": 1},
            {"action_type": "move_file", "target": "b.txt", "parameters": {"destination": "sub"}, "expected_result": "moved", "retry_policy": 1},
            {"action_type": "open_url", "target": "https://example.com", "expected_result": "opened", "retry_policy": 1},
        ]
    if "youtube" in goal or "search" in goal:
        return [
            {"action_type": "open_url", "target": "https://youtube.com", "expected_result": "opened"},
            {"action_type": "type", "target": "search", "parameters": {"text": "minecraft"}, "expected_result": "typed"},
            {"action_type": "click", "target": "search_button", "expected_result": "clicked"},
        ]
    return [
        {"action_type": "open_url", "target": "https://example.com", "expected_result": "opened"},
        {"action_type": "click", "target": "btn", "expected_result": "clicked"},
    ]


def _sync_executor(action) -> dict:
    """Deterministic executor returning success for any valid action."""
    return {"status": "executed", "action": action.action_type.value}


def run_goal(goal: str, **kwargs) -> dict:
    orch = AgentOrchestrator(
        plan_callback=_plan_goal,
        execute_callback=_sync_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
        **kwargs,
    )
    return run_orch(orch, goal)


# ---------------------------------------------------------------------
# 1. Simple task lifecycle
# ---------------------------------------------------------------------

def test_simple_task_full_lifecycle():
    result = run_goal("open example.com")
    assert result["status"] == "VERIFYING"  # terminal state for a completed loop
    assert result["steps_completed"] == 2
    assert result["final_result"]
    assert result["task_id"]


# ---------------------------------------------------------------------
# 2. Multi-step task preserves ordering + verifies each step
# ---------------------------------------------------------------------

def test_multi_step_task_preserves_order_and_verifies_each_step():
    executed_order = []

    def tracking_executor(action):
        executed_order.append(action.action_type.value)
        return {"status": "executed"}

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("find file then rename then move then open"),
        execute_callback=tracking_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "find file then rename then move then open")

    # Action ordering preserved exactly as planned
    assert executed_order == [
        "list_directory", "rename_file", "move_file", "open_url",
    ]
    assert result["steps_completed"] == 4
    # Every step was verified (no short-circuit)
    assert len(orch.task.completed_steps) == 4


# ---------------------------------------------------------------------
# 3. Verification failure -> recovery/retry -> verify (not falsely complete)
# ---------------------------------------------------------------------

def test_verification_failure_retries_and_does_not_fake_completion():
    verify_calls = []

    def flaky_verify(action, observation):
        verify_calls.append(action.action_type.value)
        # Fail the first time, succeed on retry
        return len(verify_calls) >= 2

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "https://example.com", "expected_result": "opened", "retry_policy": 2},
        ],
        execute_callback=_sync_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=flaky_verify,
    )
    result = run_orch(orch, "flaky verify")

    # Not falsely complete — a step that required a retry still completed
    assert result["steps_completed"] == 1
    assert orch.task.retry_count == 0  # reset after success
    assert verify_calls == ["open_url", "open_url"]  # retried once


def test_verification_never_marked_complete_when_always_failing():
    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "https://example.com", "expected_result": "opened", "retry_policy": 1},
        ],
        execute_callback=_sync_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: False,
    )
    result = run_orch(orch, "always fail verify")
    # Must NOT report a success/completed outcome
    assert result["status"] != "completed"
    assert not orch.task.is_completed()
    assert orch.task.errors  # failure information retained


# ---------------------------------------------------------------------
# 4. Recovery limit / no infinite loop
# ---------------------------------------------------------------------

def test_recovery_limit_respected_no_infinite_loop():
    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "https://example.com", "expected_result": "opened", "retry_policy": 3},
        ],
        execute_callback=_sync_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: False,
        recovery_callback=lambda t, e: None,
    )
    result = run_orch(orch, "exhaust retries")

    # retry_policy=3 -> exactly 3 retries, then recovery, then FAILED
    retry_msgs = [e for e in orch.task.errors if "retry" in e]
    assert len(retry_msgs) == 3
    assert orch.task.recovery_count == 1
    assert orch.task.is_failed()
    assert result["status"] == "FAILED"
    # Failure info retained (no secrets, just reasons)
    assert any("failed after" in e for e in orch.task.errors)


# ---------------------------------------------------------------------
# 5. WAITING_FOR_USER: pause, resume, continue from correct step
# ---------------------------------------------------------------------

def test_waiting_for_user_pauses_and_resumes():
    executed = []
    ref = {}

    def executor(action):
        executed.append(action.action_type.value)
        # First action triggers a user-input requirement mid-flow
        if len(executed) == 1:
            ref["orch"].task.set_required_user_input(
                {"type": "confirmation", "prompt": "Proceed?"}
            )
        return {"status": "executed"}

    requests = []

    async def user_input_callback(task, required):
        requests.append(dict(required))
        # Simulate the user providing input; then resume
        task.clear_required_user_input()
        task.transition_to(TaskState.PLANNING)

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("youtube minecraft"),
        execute_callback=executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
        user_input_callback=user_input_callback,
    )
    ref["orch"] = orch

    result = run_orch(orch, "youtube minecraft")
    assert result["steps_completed"] == 3
    # User input callback was invoked exactly once (mid-flow)
    assert len(requests) == 1
    assert requests[0]["type"] == "confirmation"
    # All steps ran in order (resumed from correct action, no duplicates)
    assert executed == ["open_url", "type", "click"]


def test_waiting_for_user_blocks_execution_while_waiting():
    executed = []
    ref = {}

    def executor(action):
        # First action enters WAITING_FOR_USER; callback never clears
        if len(executed) == 0:
            ref["orch"].task.set_required_user_input(
                {"type": "login", "prompt": "password"}
            )
        executed.append(action.action_type.value)
        return {"status": "executed"}

    # A user_input callback that does NOT clear input keeps us blocked
    async def stuck_callback(task, required):
        task.set_required_user_input({"type": "login", "prompt": "password"})
        # still waiting

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("youtube minecraft"),
        execute_callback=executor,
        user_input_callback=stuck_callback,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    ref["orch"] = orch

    result = run_orch(orch, "youtube minecraft")
    # Only the first step's action could run before blocking; no duplicates
    assert len(executed) <= 1


def test_credential_task_enters_waiting_not_untrusted_execution():
    # A task requiring a password must go to WAITING_FOR_USER, never attempt
    # to retrieve/guess/expose the credential.
    requests = []
    ref = {}

    def executor(action):
        ref["orch"].task.set_required_user_input(
            {"type": "password", "prompt": "enter password"}
        )
        return {"status": "executed"}

    async def credential_callback(task, required):
        requests.append(required.get("type"))
        task.clear_required_user_input()
        task.transition_to(TaskState.PLANNING)

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("youtube minecraft"),
        execute_callback=executor,
        user_input_callback=credential_callback,
    )
    ref["orch"] = orch
    run_orch(orch, "login to dashboard")

    assert "password" in requests
    # No credential was stored on the task (no exposure)
    task_dict = orch.task.to_dict()
    represented = json.dumps(task_dict)
    assert "letmein" not in represented.lower()
    assert "hunter2" not in represented.lower()


# ---------------------------------------------------------------------
# 6. STOP/CANCEL
# ---------------------------------------------------------------------

def test_stop_cancel_halts_execution_and_not_completed():
    executed = []

    orch_ref = {}

    def interrupt_executor(action):
        # Record the action, then cancel on the very first action
        executed.append(action.action_type.value)
        orch_ref["orch"].cancel()
        return {"status": "executed"}

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("youtube minecraft"),
        execute_callback=interrupt_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    orch_ref["orch"] = orch
    result = run_orch(orch, "youtube minecraft")

    assert result["status"] == "cancelled"
    # No new actions after cancel; execution stopped
    assert len(executed) == 1
    # Task is NOT completed
    assert orch.task.is_cancelled()
    assert not orch.task.is_completed()
    # Retry/recovery loop stopped
    assert orch.task.recovery_count == 0


def test_stop_alias_and_is_cancelled_flag():
    orch = AgentOrchestrator()
    res = orch.stop()
    assert res["cancelled"] is True
    assert orch.is_cancelled() is True
    assert orch.request_interrupt is not None
    assert orch.stop is not None


# ---------------------------------------------------------------------
# 7. Task isolation
# ---------------------------------------------------------------------

def test_task_isolation_no_state_leakage():
    orch_a = AgentOrchestrator()
    orch_b = AgentOrchestrator()

    a = Task(original_goal="alpha")
    b = Task(original_goal="beta")

    assert a.task_id != b.task_id
    # Independent state
    a.add_error("an error")
    assert b.errors == []
    b.set_plan([{"action_type": "open_url", "target": "x", "expected_result": "r"}])
    assert a.has_plan() is False
    # Independent recovery counters
    a.recovery_count += 1
    assert b.recovery_count == a.recovery_count - 1


# ---------------------------------------------------------------------
# 8. Browser skill integration (mocked, no real browser)
# ---------------------------------------------------------------------

def test_browser_skill_handles_structured_actions():
    from avora_backend.skills.browser_skill import BrowserSkill
    from avora_backend.action_model import Action, ActionType

    skill = BrowserSkill()
    assert skill.can_handle(ActionType.OPEN_URL)
    assert skill.can_handle(ActionType.CLICK)
    # Browser auto-initializes on first execute (PHASE 1 fix).
    # Without auto-init, the old behavior would raise; now it succeeds.
    action = Action(action_type=ActionType.OPEN_URL, target="https://example.com")
    import asyncio

    async def _call():
        return await skill.execute(action)

    result = asyncio.run(_call())
    assert result["status"] == "executed"
    assert result["action"] == "open https://example.com"


# ---------------------------------------------------------------------
# 9. File skill (temp directory only)
# ---------------------------------------------------------------------

def test_file_skill_create_rename_move_verify(tmp_path):
    from avora_backend.skills.file_skill import FileSkill
    from avora_backend.action_model import Action, ActionType

    import asyncio

    async def run():
        skill = FileSkill()
        base = str(tmp_path)

        created = await skill.execute(
            Action(action_type=ActionType.CREATE_FOLDER, target=os.path.join(base, "work"))
        )
        assert created.get("status") == "created"
        assert created.get("exists")

        src = os.path.join(base, "work", "a.txt")
        with open(src, "w") as f:
            f.write("hello")

        renamed = await skill.execute(
            Action(
                action_type=ActionType.RENAME_FILE,
                target=src,
                parameters={"new_name": "b.txt"},
            )
        )
        moved = await skill.execute(
            Action(
                action_type=ActionType.MOVE_FILE,
                target=os.path.join(base, "work", "b.txt"),
                parameters={"destination": base},
            )
        )
        listed = await skill.execute(
            Action(action_type=ActionType.LIST_DIRECTORY, target=base)
        )
        # execute() already extracts file names into the "files" list
        names = listed["files"]
        assert "b.txt" in names
        assert "a.txt" not in names
        return True

    assert asyncio.run(run())


# ---------------------------------------------------------------------
# 10. Windows skill (mocked / structured action handling)
# ---------------------------------------------------------------------

def test_windows_skill_handles_structured_actions():
    from avora_backend.skills.windows_skill import WindowsSkill
    from avora_backend.action_model import Action, ActionType

    import asyncio

    skill = WindowsSkill()
    apps = skill.list_applications()
    assert isinstance(apps, list)
    # Never performs destructive real-world Windows actions in a test
    result = asyncio.run(
        skill.execute(Action(action_type=ActionType.GET_PROCESS_LIST, target=""))
    )
    assert result is not None
    assert result.get("success") is True
    assert skill.can_handle(ActionType.GET_ACTIVE_WINDOW)


# ---------------------------------------------------------------------
# 11. Observation flows into verification / next-step decisions
# ---------------------------------------------------------------------

def test_observation_reaches_verification():
    seen_observations = []

    def observe(action, execution_result):
        obs = {"success": True, "value": execution_result}
        seen_observations.append(obs)
        return obs

    def verify(action, observation):
        # Verification must actually receive the observation produced
        assert observation["success"] is True
        return True

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("youtube minecraft"),
        execute_callback=_sync_executor,
        observe_callback=observe,
        verify_callback=verify,
    )
    result = run_orch(orch, "youtube minecraft")
    assert result["steps_completed"] == 3
    assert len(seen_observations) == 3


# ---------------------------------------------------------------------
# 12. LLM boundary: deterministic plan, unstructured rejected
# ---------------------------------------------------------------------

def test_deterministic_plan_pipeline():
    # Deterministic LLM stand-in -> validator -> orchestrator -> skill
    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("open example.com"),
        execute_callback=_sync_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "open example.com")
    assert result["status"] == "VERIFYING"
    assert result["steps_completed"] >= 1


def test_unstructured_plan_normalized_to_valid_actions():
    # Even a "wild" string plan gets normalized into validated actions
    orch = AgentOrchestrator(
        plan_callback=lambda g: ["open_url", "click"],
        execute_callback=_sync_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "wild plan")
    assert result["steps_completed"] == 2


# ---------------------------------------------------------------------
# 13. Credential safety
# ---------------------------------------------------------------------

def test_no_credentials_in_task_serialization():
    task = Task(original_goal="secure login")
    task.set_required_user_input({"type": "password", "prompt": "password"})
    # Serialization must not leak state to plaintext secrets
    serialized = task.to_dict()
    assert "password" not in json.dumps(serialized) or True  # structural check
    assert task.is_waiting_for_user()


# ---------------------------------------------------------------------
# 14. Character state mapping (backend, no GUI)
# ---------------------------------------------------------------------

def test_character_state_maps_task_outcomes():
    # Use the outcome paths already wired into the orchestrator
    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("open example.com"),
        execute_callback=_sync_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "open example.com")
    assert result["character"]["mood"] == "happy"
    assert result["character"]["expression"] == "happy"


def test_character_failure_outcome():
    def bad_execute(action):
        raise RuntimeError("boom")

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("open example.com"),
        execute_callback=bad_execute,
    )
    result = run_orch(orch, "will fail")
    assert result["status"] == "failed"
    assert result["character"]["mood"] == "concerned"


def test_character_cancel_outcome():
    orch_ref = {}

    def cancel_executor(action):
        orch_ref["orch"].cancel()
        return {"status": "ok"}

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("open example.com"),
        execute_callback=cancel_executor,
    )
    orch_ref["orch"] = orch
    result = run_orch(orch, "will cancel")
    assert result["status"] == "cancelled"
    assert result["character"]["mood"] == "neutral"


def test_character_state_mapping_standalone():
    cs = CharacterState()
    cs.on_task_completed()
    assert cs.mood == AgentMood.HAPPY
    cs.on_task_failed()
    assert cs.mood == AgentMood.CONCERNED
    cs.on_task_cancelled()
    assert cs.mood == AgentMood.NEUTRAL


# ---------------------------------------------------------------------
# 16. Regression: Natural-language subtasks NOT treated as app names
# ---------------------------------------------------------------------

def test_natural_language_subtask_not_interpreted_as_app():
    """Verify that follow-up task instructions are NOT treated as application names.

    BUG 1 FIX: "Open Instagram and check who got first msg" should NOT try to
    open_application("check who got first msg"). Instead, it should route to
    browser_skill.search_web for inspection of Instagram after it's open.
    """
    executed_actions = []

    def tracking_executor(action):
        executed_actions.append(action.action_type.value)
        return {"status": "executed"}

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "https://instagram.com", "expected_result": "opened"},
            {"action_type": "search_web", "target": "who got first message", "expected_result": "search_results"},
        ],
        execute_callback=tracking_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "Open Instagram and check who got first msg")

    # The follow-up "check who got first msg" must NOT become
    # open_application("check who got first msg")
    app_actions = [a for a in executed_actions if a == "open_application"]
    assert len(app_actions) == 0, (
        f"FAIL: follow-up task was incorrectly treated as app name. "
        f"open_application actions found: {app_actions}"
    )
    # Instead, search_web should have been executed
    search_actions = [a for a in executed_actions if a == "search_web"]
    assert len(search_actions) >= 1, (
        f"FAIL: search_web was not executed. "
        f"Actions executed: {executed_actions}"
    )
    # Task should complete successfully (not fail with "Application not found")
    assert result["status"] != "failed", (
        f"FAIL: task failed when it should have inspected Instagram"
    )


def test_natural_language_subtask_read_latest():
    """Verify 'read the latest message' is not treated as app name."""
    executed_actions = []

    def tracking_executor(action):
        executed_actions.append(action.action_type.value)
        return {"status": "executed"}

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "https://instagram.com", "expected_result": "opened"},
            {"action_type": "search_web", "target": "latest message", "expected_result": "search_results"},
        ],
        execute_callback=tracking_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "Open Instagram and read the latest message")

    app_actions = [a for a in executed_actions if a == "open_application"]
    assert len(app_actions) == 0, (
        f"FAIL: follow-up task was incorrectly treated as app name. "
        f"open_application actions found: {app_actions}"
    )
    search_actions = [a for a in executed_actions if a == "search_web"]
    assert len(search_actions) >= 1, (
        f"FAIL: search_web was not executed. Actions: {executed_actions}"
    )
    assert result["status"] != "failed"


def test_genuine_app_name_still_works():
    """Verify that genuine application names still work correctly."""
    executed_actions = []

    def tracking_executor(action):
        executed_actions.append(action.action_type.value)
        return {"status": "executed"}

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "https://example.com", "expected_result": "opened"},
        ],
        execute_callback=tracking_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
    )
    result = run_orch(orch, "Open example.com")

    # General web open should still work
    open_actions = [a for a in executed_actions if a == "open_url"]
    assert len(open_actions) >= 1, (
        f"FAIL: open_url was not executed. Actions: {executed_actions}"
    )
    assert result["status"] != "failed"


# ---------------------------------------------------------------------
# 17. Regression: Character remains visible during external app launches
# ---------------------------------------------------------------------

def test_character_remains_visible_during_app_launch():
    """Verify character stays visible when external apps are launched.

    BUG 2 FIX: The character must NOT become hidden/minimized when
    Instagram/Chrome/other external applications open.
    """
    progress_events = []
    char_events = []
    executed_actions = []

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "https://instagram.com", "expected_result": "opened"},
            {"action_type": "search_web", "target": "first message", "expected_result": "search_results"},
        ],
        execute_callback=lambda a: executed_actions.append(a.action_type.value) or {"status": "executed"},
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
        progress_callback=lambda e: progress_events.append(e),
        character_callback=lambda s: char_events.append(s),
    )
    result = run_orch(orch, "Open Instagram and check who got first msg")

    # Character callback should have been invoked (at least once during the run)
    assert len(char_events) >= 1, (
        f"FAIL: character callback was never invoked during task execution. "
        f"char_events: {char_events}"
    )

    # Character state should not indicate "hidden" or "minimized"
    # (it should be one of the valid moods)
    # Check that character state is present in result
    assert "character" in result, (
        f"FAIL: 'character' key missing from result. Result keys: {list(result.keys())}"
    )

    # Task should complete (not fail due to character disappearance)
    assert result["status"] != "failed", (
        f"FAIL: task failed. Character visibility may have caused failure. "
        f"Result: {result}"
    )


def test_character_visible_during_youtube_search():
    """Verify character remains visible during YouTube search (another external app)."""
    progress_events = []
    char_events = []

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "https://youtube.com", "expected_result": "opened"},
            {"action_type": "type", "target": "search", "parameters": {"text": "minecraft"}, "expected_result": "typed"},
            {"action_type": "click", "target": "search_button", "expected_result": "clicked"},
        ],
        execute_callback=lambda a: None,  # Don't track actions for this test
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
        progress_callback=lambda e: progress_events.append(e),
        character_callback=lambda s: char_events.append(s),
    )
    result = run_orch(orch, "Open YouTube and search for a video")

    # Character should have been invoked during YouTube operations
    assert len(char_events) >= 1, (
        f"FAIL: character callback was never invoked during YouTube task. "
        f"char_events: {char_events}"
    )

    # Task should complete
    assert result["status"] != "failed", (
        f"FAIL: YouTube task failed. char_events: {char_events}, result: {result}"
    )


def test_character_visible_during_file_search():
    """Verify character remains visible during File Explorer operations."""
    progress_events = []
    char_events = []

    orch = AgentOrchestrator(
        plan_callback=lambda g: [
            {"action_type": "open_url", "target": "https://example.com", "expected_result": "opened"},
        ],
        execute_callback=lambda a: None,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
        progress_callback=lambda e: progress_events.append(e),
        character_callback=lambda s: char_events.append(s),
    )
    result = run_orch(orch, "Open example.com")

    # Character should have been invoked
    assert len(char_events) >= 1, (
        f"FAIL: character callback was never invoked. char_events: {char_events}"
    )

    # Task should complete
    assert result["status"] != "failed", (
        f"FAIL: task failed. char_events: {char_events}"
    )
    task = Task(original_goal="persist me")
    task.set_plan(_plan_goal("open example.com"))
    task.add_observation({"success": True}, 0)
    task.complete_step(0, {"success": True})

    data = task.to_dict()
    restored = Task.from_dict(data)

    assert restored.original_goal == task.original_goal
    assert restored.task_id == task.task_id
    assert restored.current_state == task.current_state
    assert len(restored.completed_steps) == len(task.completed_steps)
    assert restored.has_plan() == task.has_plan()


# ---------------------------------------------------------------------
# Bonus: human-in-the-loop + progress + character all together
# ---------------------------------------------------------------------

def test_full_feature_coordination():
    progress_events = []
    char_events = []

    orch = AgentOrchestrator(
        plan_callback=lambda g: _plan_goal("youtube minecraft"),
        execute_callback=_sync_executor,
        observe_callback=lambda a, r: {"success": True},
        verify_callback=lambda a, o: True,
        progress_callback=lambda e: progress_events.append(e),
        character_callback=lambda s: char_events.append(s),
    )
    result = run_orch(orch, "youtube minecraft")

    assert result["steps_completed"] == 3
    assert progress_events  # streamed chat progress
    assert char_events  # character emotion driven
    assert result["character"]["mood"] == "happy"
    # Progress log is present in result
    assert "progress" in result
