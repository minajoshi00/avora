# AVORA S43 — CONCURRENCY REMEDIATION REPORT

**Status:** FIXED
**Scope:** AVORA Agent Mode — `AgentOrchestrator.execute_goal()` single-task-slot corruption under concurrent execution
**Date:** 2026-08-30
**Baseline verified:** 68 tests passing (62 prior + 6 S37) — preserved, not regressed

---

## 1. Original Reproduction

Two `execute_goal()` calls issued **concurrently on a single `AgentOrchestrator` instance**, using a real `asyncio.gather`, real `Task`, real `FileSkill`, and unique temporary targets, produced silent cross-contamination between the two goals:

| Measurement | Goal A | Goal B |
|---|---|---|
| Files actually created | `[True, False]` (1 file) | `[True, True]` (2 files) |
| Reported `steps_completed` | **2** (wrong — A only did 1) | 2 |
| `self.task.original_goal` (post-run) | `'goal B'` (**A's identity lost**) | `'goal B'` |
| Goal progress events | **only one** (`'New task: goal B'` — A's was overwritten) | one |

The concrete corruption: when goal A was in-flight inside `execute_goal` (having already mutated `self.task`, `self._progress_log`, `self._interrupted`), goal B's `execute_goal` executed `self.task = Task(...)` (original line 198), **replacing the single mutable `self.task` slot** that A's loop was still reading and writing. A then operated on B's task state — steps, observations, verification records, progress events and final results all became ambiguous and were attributed to the wrong request.

This was reproduced with a real harness before any fix was applied (`Receipt`: corruption present in all measured dimensions).

## 2. Root Cause

`AgentOrchestrator` stores its entire working state in **instance-level mutable fields shared by every helper method**:

```
self.task            # single slot — replaced per execute_goal()  (was line 198)
self._interrupted    # single bool
self._progress_log   # single list
self._character_state
```

`execute_goal()` reset these fields unconditionally at entry with **no guard, no lock**: `self.task = Task(...)`, `self._interrupted = False`, `self._progress_log = []`. Every helper (`_execute_loop`, `_handle_verification_failure`, `_execute_loop_step_resume`, `_request_confirmation`, `confirm_current_action`, `decline_current_action`, `cancel`, `request_interrupt`, `_observe_action`, `_verify_action`, …) reads and writes `self.task` directly.

`grep` for a concurrency primitive (lock/semaphore/`asyncio.Lock`) found **none**. The architecture therefore supports **exactly one active task per orchestrator instance** — it is not designed for in-instance task parallelism.

## 3. Architecture Decision (documented policy)

> **An `AgentOrchestrator` instance runs ONE active goal at a time. Concurrent goals are achieved with SEPARATE orchestrator instances — each instance owns fully isolated task / progress / interrupt / confirmation / character state.**

Decision: **Reject a second concurrent `execute_goal` on the same instance with a clear, structured error** (raise `RuntimeError`), rather than:
- **a global serializing lock** — rejected: it would silently serialize the two calls (hiding the misuse, hurting latency, and changing observable UX from "error" to "wait"), and would not solve the deeper issue that the callers genuinely need isolated state;
- **queueing the second call** — rejected: the orchestrator has no queue machinery, and cold-queueing tasks without their own isolated state would reproduce the same corruption the moment the queued task ran;
- **isolating per-call contexts** — rejected: this is a broad refactor of every helper method and changes the orchestrator's public mutation contract (out of S43 scope; raised as a future improvement).

The chosen guard enforces the already-intended single-active-task model explicitly and safely. Because both calls run on a **single-threaded asyncio event loop**, the check-and-set (`_goal_execution_active` read, then set `True`) is **atomic** — there is no `await` between reading the flag and setting it, so no interleaving can slip through. The flag is cleared in a `finally` so the instance remains reusable for **sequential** runs.

Genuine concurrency (the documented, intended model) uses separate orchestrator instances. Verified working: two instances running simultaneously via `asyncio.gather` both complete correctly, each producing isolated files, content, progress logs, verification records and results (Section 9).

## 4. Exact Files Changed

| File | Change |
|---|---|
| `avora_backend/agent_orchestrator.py` | Production fix (single file) |
| `avora_backend/tests/test_s43_concurrency_isolation.py` | **New** regression test file (17 tests) |

## 5. Exact Production Changes (`avora_backend/agent_orchestrator.py`)

**`__init__` (line 70):** added a single new instance flag:

```python
self.task = task or Task(original_goal="")
self._goal_execution_active: bool = False
```

**`execute_goal` (lines 207-223):** became a thin concurrency-guarded wrapper over the original body (which is now the private `_execute_goal_impl`):

```python
if self._goal_execution_active:
    raise RuntimeError(
        "execute_goal is already running on this orchestrator. An "
        "AgentOrchestrator runs one active goal at a time; create a "
        "separate AgentOrchestrator instance for concurrent goals."
    )
self._goal_execution_active = True
try:
    return await self._execute_goal_impl(user_goal)
finally:
    self._goal_execution_active = False
```

The guard is placed **before** the original `self.task = Task(...)` / `self._interrupted = False` / `self._progress_log = []` resets (now at the top of `_execute_goal_impl`), so a rejected second call **cannot clobber the in-flight run's state**. The `finally` guarantees the flag resets even if the inner run raises or is cancelled, preserving sequential reuse.

No other production code was touched. The full original method body (attempts, plan, execution loop, error/interrupt handling, character emotion, progress emission, returns) is preserved verbatim inside `_execute_goal_impl`.

## 6. Task Isolation Model

Isolation is enforced structurally rather than by copying `self.task`:
- Each orchestrator instance owns exactly one `self.task`. Concurrent goals get their own instance (and therefore their own `Task`, `_progress_log`, `_interrupted`, `_character_state`).
- A second call on the SAME instance is rejected before it can touch the in-flight instance state, so the running task's `plan`, `completed_steps`, `observations`, `verification_results`, `errors`, `retry_count`, `recovery_count`, `current_step`, and `required_user_input` are never overwritten mid-flight.
- Regression test `test_no_shared_self_task_corruption_after_concurrency` and `test_two_concurrent_goals_isolated_real_files` prove each instance's `self.task` retains its own `original_goal`, `task_id`, `completed_steps`, observations and on-disk content after concurrent runs.

## 7. Cancellation Isolation

`cancel()` / `request_interrupt()` set that instance's `self._interrupted` / transition that instance's `self.task`. With separate instances, cancelling A only affects A. Tests:
- `test_cancel_a_while_b_runs` — cancel A → A `cancelled`; B continues to `VERIFYING` with all its files written; B not cancelled.
- `test_cancel_b_while_a_runs` — cancel B → B `cancelled`; A continues.
- `test_interrupt_a_while_b_runs` — interrupt A → A stops; B unaffected, not cancelled.

## 8. Confirmation / WAITING_FOR_USER Isolation

Confirmation is resolved by that instance's `user_input_callback`/`confirm_current_action`/`decline_current_action`, which only touch its own `self.task`. Two concurrent instances (A = HIGH-risk, B = LOW-risk) never share confirmation state. Tests:
- `test_confirmation_waiting_a_while_b_executes` — A pauses at `WAITING_FOR_USER`, its HIGH delete does **not** run; B completes its plan unaffected and is not in a waiting state.
- `test_confirm_a_while_b_executes_does_not_confirm_b` — confirming A resumes only A (delete executes); B completes its own two steps, never granted/advanced/blocked by A's confirmation.
- `test_decline_a_while_b_executes` — declining A cancels A only (delete never runs); B completes normally, not cancelled.

## 9. Real-Skill Evidence

`test_two_concurrent_goals_isolated_real_files` and the verification harness use the **real async `FileSkill`** with unique temp targets:
- A wrote `A1.txt`/`A2.txt` (content `AAA`), B wrote `B1.txt`/`B2.txt` (content `BBB`).
- Files independently inspected on disk; A's content never appears in B's files and vice-versa.
- A's progress log contains only `New task: goal A`; B's only `New task: goal B`; neither log leaks the other's events.
- Both runs end `VERIFYING` with correct `steps_completed` (no cross-attribution).

## 10. Adversarial Test Results

New file `avora_backend/tests/test_s43_concurrency_isolation.py` — **17 tests, all passing** (`-W error::RuntimeWarning` clean):

| # | Scenario | Result |
|---|---|---|
| 1 | Same-instance concurrent `execute_goal` → rejected, not corrupted | PASS |
| 2 | Concurrent different goals (real FileSkill) | PASS |
| 3 | Concurrent multi-step goals | PASS |
| 4 | Cancel A while B runs | PASS |
| 5 | Cancel B while A runs | PASS |
| 6 | Interrupt A while B runs | PASS |
| 7 | A waiting-for-confirmation while B executes | PASS |
| 8 | Confirm A while B executes | PASS |
| 9 | Decline A while B executes | PASS |
| 10 | A fails verification while B succeeds | PASS |
| 11 | A retries while B executes | PASS |
| 12 | A raises execution exception while B succeeds | PASS |
| 13 | Progress callbacks isolated | PASS |
| 14 | Verification records isolated | PASS |
| 15 | Final results associated with correct task | PASS |
| 16 | No shared `self.task` corruption after concurrency | PASS |
| 17 | Sequential reuse after concurrent rejection (flag resets) | PASS |

Deterministic overlap was achieved with `asyncio` events/`sleep` + `asyncio.gather`/`create_task`, and instance separation, ensuring the runs genuinely overlap on the event loop.

## 11. Full Regression Results

```
python -m pytest avora_backend/tests "avora backend/tests" -q
85 passed in ~13.5s   (68 baseline + 17 new S43)
-W error::RuntimeWarning: 85 passed
python -m compileall -q avora_backend   # exit 0
python -c "from avora_backend.agent_orchestrator import AgentOrchestrator"   # import OK
```

- **68-test baseline preserved** (62 prior + 6 S37): P0 #1 async dispatch, P0 #2 HIGH-risk confirmation gate, P0 #3 failed-step handling, P0 #4 trustworthy verification, S37 CANCELLED terminal-state protection — all still passing.
- Conflicts with standing conventions confirmed: `CONCURRENT_GUARD` uses the same atomic check-and-set / `finalysis` pattern already used for the S37 interrupt guards; `execute_goal` terminal convention preserved (successful run returns `"VERIFYING"`, failures return `"FAILED"` via enum name, recoveries `"failed"` via exception path).
- No commits made (per scope restriction).

## 12. Remaining Known Issues

- **S44** (cross-call resume) — out of scope; unchanged.
- **S9/S11** (private execution bypass), **S15** (execution-exception retry), **S34** (VERIFYING ambiguity), **S35** (COMPLETED), **S40** (cancellation timing) — out of scope; unchanged.
- **Per-call context isolation** (letting a single instance run multiple tasks on fully separate context objects) is a deliberate, larger refactor of every helper method. It is documented as the intended-but-future model; today the supported concurrency model is one instance per goal.
- The rejection is a `RuntimeError`; consumers that might legally desire advanced scheduling would need their own orchestration layer (multiple instances or a queue) built on top.

## 13. Before / After Behavior

| Aspect | Before (S43 bug) | After (S43 fixed) |
|---|---|---|
| Concurrent `execute_goal`, same instance | Silent corruption: tasks overwrite each other's `self.task`; wrong files/steps/progress/results | Second call **rejected** with a clear `RuntimeError`; first run completes correctly |
| Concurrent goals | Unsafe on one instance | **Separate instances** → truly concurrent, fully isolated (files, content, progress, verification, results) |
| Cancel / interrupt | Affected the wrong (shared) task | Isolated per instance — only the target instance's task is affected |
| Confirmation / WAITING_FOR_USER | Shared `self.task` could misattribute confirmation | Isolated per instance |
| Sequential reuse of one instance | Unintended overwrite semantics | Clean reset via `finally`; unchanged sequential behavior |
| Registry/API compatibility | — | No new public API; one private method rename (`_execute_goal_impl`); existing public surface unchanged |
