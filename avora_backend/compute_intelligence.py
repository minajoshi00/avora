# ============================================================
# COMPUTER INTELLIGENCE — AVORA (additive layer on Agent Mode)
# ============================================================
# Turns AVORA from "execute a fixed sequence" into "an intelligent
# desktop operator": it holds a structured model of the computer's
# current state, OBSERVES before and after acting, reasons about
# whether reality matches expectation, chooses the next semantic
# action from the latest observation, CLASSIFIES failures, and picks
# a state-aware recovery strategy.
#
# This module is 100% additive. It does NOT replace AgentOrchestrator,
# the verification engine, the confirmation gates, or the skills. It
# exposes hooks intended to be used as the orchestrator's
# plan/observe/recovery callbacks (or run standalone in tests).
#
# Honesty rules (Phase 13):
#   - Every observation records a SOURCE.
#   - Every fact carries a CERTAINTY (OBSERVED / INFERRED / ASSUMED).
#   - Nothing is silently upgraded from ASSUMED/INFERRED to OBSERVED.
# ============================================================

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Sequence


# -----------------------------------------------------------------
# Observation source + certainty (Phase 13 — no fake vision)
# -----------------------------------------------------------------

class ObservationSource(Enum):
    DOM = "dom"
    ACCESSIBILITY = "accessibility"
    OCR = "ocr"
    SCREENSHOT_VISION = "screenshot_vision"
    APP_API = "app_api"
    FILESYSTEM = "filesystem"
    WINDOW_STATE = "window_state"
    PROCESS_STATE = "process_state"
    UNKNOWN = "unknown"


class Certainty(Enum):
    """How confident the agent is that a fact is true."""
    OBSERVED = "observed"   # real observation mechanism produced it
    INFERRED = "inferred"   # derived from observed evidence
    ASSUMED = "assumed"     # default / guess, no evidence yet
# -----------------------------------------------------------------
# Computer World Model (Phase 2)
# -----------------------------------------------------------------

@dataclass
class BrowserState:
    url: Optional[str] = None
    title: Optional[str] = None
    elements: List[Dict[str, Any]] = field(default_factory=list)
    source: ObservationSource = ObservationSource.UNKNOWN


@dataclass
class ScreenState:
    width: int = 0
    height: int = 0
    cursor: Optional[Dict[str, int]] = None
    source: ObservationSource = ObservationSource.UNKNOWN


@dataclass
class ComputerState:
    """Structured representation of the computer's current state.

    Not tied to any single application. Fields are populated by
    OBSERVED facts; uninspected fields stay None/empty (never
    fabricated).
    """

    active_app: Optional[str] = None
    active_window: Optional[str] = None
    browser: BrowserState = field(default_factory=BrowserState)
    open_windows: List[str] = field(default_factory=list)
    visible_elements: List[Dict[str, Any]] = field(default_factory=list)
    focused_element: Optional[Dict[str, Any]] = None
    screen: ScreenState = field(default_factory=ScreenState)
    open_files: List[str] = field(default_factory=list)
    task_context: Dict[str, Any] = field(default_factory=dict)
    # observe-after-act bookkeeping
    last_action: Optional[str] = None
    expected_state: Dict[str, Any] = field(default_factory=dict)
    observed_state: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    updated_at: float = field(default_factory=time.time)

    def update(self, **fields: Any) -> None:
        for key, value in fields.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = time.time()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "active_app": self.active_app,
            "active_window": self.active_window,
            "browser": {
                "url": self.browser.url,
                "title": self.browser.title,
                "elements": len(self.browser.elements),
            },
            "open_windows": list(self.open_windows),
            "visible_elements": [
                {k: v for k, v in e.items() if k in ("text", "type", "selector")}
                for e in self.visible_elements
            ],
            "focused_element": self.focused_element,
            "screen": {
                "width": self.screen.width,
                "height": self.screen.height,
                "cursor": self.screen.cursor,
            },
            "task_context": dict(self.task_context),
            "last_action": self.last_action,
            "expected_state": dict(self.expected_state),
            "observed_state": dict(self.observed_state),
            "confidence": self.confidence,
        }

    def summarize(self) -> str:
        """Short human-readable description used for reasoning/chat context."""
        parts = []
        if self.active_app:
            parts.append(f"active app: {self.active_app}")
        if self.active_window:
            parts.append(f"window: {self.active_window}")
        if self.browser.url:
            parts.append(f"url: {self.browser.url}")
        if self.browser.title:
            parts.append(f"page: {self.browser.title}")
        if self.browser.elements:
            parts.append(f"{len(self.browser.elements)} page elements")
        if self.visible_elements:
            texts = [e.get("text") for e in self.visible_elements if e.get("text")]
            if texts:
                parts.append("visible: " + " | ".join(texts[:8]))
        return "; ".join(parts) or "no state observed yet"


