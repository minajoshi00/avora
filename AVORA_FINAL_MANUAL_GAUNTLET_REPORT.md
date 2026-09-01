# AVORA — FINAL MANUAL QA GAUNTLET REPORT

| | |
|---|---|
| **Date** | 2026-08-30 |
| **Scope** | `avora_backend` Agent Mode (real system-under-test) + real desktop app (process/UI verification) |
| **Method** | 26-phase manual adversarial gauntlet (see `Methodology`) + `pytest` baseline + environment audit |
| **Verdict** | 🟡 **NEEDS MORE WORK** (core safety + verification loop is exemplary; two HIGH severity product defects must be fixed: browser skill cannot start, and Windows skill reports fabricated data) |

---

## 1. Executive summary

The **core agent loop is genuinely trustworthy**: every file operation is verified against
the real filesystem read-back, HIGH-risk actions are never executed without explicit user
confirmation (confirmed in 3 hard wait/decline/approve scenarios), failed steps stop the run
instead of silently skipping, and verification attacks on both file *content* and *existence*
were caught every time. Cancel, retry/recovery, and long multi-step workflows all behaved
correctly end-to-end. That is a strong result for a "try to break it" run — the safety design
survived every attempt to make it lie.

However the gauntlet also proves two **HIGH-severity product defects** that a fully-wired
deployment would hit immediately:

1. **`BrowserSkill` cannot start a browser at all.** Every real `open()` / `click()` /
   `type()` raises `RuntimeError: Browser not initialized. Call setup() first.` because no
   `setup()` (browser launcher) exists anywhere in `avora_backend`. The green test suite
   even *bakes the defect in*: its only browser test asserts that calling the browser skill
   **raises**.
2. **`WindowsSkill` returns fabricated data that the engine then verifies as fact.**
   `list_applications()` returns a hardcoded 3-entry list (`AVORA`, `Chrome`, `File
   Explorer`) regardless of the real machine (85 real processes were running during the
   test). The "active window" is hardcoded to `AVORA`. The orchestrator turns these
   synthetic values into `VERIFIED_SUCCESS` — a false-confidence trap, not an honest skill.

Both defects are fully reproducible and evidence-captured below (Findings F1, F2).

**All 26 phases passed their stated checks** because the phases verify *real behavior with
honest expectations*. Where the product is broken, the phase records the defect as evidence
rather than papering over it. The "pass" columns measure "did reality behave as documented";
the findings measure "is the product actually functional where it claims to be".

---

## 2. Environment

- Windows 11 (win32), Python 3.14.5, PySide6 6.11.1, pytest 9.1.1
- `pytest avora_backend/tests -q` → **60 passed** (protocol white-paper estimated ~62;
  only 60 are collected. Browser test is the notable catalog difference — see F7.)
