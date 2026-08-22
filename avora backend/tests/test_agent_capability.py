"""
Phase 5 - Real Actions / Agent Capability test suite.

Uses a mock tool registry so no real actions are performed.

Covers:
  * Successful task (safe tool runs, progress reported)
  * Failed task (transient failure retried once)
  * Cancelled task (cancel() stops execution)
  * Permission denied (risky tool without confirmation)
  * Permission granted via callback
  * Tool unavailable (unknown tool -> graceful message)
  * Activity log records every invocation

Run from repo root:
    python "avora backend/tests/test_agent_capability.py"
"""

import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

PASS = []
FAIL = []


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name} {detail}")


def section(title):
    print()
    print(f"[{title}]")
    print("-" * 50)


class MockOutcome:
    def __init__(self, name):
        self.name = name


class MockResult:
    def __init__(self, ok, summary, outcome="SUCCESS", data=None, error=""):
        self.ok = ok
        self.summary = summary
        self.outcome = MockOutcome(outcome)
        self.data = data or {}
        self.error = error
        self.tool = "mock_tool"


class MockTool:
    def __init__(self, name, risk):
        self.name = name
        self.risk = risk


class MockRegistry:
    """Mock tool registry with controllable behavior."""

    SAFE = 0
    MODERATE = 1

    def __init__(self):
        self.calls = []
        self.fail_first = False
        self.tools = {
            "safe_tool": MockTool("safe_tool", self.SAFE),
            "risky_tool": MockTool("risky_tool", self.MODERATE),
        }

    def get(self, name):
        return self.tools.get(name)

    def invoke(self, name, args):
        self.calls.append((name, dict(args)))

        if name == "safe_tool":
            if (
                self.fail_first
                and len([c for c in self.calls if c[0] == "safe_tool"]) == 1
            ):
                return MockResult(False, "transient error", outcome="FAILURE")
            return MockResult(True, "safe tool done", data={"result": 42})

        if name == "risky_tool":
            return MockResult(True, "risky tool done")

        return MockResult(False, "unknown tool", outcome="FAILURE")


def make_orchestrator(registry):
    from agent.orchestrator import AgentOrchestrator

    class TestableOrchestrator(AgentOrchestrator):
        # Route the mock tool names so tests exercise the real
        # permission/progress/recovery logic without real actions.
        ROUTED_TOOLS = ("safe_tool", "risky_tool")

    return TestableOrchestrator(registry=registry)


def main():
    print("=" * 60)
    print("PHASE 5 - AGENT CAPABILITY TESTS")
    print("=" * 60)

    tmp = tempfile.mkdtemp(prefix="avora_agent_test_")

    # --------------------------------------------------------
    section("1. Successful task (safe tool)")
    # --------------------------------------------------------
    registry = MockRegistry()
    orch = make_orchestrator(registry)

    progress_steps = []
    orch.progress_callback = lambda step, frac: progress_steps.append((step, frac))

    result = orch.handle_request("please run safe_tool")
    check("safe task succeeds", result.get("success") is True)
    check("tool was invoked", len(registry.calls) == 1)
    check("progress was reported", len(progress_steps) >= 2)
    check(
        "progress reaches 100%",
        any(frac >= 1.0 for _, frac in progress_steps),
    )
    check("activity logged", len(orch.get_activity_log()) == 1)
    check(
        "activity records outcome",
        orch.get_activity_log()[0]["outcome"] == "SUCCESS",
    )

    # --------------------------------------------------------
    section("2. Failed task with recovery (retry once)")
    # --------------------------------------------------------
    registry = MockRegistry()
    registry.fail_first = True
    orch = make_orchestrator(registry)

    result = orch.handle_request("please run safe_tool")
    check("retry recovers from transient failure", result.get("success") is True)
    check(
        "tool invoked twice (retry)",
        len([c for c in registry.calls if c[0] == "safe_tool"]) == 2,
    )

    # --------------------------------------------------------
    section("3. Cancelled task")
    # --------------------------------------------------------
    registry = MockRegistry()
    orch = make_orchestrator(registry)
    orch.cancel()

    result = orch.handle_request("please run safe_tool")
    check("cancelled task reports cancelled", result.get("cancelled") is True)
    check("cancelled task does not invoke tool", len(registry.calls) == 0)

    # Reset and verify it works again
    orch.reset()
    result = orch.handle_request("please run safe_tool")
    check("reset allows new operations", result.get("success") is True)

    # --------------------------------------------------------
    section("4. Permission denied (risky tool, no confirmation)")
    # --------------------------------------------------------
    registry = MockRegistry()
    orch = make_orchestrator(registry)
    # No permission_callback registered -> deny by default

    result = orch.handle_request("please run risky_tool")
    check("risky tool denied without confirmation", result.get("success") is False)
    check(
        "denial asks for confirmation",
        result.get("needs_confirmation") is True,
    )
    check("denied tool was NOT invoked", len(registry.calls) == 0)
    check(
        "denial recorded in activity log",
        any(e["outcome"] == "DENIED" for e in orch.get_activity_log()),
    )

    # --------------------------------------------------------
    section("5. Permission granted via callback")
    # --------------------------------------------------------
    registry = MockRegistry()
    orch = make_orchestrator(registry)
    orch.permission_callback = lambda tool, reason: True

    result = orch.handle_request("please run risky_tool")
    check("approved risky tool runs", result.get("success") is True)
    check("approved tool was invoked", len(registry.calls) == 1)

    # --------------------------------------------------------
    section("6. Permission denied via callback")
    # --------------------------------------------------------
    registry = MockRegistry()
    orch = make_orchestrator(registry)
    orch.permission_callback = lambda tool, reason: False

    result = orch.handle_request("please run risky_tool")
    check("callback denial blocks tool", result.get("success") is False)
    check("denied tool not invoked", len(registry.calls) == 0)

    # --------------------------------------------------------
    section("7. Explicit confirm bypasses permission gate")
    # --------------------------------------------------------
    registry = MockRegistry()
    orch = make_orchestrator(registry)

    result = orch.handle_request("please run risky_tool", confirm=True)
    check("confirm=True runs risky tool", result.get("success") is True)
    check("confirmed tool invoked", len(registry.calls) == 1)

    # --------------------------------------------------------
    section("8. Tool unavailable")
    # --------------------------------------------------------
    registry = MockRegistry()
    orch = make_orchestrator(registry)

    result = orch.handle_request("completely unknown request")
    check(
        "unknown request handled gracefully",
        isinstance(result, dict) and "message" in result,
    )

    # --------------------------------------------------------
    print()
    print("=" * 60)
    print(f"RESULTS: {len(PASS)} passed, {len(FAIL)} failed")
    print("=" * 60)

    if FAIL:
        print("Failed tests:")
        for name in FAIL:
            print(f"  - {name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