# -----------------------------------------------------------------
# Observation record (Phase 3 / Phase 13)
# -----------------------------------------------------------------

@dataclass
class Observation:
    source: ObservationSource
    certainty: Certainty
    payload: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source.value,
            "certainty": self.certainty.value,
            "payload": dict(self.payload),
            "error": self.error,
        }
# -----------------------------------------------------------------
# Failure classification + state-aware recovery (Phase 8)
# -----------------------------------------------------------------

class FailureCategory(Enum):
    TARGET_NOT_FOUND = "target_not_found"
    WRONG_STATE = "wrong_state"
    WRONG_APPLICATION = "wrong_application"
    NAVIGATION_FAILURE = "navigation_failure"
    TIMING_LOADING = "timing_loading"
    PERMISSION_ISSUE = "permission_issue"
    AUTH_REQUIRED = "auth_required"
    UI_CHANGED = "ui_changed"
    EXECUTED_BUT_NO_RESULT = "executed_but_no_result"
    AMBIGUOUS_STATE = "ambiguous_state"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    WAIT_AND_REOBSERVE = "wait_and_reobserve"
    INSPECT_ALTERNATIVE = "inspect_and_alternate"
    REPLAN = "replan"
    REQUEST_PERMISSION = "request_permission"
    REQUEST_AUTH = "request_auth"
    RETRY_ACTION = "retry_action"
    STOP_AND_REPORT = "stop_and_report"


_RECOVERY_MAP: Dict[FailureCategory, RecoveryStrategy] = {
    FailureCategory.TARGET_NOT_FOUND: RecoveryStrategy.INSPECT_ALTERNATIVE,
    FailureCategory.WRONG_STATE: RecoveryStrategy.REPLAN,
    FailureCategory.WRONG_APPLICATION: RecoveryStrategy.REPLAN,
    FailureCategory.NAVIGATION_FAILURE: RecoveryStrategy.REPLAN,
    FailureCategory.TIMING_LOADING: RecoveryStrategy.WAIT_AND_REOBSERVE,
    FailureCategory.PERMISSION_ISSUE: RecoveryStrategy.REQUEST_PERMISSION,
    FailureCategory.AUTH_REQUIRED: RecoveryStrategy.REQUEST_AUTH,
    FailureCategory.UI_CHANGED: RecoveryStrategy.INSPECT_ALTERNATIVE,
    FailureCategory.EXECUTED_BUT_NO_RESULT: RecoveryStrategy.REPLAN,
    FailureCategory.AMBIGUOUS_STATE: RecoveryStrategy.WAIT_AND_REOBSERVE,
    FailureCategory.UNKNOWN: RecoveryStrategy.STOP_AND_REPORT,
}