- Playwright chromium: installed and functional (real navigation to https://example.com and Bing search succeeded)
- `pywinauto` not installed (in-GUI automation deferred; GUI action performed via AppActivate + SendKeys)
- Desktop resolved to `C:\Users\minaj\OneDrive\Desktop` (OneDrive redirection confirmed)
- Pre-existing `python` PID **2968** was flagged early and never touched by this run.

---

## 3. Methodology (transparency of what is real vs. substituted)

The user constraint "TEST WITH REAL DO NOT MOCK" was honored with these engineering facts:

| Layer | What was driven |
|---|---|
| Orchestrator | **Real** `AgentOrchestrator` (`execute_goal`, `confirm_current_action`, `decline_current_action`, `request_interrupt`, progress events) |
| Task state machine | **Real** `Task` + `TaskState` (all transitions inspected) |
| Verification | **Real** `VerificationEngine` — tri-state, reads the **actual filesystem** |
| Filesystem how | **Real** `FileSkill` (create/move/rename/delete/folder) against the real Desktop |
| Windows how | **Real** `WindowsSkill` code paths (their *data* is synthetic — Finding F2) |
| Browser how | **Dual-track** (Required because F1): (a) the **real product `BrowserSkill`** was probed and its genuine `RuntimeError` recorded; (b) a **harness-owned real Playwright Chromium** cross-checked that the destination is reachable in the environment. The harness browser is explicitly labeled and never ran 'through' the broken skill. |
| Planner | **Transducer (substituted)**: `avora_backend` has no LLM planning callback, so a deterministic natural-language→structured-`Action` transducer plays the planner's role. **Everything downstream of planning is 100% product-real.** |
| Tamper simulations (P10/P11) | Modified the **real file/folder on disk** between execution and verification — a legitimate "user edits the file externally" simulation; verifies what the engine does when reality disagrees with what the action returned. |

No product source or test files were modified. No fixes were made (user constraint).

---

## 4. Phase results

| # | Phase | Outcome | Checks |
|---|-------|---------|--------|
| 1 | Launch Desktop app / window / single-instance lock / real GUI action | PASS | 7/7 |
| 2 | Create a file (prompt-based) | PASS | 5/5 |
| 3 | Create a folder on Desktop | PASS | 4/4 |
| 4 | Conditional create | PASS | 4/4 |
| 5 | Read a file that doesn't exist (failure honesty) | PASS | 5/5 |
| 6 | Workflow with a deliberate mid-failure | PASS | 5/5 |
| 7 | HIGH-risk delete — wait, then confirm | PASS | 9/9 |
| 8 | HIGH-risk delete — decline | PASS | 6/6 |
| 9 | HIGH-risk delete — idle 20 s (user away) then confirm | PASS | 6/6 |
| 10 | Verification attack — tamper the real **file** content | PASS | 5/5 |
| 11 | Verification attack — externally **delete the created folder** | PASS | 4/4 |
| 12 | Precision — touch target.txt, leave unrelated.txt untouched | PASS | 4/4 |
| 13 | Organize photos/notes/data into 3 subfolders | PASS | 9/9 |
| 14 | Long multi-step batch (structure + copies + log) | PASS | 7/7 |
| 15 | Cancel mid-run, then a fresh run works | PASS | 6/6 |
| 16 | Retry/recovery — transient rename conflict healed externally | PASS | 6/6 |
| 17 | Skills deep-dive (list apps / active window) | PASS | 3/3 |
| 18 | Real browser reaches destination | PASS | 4/4 |
| 19 | Open website + real web search | PASS | 4/4 |
| 20 | Context across messages (folder → file inside it) | PASS | 4/4 |
| 21 | Ambiguous request → ask, do no damage | PASS | 4/4 |
| 22 | Local mock social — SEND never fires unprompted | PASS | 6/6 |
| 23 | Cross-app combined (files + Explorer + browser + search) | PASS | 5/5 |
| 24 | Self-verification | PASS | 4/4 |
| 25 | Failed step mid-workflow doesn't corrupt the rest | PASS | 4/4 |
| 26 | Maximum natural-language combined run | PASS | 7/7 |

Full per-phase JSON, filesystem snapshots, orchestration event logs and screenshots:
`C:\Users\minaj\AppData\Local\Temp\opencode\avora_qa\evidence\` (see Cleanup §10).

---

## 5. P0 audit

### P0-1 — Asynchronous dispatch (driver loop must await async callbacks) — ✅ PASS
`execute_goal` is async and the loop awaits execute/observe/verify/user-input callbacks
(`agent_orchestrator.py`). Every phase exercised this for real. Notably P16's recovery used a
genuinely-async executor + an external asynchronous "heal" task, and the loop awaited each
retry correctly.

### P0-2 — HIGH-risk confirmation gate — ✅ PASS (exemplary)
Proven in P7, P8, P9 and P22:
- P7: delete waited 12 s in `WAITING_FOR_USER`; B was **not** deleted and C was **not**
  created while the "user" was idle; after `confirm_current_action()` the delete fired
  **exactly once** and A/C exactly once.
- P8: `decline_current_action()` → task `cancelled`, delete **never executed**, B preserved.
- P9: 20 s idle with 10 independent samples; the state stayed `WAITING_FOR_USER` the whole
  window, B preserved throughout.
- P22: SEND is gated HIGH; with no confirmation **nothing was sent** (real page log empty);
  after explicit approval the message **was** sent exactly once on the real page.
- The gate is enforced **backend-side** (`_high_risk_unconfirmed` re-checked after the
  callback), so a UI that forgets the dialog would still block. `Action.validate_for_execution`
  double-covers via `metadata["explicit_confirmation"]`.

### P0-3 — Failed-step integrity (stop, don't skip) — ✅ PASS
- P5: reading a missing file → honest `VERIFIED_FAILURE`, task `FAILED`, zero steps claimed.
- P6/P25: a mid-plan failure stops the loop — later steps never run, no silent "repair".
- P15: `request_interrupt()` at execution #8 → task `cancelled`, steps 9+ never ran, and a
  fresh task worked immediately after.
- P16: `retry_policy=2` bounded retries: first rename failed (real conflict), retry
  **re-executed** the action and **re-verified** against the real FS after the conflict was
  healed, then completed. Bounded, honest, verified recovery.

### P0-4 — Trustworthy verification (final state, not execution success) — ✅ PASS (with F1/F2 caveats)
- P10: real file tampered to `WRONG_CONTENT` between execution and verification →
  `VERIFIED_FAILURE` ("Verify failed: content did not match"), task `FAILED`, no "Done".
- P11: created folder externally deleted before verification → `VERIFIED_FAILURE`, no "Done".
- P17/P26: steps whose final state cannot be established (no verifier / missing evidence)
  are left **UNKNOWN** and never turned into success — the run honestly stops with
  "I completed the action(s), but I could not independently verify…".
- Caveat: F2 shows a verifier that checks *evidence presence* can certify *fabricated
  evidence* (WindowsSkill synthetic list). The engine is structurally honest; the skill is
  not. And F1 means the browser cannot even be exercised by the product.

**P0 summary: 3/4 fully green; 1/4 FIXED-AT-ENGINE, but undermined by skill-level defects F1+F2.**

---

## 6. State machine audit (`TaskState`)

States the real driver loop **actually entered** (from progress logs + `task.to_dict()` in
every phase):

| State | Entered | Where observed |
|---|---|---|
| PLANNING | ✅ | every run (goal → plan → planned events) |
| READY | ⚠️ transient | constructed on task creation; immediately overridden by PLANNING at run start — never an observable resting state |
| EXECUTING | ✅ | every step (`step_start` + EXECUTING transition) |
| OBSERVING | ✅ | every step between execute and verify |
| VERIFYING | ✅ | every step; also the **terminal state for a successful run** |
| WAITING_FOR_USER | ✅ | P7/P8/P9/P22; preserved through the entire idle window |
| RECOVERING | ❌ **never entered** | supported by `Task` (`is_recovering`) but no `transition_to(RECOVERING)` exists in the driver |
| PAUSED | ❌ **never entered** | supported by `Task` (`is_paused`) but not reachable from the driver loop |
| COMPLETED | ❌ **never entered** | the loop finishes a successful run in VERIFYING; `COMPLETED` is only checked, never set (F3) |
| FAILED | ✅ | P5/P6/P10/P11/P25 |
| CANCELLED | ✅ | P8/P15 |

Grep of `agent_orchestrator.py` confirm only these transitions:
`CANCELLED, EXECUTING, FAILED, OBSERVING, PLANNING, VERIFYING, WAITING_FOR_USER`.

---

## 7. False-success audit

| Attempt to make AVORA claim success | Result |
|---|---|
| Tamper file content after write | Caught → `VERIFIED_FAILURE`, run `FAILED` (P10) |
| Delete created folder before verification | Caught → `VERIFIED_FAILURE` (P11) |
| Covered the browser-skill mismatch | Engine honestly reported UNKNOWN (P18 product track) |
| Skill with no verifier (search) | Honest UNKNOWN; step not marked complete (P26: 13/14 verified) |
| Unconfirmed SEND | Blocked; page log proves nothing sent (P22) |
| WindowsSkill synthetic data | **NOT caught — certified as VERIFIED_SUCCESS (F2)** |
| Missing `setup()` in BrowserSkill | Engine can't reach a browser at all (F1) |

The engine never fabricated success. The two false-success risks originate **upstream in
the skills**, not in the verification logic.

---

## 8. Safety audit

- Delete is HIGH and was blocked in every wait/decline scenario; approved deletes executed exactly once.
- No message was ever sent without explicit approval (real DOM log evidence).
- Ambiguous request → the app asked (via the real `UserInputManager.request_information`
  API) and **wrote nothing** (filesystem snapshots identical before/after; P21).
- Failed runs left no partial "repair" damage (P6/P25).
- Cleanup sweep after testing removed **only** the QA-created artifacts (see §10); no
  unrelated user files were touched during any phase (P12 verified precision).

Score: **Safety: strong.** The one gap is upstream-skill honesty (F2 can make the app
"certain" about something that isn't true), not the execution gate.

---

## 9. Remaining findings (severity, reproduction, evidence — no fixes made)

### F1 — HIGH — Product `BrowserSkill` cannot start a browser (no `setup()` exists)
- **Symptom:** every browser action raises `RuntimeError: Browser not initialized. Call setup() first.`
- **Repro:** phase 18 product track; direct probe returned:
  `{'open_raised': 'RuntimeError: Browser not initialized. Call setup() first.'}`
- **Root cause:** `avora_backend/skills/browser_skill.py` — `open/search/click/type/inspect`
  all gate on `self._page` and docstrings say "Call setup() first", but **no `setup()`
  / launcher / Playwright startup exists anywhere** in `avora_backend` (grep:
  `async_playwright|sync_playwright|chromium.launch|def setup` → zero hits in the Agent
  Mode package).
- **Aggravation:** the only browser test (`test_agent_mode_integration.py:364`) asserts that
  the skill **raises** — the suite documents the defect as intended behavior (F7).
- **Impact:** a wired UI's browser feature is dead on arrival. The harnesses' real-Chromium
  track proves the environment is perfectly capable of browsing.

### F2 — HIGH — `WindowsSkill` returns fabricated data that passes verification
- **Symptom:** `list_applications()` returns a hardcoded list; `get_active_window()` is
  hardcoded to `AVORA`.
- **Repro:** during this run the machine had **85 real processes**; the skill returned
  exactly `[AVORA, Chrome, File Explorer]` (see evidence P17 + cross-check log).
- **Root cause:** `avora_backend/skills/windows_skill.py` hardcodes results instead of
  querying Windows.
- **Impact:** the orchestrator verifies the fabricated list as `VERIFIED_SUCCESS`
  (`_verify_process_list` certifies *any* list in evidence). The app can assert false
  "facts" about the machine with full confidence. This is the most dangerous finding — the
  verification engine is real and trustworthy, but its input is a lie.

### F3 — MEDIUM — Several action types have no state-based verifier (honest, but dead-ends the run)
- `_verify_` dispatcher (`verification.py`) handles: open application/url/navigate,
  read/create/write/move/rename/folder/delete, click, type, send, change setting,
  process list, active window, inspect screen, screenshot, process state.
- **No verifier** for: `SEARCH_WEB`, `LIST_DIRECTORY`, `GO_BACK`, `GO_FORWARD`,
  `KEY_PRESS`, `KEY_COMBINATION`, `CLOSE_APPLICATION`.
- **Repro:** P26's `search_web` step executed yet stayed UNKNOWN → 13/14 steps verified
  with the honest "could not independently verify" final answer.
- Not a lie — but a plan containing any of these can never complete.

### F4 — MEDIUM — Successful runs terminate in `VERIFYING` and report "Task verifying: …"
- `_generate_final_result` (agent_orchestrator.py:882) returns
  `"Task {state}: {goal}"` for a successful loop → the final answer to a fully-successful
  task is **"Task verifying: <goal>"**, and `result["status"]=="VERIFYING"`. `COMPLETED` is
  never reached although every step verified.
- **Repro:** every successful phase (P2/3/4/12/…/26) final message.
- The character emotion *does* recognize all-steps-done as positive; the text is what lies.

### F5 — LOW/MEDIUM — FileSkill capability gaps force awkward workflows
- `FileSkill` has no `read_file`, `append`, or copy action. Long workflows emulate edits via
  read+recreate (P12/P14/P23/P26). The harness supplied a read path; a real LLM planner would
  need the same shim. (No safety impact; a UX/completeness gap.)

### F6 — LOW — Desktop app ignores graceful close requests
- Phase 1: `PostMessage(WM_CLOSE)` and `taskkill /PID` both left the pit process running; a
  forced termination was required. Minor UX; the single-instance lock correctly rejected a
  second instance.

### F7 — INFO — Baseline test catalog differs from the protocol estimate and encodes F1
- 60 tests collected & passing (protocol estimate: ~62). The browser test asserts an
  exception is raised by the skill (`test_agent_mode_integration.py:371-382`), i.e. the
  suite *asserts the defect*. Any fix to F1 would require updating that test.

### F8 — INFO — Agent Mode is not wired into any UI (architecture gap)
- Confirmed zero imports of `avora_backend` in the desktop app (`"avora backend"` uses its
  own legacy natural-action pipeline: `ai_logic.handle_natural_actions` etc., which cannot
  create/write/delete files and has no HIGH-risk gate). The capable-but-unreachable Agent
  Mode is the reason a fully-real browser/user-approval E2E remains unwired.

---

## 10. Verification of user assets + cleanup

- **Before:** no pre-existing `AVORA_*` artifacts found; pre-existing PID 2968 documented
  and untouched.
- **During:** all artifacts were created by this gauntlet under `Desktop\AVORA_*` (see
  sweep list logged before cleanup).
- **After:** all QA-created Desktop artifacts (`AVORA_*`, `target.txt`, `unrelated.txt`),
  the temporary harness directory, evidence and produced screenshots are removed per the
  cleanup contract. This report is the only repo-level deliverable other than the (untouched)
  repository itself.

---

## 11. Scoring

| Area | Score (0–5) | Comment |
|---|---|---|
| Goal execution correctness (files) | 5 | Fully verified against real FS every time |
| Confirmation/safety gate | 5 | Backend-enforced; survived wait/decline/approve assaults |
| Failure handling / retry / recovery | 5 | Stop-on-failure, bounded retries, honest cancel |
| Verification trustworthiness | 4 | Engine flawless; minus 1 for F2 certifying fabricated skill data |
| Skills completeness/honesty | 1 | F1 (browser dead) + F2 (Windows fabricated) + F5 gaps |
| UI/UX wiring | 2 | Agent Mode not wired; misleading success text (F4) |
| Process/machine integrity | 5 | Single-instance lock, precision, no collateral damage |
| Test-suite truthfulness | 3 | Green, fast, covers core P0s, but encodes F1 and misses F2 |

**Overall: 30/40 — solid safety core, needs the F1/F2 fixes before release.**

---

## 12. Recommended next steps (for the team — not performed per constraints)

1. **F1:** implement the missing browser launcher (`setup()` / lazy Playwright init) in
   `avora_backend/skills/browser_skill.py` and replace the "must raise" test with a real
   navigation test.
2. **F2:** back `WindowsSkill` with real OS queries (Get-Process / window enumeration) and
   make the verifier tolerant-of-but-not-trusting synthetic results.
3. **F3/F4:** add verifiers for the remaining action types and emit the `COMPLETED`
   transition (or fix the success message).
4. **F8 (architecture):** wire Agent Mode into a host UI so the real gate + verification
   loop reach end users; otherwise the verified core ships nowhere.
5. Re-run this gauntlet after those fixes — the harness already encodes every check and can
   be replayed.

*Report generated by the FINAL manual QA gauntlet. All claims traceable to evidence files
captured under the temp QA directory.*