class FailureClassifier:
    """Map a failed action + observation to a FailureCategory."""

    _PERMISSION_HINTS = ("permission", "denied", "access denied", "not allowed",
                         "authorization", "forbidden", "401", "403")
    _AUTH_HINTS = ("sign in", "log in", "login", "authenticate",
                   "credential", "password", "otp", "verify your identity")
    _LOADING_HINTS = ("loading", "wait", "spinner", "please wait", "still loading")

    def classify(self, action: Dict[str, Any], state: ComputerState,
                 evidence: Optional[List[str]] = None) -> FailureCategory:
        evidence = [str(e).lower() for e in (evidence or [])]
        evidence_text = " ".join(evidence).lower()
        action_text = f"{action.get('action_type') or action.get('action', '')} {action.get('target') or ''}".lower()

        if any(h in evidence_text for h in self._PERMISSION_HINTS):
            return FailureCategory.PERMISSION_ISSUE
        if any(h in evidence_text for h in self._AUTH_HINTS):
            return FailureCategory.AUTH_REQUIRED
        if any(h in evidence_text for h in self._LOADING_HINTS):
            return FailureCategory.TIMING_LOADING

        target = str(action.get("target") or "")
        expected_app = str(action.get("expected_app") or "")
        if expected_app:
            if state.active_app and _norm(expected_app) not in _norm(state.active_app):
                return FailureCategory.WRONG_APPLICATION
            if not state.active_app:
                return FailureCategory.WRONG_APPLICATION

        if "open_url" in action_text or "navigate" in action_text:
            if state.browser.url is None:
                return FailureCategory.TIMING_LOADING
            expected_url = action.get("expected_url") or _base_url_of(target)
            if expected_url and _norm(expected_url) not in _norm(state.browser.url or ""):
                return FailureCategory.NAVIGATION_FAILURE

        if "click" in action_text or "type" in action_text or "select" in action_text:
            if target and not _element_matches(state, target):
                if not state.browser.elements and not state.visible_elements:
                    return FailureCategory.TIMING_LOADING
                return FailureCategory.TARGET_NOT_FOUND

        if action.get("action_type") not in ("inspect_screen", "get_active_window"):
            if action.get("verify") is False and state.confidence < 0.5:
                return FailureCategory.EXECUTED_BUT_NO_RESULT

        if action.get("verify") is None:
            return FailureCategory.AMBIGUOUS_STATE
        return FailureCategory.UNKNOWN

    @staticmethod
    def recovery_for(category: FailureCategory) -> RecoveryStrategy:
        return _RECOVERY_MAP.get(category, RecoveryStrategy.STOP_AND_REPORT)
# -----------------------------------------------------------------
# Desktop observation — real Windows perception (Phase 4)
# -----------------------------------------------------------------

@dataclass
class DesktopObservation:
    """Result of a single real desktop observation (Phase 4).

    Every field is either OBSERVED from a real mechanism or None/empty
    when the mechanism is unavailable.  ``confidence`` is an aggregate
    certainty that reflects how much of the above came from real sources.
    """

    active_app: Optional[str] = None
    active_window: Optional[str] = None
    open_windows: List[str] = field(default_factory=list)
    screen_width: int = 0
    screen_height: int = 0
    cursor: Optional[Dict[str, int]] = None
    screenshot: Optional[Any] = None          # PIL Image | None
    detected_text: Optional[str] = None       # OCR / text — str | None
    responsive: bool = False
    confidence: float = 0.0
    source: ObservationSource = ObservationSource.UNKNOWN
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None


# -----------------------------------------------------------------
# Observer — observe before AND after acting (Phase 3)
# -----------------------------------------------------------------

class ComputerObserver:
    """Coordinates OBSERVE -> REASON -> ACT and ACT -> OBSERVE -> VERIFY,
    maintaining the ComputerState world model with explicit sources.

    Uses real Windows APIs (ctypes) when available; degrades gracefully
    to a minimal window-only model if vision libraries are absent, and to
    an empty-but-valid state on non-Windows platforms.
    """

    def __init__(self) -> None:
        self.state = ComputerState()
        self.observation_log: List[Observation] = []

    # -- low-level record -------------------------------------------------
    def record(self, source: ObservationSource, payload: Dict[str, Any],
               certainty: Certainty = Certainty.OBSERVED) -> Observation:
        obs = Observation(source=source, certainty=certainty, payload=dict(payload))
        self.observation_log.append(obs)
        self._merge(obs)
        return obs

    # -- observe BEFORE acting -------------------------------------------
    def observe_before_act(self, expected: Dict[str, Any]) -> List[str]:
        """Return anomalies between current state and what the next action
        expects. Empty list = ready to act."""
        issues: List[str] = []

        expected_app = expected.get("active_app")
        if expected_app:
            if not self.state.active_app:
                issues.append(f"application_not_observed:{expected_app}")
            elif _norm(expected_app) not in _norm(self.state.active_app):
                issues.append(f"wrong_application:{expected_app}!={self.state.active_app}")

        expected_url = expected.get("url")
        if expected_url:
            if not self.state.browser.url:
                issues.append(f"page_not_observed:{expected_url}")
            elif _norm(expected_url) not in _norm(self.state.browser.url):
                issues.append(f"wrong_page:{expected_url}!={self.state.browser.url}")

        expected_element = expected.get("element")
        if expected_element:
            if not _element_matches(self.state, expected_element):
                if not self.state.browser.elements and not self.state.visible_elements:
                    issues.append("loading_state:no_elements")
                else:
                    issues.append(f"target_not_found:{expected_element}")

        expected_open = expected.get("open_window")
        if expected_open and expected_open not in self.state.open_windows:
            issues.append(f"window_not_open:{expected_open}")

        return issues

    # -- observe AFTER acting --------------------------------------------
    def observe_after_act(self, action: str, expected: Dict[str, Any],
                          confidence: float) -> None:
        """Record the post-action expectation so verification can compare."""
        self.state.last_action = action
        self.state.expected_state = dict(expected)
        self.state.observed_state = self._observed_facts()
        self.state.confidence = confidence

    def _observed_facts(self) -> Dict[str, Any]:
        facts: Dict[str, Any] = {}
        if self.state.active_app:
            facts["active_app"] = self.state.active_app
        if self.state.active_window:
            facts["active_window"] = self.state.active_window
        if self.state.browser.url:
            facts["url"] = self.state.browser.url
        if self.state.browser.title:
            facts["page_title"] = self.state.browser.title
        if self.state.visible_elements:
            facts["visible_elements"] = [e.get("text") for e in self.state.visible_elements if e.get("text")]
        return facts

    def detected_mismatch(self) -> bool:
        """True if the observed facts contradict the post-action expectation."""
        expected = self.state.expected_state
        observed = self.state.observed_state
        if expected.get("active_app") and observed.get("active_app"):
            if _norm(expected["active_app"]) not in _norm(observed["active_app"]):
                return True
        if expected.get("url") and observed.get("url"):
            if _norm(expected["url"]) not in _norm(observed["url"]):
                return True
        return False

    # -- merge observation into the world model --------------------------
    def _merge(self, obs: Observation) -> None:
        p = obs.payload
        if obs.certainty is Certainty.ASSUMED:
            # Never overwrite a real observation with an assumption.
            return
        for key in ("active_app", "active_window"):
            if p.get(key):
                setattr(self.state, key, p[key])
        if p.get("open_windows") is not None:
            self.state.open_windows = list(p["open_windows"])
        if p.get("visible_elements") is not None:
            self.state.visible_elements = list(p["visible_elements"])
        if p.get("focused_element"):
            self.state.focused_element = p["focused_element"]
        if p.get("open_files") is not None:
            self.state.open_files = list(p["open_files"])
        if p.get("browser"):
            b = p["browser"]
            if b.get("url"):
                self.state.browser.url = b["url"]
            if b.get("title"):
                self.state.browser.title = b["title"]
            if b.get("elements") is not None:
                self.state.browser.elements = list(b["elements"])
            self.state.browser.source = obs.source
        if p.get("screen"):
            s = p["screen"]
            if s.get("width"):
                self.state.screen.width = s["width"]
            if s.get("height"):
                self.state.screen.height = s["height"]
            if s.get("cursor") is not None:
                self.state.screen.cursor = s["cursor"]
        self.state.updated_at = time.time()

    # -- real desktop observation --------------------------------------------

    def observe_real(self, include_screenshot: bool = False,
                     include_ocr: bool = False) -> DesktopObservation:
        """Perform ONE real desktop observation cycle and merge it into the
        world model (Phase 2/8).

        Uses real Windows APIs (user32/psapi) for the active window, open
        windows, screen geometry and cursor. Screenshot (mss) and OCR
        (pytesseract) are opt-in ONLY — never run per-observation by default
        (Phase 13: strategic, not continuous, perception).

        Every value is genuinely OBSERVED or left None/empty when the
        mechanism is unavailable — never assumed.
        """
        active = self._get_active_window()
        obs = DesktopObservation(
            active_app=active.get("app") or None,
            active_window=active.get("title") or None,
            open_windows=self._get_open_windows(),
        )

        geom = self._get_screen_geometry()
        obs.screen_width = geom.get("width", 0)
        obs.screen_height = geom.get("height", 0)
        obs.cursor = self._get_cursor_pos()

        # confidence reflects how much came from REAL mechanisms
        if obs.active_app and obs.active_window and obs.screen_width:
            obs.confidence = 0.99
        elif obs.active_window or obs.open_windows:
            obs.confidence = 0.85
        else:
            obs.confidence = 0.3
        obs.source = (ObservationSource.WINDOW_STATE
                      if self._windows_available() else ObservationSource.UNKNOWN)

        # Only pay the screenshot/OCR cost when explicitly requested.
        if include_screenshot:
            obs.screenshot = self._capture_screenshot()
            if include_ocr and obs.screenshot is not None:
                obs.detected_text = self._extract_text(obs.screenshot)

        # Merge REAL observations into the world model with explicit source.
        payload: Dict[str, Any] = {}
        if obs.active_app:
            payload["active_app"] = obs.active_app
        if obs.active_window:
            payload["active_window"] = obs.active_window
        if obs.open_windows:
            payload["open_windows"] = obs.open_windows
        if obs.screen_width and obs.screen_height:
            payload["screen"] = {"width": obs.screen_width,
                                 "height": obs.screen_height,
                                 "cursor": obs.cursor}
        if payload:
            self.record(obs.source, payload, Certainty.OBSERVED)
        return obs

    def _windows_available(self) -> bool:
        """True when running on a Windows build with ctypes access."""
        if not sys.platform.startswith("win"):
            return False
        try:
            import ctypes  # noqa: F401
            ctypes.windll  # raises AttributeError on some non-Windows
            return True
        except (AttributeError, OSError):
            return False

    def _get_active_window(self) -> Dict[str, Any]:
        """Real active-window + process detection via Windows user32/psapi."""
        result: Dict[str, Any] = {"title": "", "app": "", "pid": 0, "source": ObservationSource.WINDOW_STATE}
        if not self._windows_available():
            result["source"] = ObservationSource.UNKNOWN
            return result
        try:
            import ctypes
            import ctypes.wintypes as wintypes

            user32 = ctypes.windll.user32

            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return result

            # Window title (may be empty for some tool windows)
            length = user32.GetWindowTextLengthW(hwnd)
            title = ""
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.strip()

            # Process ID -> process name
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_name = ""
            try:
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x0400 | 0x0010, False, pid.value)
                if handle:
                    exe_buf = ctypes.create_unicode_buffer(260)
                    size = wintypes.DWORD(260)
                    if ctypes.windll.psapi.GetModuleBaseNameW(handle, None, exe_buf, size):
                        process_name = exe_buf.value.strip()
                    kernel32.CloseHandle(handle)
            except Exception:
                pass

            result["title"] = title
            result["app"] = process_name
            result["pid"] = pid.value
            return result
        except Exception:
            result["source"] = ObservationSource.UNKNOWN
            return result

    def _get_open_windows(self) -> List[str]:
        """Enumerate visible top-level windows via EnumWindows."""
        windows: List[str] = []
        if not self._windows_available():
            return windows
        try:
            import ctypes
            import ctypes.wintypes as wintypes

            user32 = ctypes.windll.user32
            EnumWindowProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

            def _enum_cb(hwnd, lParam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        title = buf.value.strip()
                        if title:
                            windows.append(title)
                return True

            user32.EnumWindows(EnumWindowProc(_enum_cb), 0)
        except Exception:
            pass
        return windows

    def _get_screen_geometry(self) -> Dict[str, int]:
        """Real screen dimensions via GetSystemMetrics."""
        geom = {"width": 0, "height": 0}
        if not self._windows_available():
            return geom
        try:
            import ctypes
            user32 = ctypes.windll.user32
            geom["width"] = int(user32.GetSystemMetrics(0))   # SM_CXSCREEN
            geom["height"] = int(user32.GetSystemMetrics(1))  # SM_CYSCREEN
        except Exception:
            pass
        return geom

    def _get_cursor_pos(self) -> Optional[Dict[str, int]]:
        """Real cursor position via GetCursorPos."""
        if not self._windows_available():
            return None
        try:
            import ctypes
            import ctypes.wintypes as wintypes

            user32 = ctypes.windll.user32
            pt = wintypes.POINT()
            if user32.GetCursorPos(ctypes.byref(pt)):
                return {"x": int(pt.x), "y": int(pt.y)}
        except Exception:
            pass
        return None

    def _capture_screenshot(self) -> Optional[Any]:
        """Capture a screen bitmap via mss if available (PIL Image | None)."""
        try:
            import mss  # type: ignore
            from PIL import Image  # type: ignore
            with mss.mss() as sct:
                monitors = sct.monitors
                if not monitors or len(monitors) < 2:
                    return None
                monitor = monitors[1] or monitors[0]
                if not monitor or monitor.get("width", 0) <= 0 or monitor.get("height", 0) <= 0:
                    return None
                sct_img = sct.grab(monitor)
                return Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        except Exception:
            return None

    def _extract_text(self, image: Any) -> Optional[str]:
        """OCR fallback via pytesseract — only when structured data is
        insufficient. Never mandatory."""
        if image is None:
            return None
        try:
            import pytesseract  # type: ignore
            text = pytesseract.image_to_string(image)
            return text.strip() or None
        except Exception:
            return None
# -----------------------------------------------------------------
# Adaptive computer driver — perceive -> reason -> act (Phase 6)
# -----------------------------------------------------------------

class AdaptiveComputerDriver:
    """Chooses the next semantic action based on the latest observation."""

    # A goal type -> sequence of semantic action templates. Never hardcodes
    # coordinates — the executor decides HOW to perform the semantic action.
    _GOAL_TEMPLATES = {
        "open_and_find": [
            {"action_type": "open_application", "key": "open"},
            {"action_type": "inspect_screen", "key": "observe"},
            {"action_type": "find_element", "key": "find", "target": ""},
        ],
        "open_url": [
            {"action_type": "open_url", "key": "open"},
            {"action_type": "inspect_screen", "key": "observe"},
        ],
        "compute": [
            {"action_type": "open_application", "key": "open"},
            {"action_type": "type", "key": "enter"},
            {"action_type": "press_key", "key": "submit"},
            {"action_type": "inspect_screen", "key": "observe"},
            {"action_type": "read_visible_content", "key": "read"},
        ],
    }

    def __init__(self, observer: ComputerObserver) -> None:
        self.observer = observer
        self.goal: Optional[str] = None
        self.goal_kind: str = "open_and_find"
        self.template_index = 0
        self.templates: Sequence[Dict[str, Any]] = []

    def set_goal(self, goal: str, goal_kind: Optional[str] = None) -> None:
        self.goal = goal
        self.goal_kind = goal_kind or self._infer_goal_kind(goal)
        self.templates = list(
            self._GOAL_TEMPLATES.get(self.goal_kind, self._GOAL_TEMPLATES["open_and_find"])
        )
        self.template_index = 0

    @staticmethod
    def _infer_goal_kind(goal: str) -> str:
        g = goal.lower()
        if "open" in g and ("find" in g or "search" in g or "message" in g):
            return "open_and_find"
        if g.strip().startswith("open") or "http://" in g or "https://" in g:
            return "open_url"
        if "calculate" in g or "compute" in g or "×" in g:
            return "compute"
        return "open_and_find"

    def next_action(self) -> Optional[Dict[str, Any]]:
        """Return the next semantic action dict, or None when the template is
        exhausted (the caller decides completion)."""
        if self.template_index >= len(self.templates):
            return None
        action = dict(self.templates[self.template_index])
        if action.get("key") == "find" and self.goal:
            action["target"] = self._extract_target(self.goal)
        action["goal"] = self.goal
        self.template_index += 1
        return action

    def can_proceed_given(self, anomalies: List[str]) -> bool:
        """Adaptive gate: if the observed state contradicts the plan, do not
        blindly continue — signal replanning/waits instead."""
        serious = [
            a for a in anomalies
            if a.startswith(("wrong_application", "wrong_page", "application_not_observed",
                             "page_not_observed", "window_not_open"))
        ]
        return not serious

    def replan(self) -> None:
        """Reset the plan and re-derive actions from the newly observed state."""
        self.template_index = 0

    @staticmethod
    def _extract_target(goal: str) -> str:
        m = re.search(r"(?:find|search for|look for|get)\s+(.+)", goal, flags=re.IGNORECASE)
        return m.group(1).strip() if m else goal
# -----------------------------------------------------------------
# Top-level engine — ties it together (Phase 3/6/8/9)
# -----------------------------------------------------------------

class ComputerIntelligenceEngine:
    """Runs UNDERSTAND -> OBSERVE -> REASON -> PLAN -> ACT -> OBSERVE ->
    VERIFY -> (REPLAN | RECOVER | COMPLETE).

    `observe_fn`, `execute_fn`, `verify_fn` are optional hooks provided by the
    host (they map to the skill/observation/verification layers). When absent
    the engine drives against the injected observer's world model — ideal for
    deterministic, mocked tests.
    """

    def __init__(self, observer: Optional[ComputerObserver] = None,
                 classifier: Optional[FailureClassifier] = None) -> None:
        self.observer = observer or ComputerObserver()
        self.classifier = classifier or FailureClassifier()
        self.driver = AdaptiveComputerDriver(self.observer)

    def run(self, goal: str, *,
            observe_fn: Optional[Callable[[], List[str]]] = None,
            execute_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
            verify_fn: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
            goal_kind: Optional[str] = None,
            max_steps: int = 20) -> Dict[str, Any]:
        self.driver.set_goal(goal, goal_kind)
        steps: List[Dict[str, Any]] = []
        total = 0

        while total < max_steps:
            total += 1
            action = self.driver.next_action()
            if action is None:
                break

            # OBSERVE -> REASON -> ACT
            expected = self._expected_for(action)
            anomalies = observe_fn() if observe_fn else self.observer.observe_before_act(expected)
            if not self.driver.can_proceed_given(anomalies):
                # Wrong/missing state is the signal to replan (not to plow on).
                self.driver.replan()
                continue

            # ACT
            result = execute_fn(action) if execute_fn else {"action": action["action_type"]}
            confidence = float(result.get("confidence", 0.0))

            # ACT -> OBSERVE -> VERIFY
            self.observer.observe_after_act(action["action_type"], expected, confidence)
            verified = verify_fn(action["action_type"], expected) if verify_fn else confidence >= 0.5

            step_record = {
                "action": action["action_type"],
                "target": action.get("target") or "",
                "anomalies": anomalies,
                "observed": self.observer.state.observed_state,
                "confidence": confidence,
                "verified": bool(verified),
            }
            steps.append(step_record)
            self.observer.state.task_context["last_verified"] = bool(verified)

            if not verified:
                category = self.classifier.classify(
                    action, self.observer.state,
                    evidence=[str(result.get("error") or "")],
                )
                recovery = FailureClassifier.recovery_for(category)
                steps[-1]["failure_category"] = category.value
                steps[-1]["recovery_strategy"] = recovery.value
                if recovery is RecoveryStrategy.STOP_AND_REPORT:
                    return self._result("failed", "could not be verified", goal, steps)
                if recovery in (RecoveryStrategy.WAIT_AND_REOBSERVE, RecoveryStrategy.REPLAN,
                                RecoveryStrategy.INSPECT_ALTERNATIVE):
                    self.driver.replan()
                    continue
                if recovery in (RecoveryStrategy.REQUEST_PERMISSION, RecoveryStrategy.REQUEST_AUTH):
                    steps[-1]["blocked_on_user"] = True
                    return self._result("waiting_for_user", recovery.value, goal, steps)

        return self._result("completed", None, goal, steps)

    # -- helpers ----------------------------------------------------------
    def _expected_for(self, action: Dict[str, Any]) -> Dict[str, Any]:
        expected: Dict[str, Any] = {}
        at = action.get("action_type", "")
        if at == "open_application":
            app = action.get("app") or self._infer_app(action.get("target"))
            if app:
                expected["active_app"] = app
        elif at == "open_url":
            expected["url"] = action.get("target")
        elif at in ("find_element", "click", "type", "select"):
            if action.get("target"):
                expected["element"] = action["target"]
        return expected

    @staticmethod
    def _infer_app(target: str) -> Optional[str]:
        if not target:
            return None
        known = {"youtube": "youtube", "instagram": "instagram", "chrome": "chrome",
                 "calculator": "calculator", "calc": "calculator",
                 "files": "file explorer", "downloads": "file explorer"}
        for key, val in known.items():
            if key in target.lower():
                return val
        return target

    @staticmethod
    def _result(status: str, note: Optional[str], goal: str,
                steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "status": status,
            "goal": goal,
            "note": note,
            "steps": steps,
            "steps_taken": len(steps),
            "completed": [s for s in steps if s.get("verified")],
            "failed": [s for s in steps if not s.get("verified")],
        }


# -----------------------------------------------------------------
# Small helpers
# -----------------------------------------------------------------

def _norm(value: str) -> str:
    s = re.sub(r"(https?://www\.|https?://)", "", str(value).lower())
    return re.sub(r"[^a-z0-9]+", "", s)


def _base_url_of(url: str) -> str:
    m = re.match(r"(https?://[^/]+)", str(url))
    return m.group(1) if m else url


def _element_matches(state: ComputerState, target: str) -> bool:
    t = _norm(target)
    if not t:
        return False
    for e in list(state.browser.elements) + list(state.visible_elements):
        for key in ("text", "selector", "name", "label"):
            val = str(e.get(key) or "")
            if val and (_norm(val) == t or t in _norm(val)):
                return True
    return False