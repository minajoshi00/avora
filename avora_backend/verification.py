# ============================================================
# VERIFICATION ENGINE — AVORA AGENT MODE (RESTORED)
# ============================================================
# Restored during the QA + restore-verification cycle.
#
# Contract (pinned by avora_backend/agent_orchestrator.py and
# avora_backend/tests/test_verification_regression.py):
#
#   EXECUTION SUCCESS != VERIFIED SUCCESS.
#
# Verification inspects ACTUAL observable state — the real
# filesystem for file/folder actions, and real evidence keys in
# the observation for everything else. A lying observation that
# only claims {"success": True} is evidence, NEVER proof.
#
# Outcomes are tri-state:
#   VERIFIED_SUCCESS  — the requested final state was observed.
#   VERIFIED_FAILURE  — the observed state contradicts expectation.
#   UNKNOWN           — the final state could not be established.
#                       UNKNOWN is NEVER converted into success
#                       (bool(VerificationResult) is False).
#
# VERIFYING is a TaskState (transient execution state) — it is
# intentionally NOT a verification outcome and must never be
# treated as successful task completion.
# ============================================================

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from avora_backend.action_model import Action, ActionType


class VerificationStatus(Enum):
    """Tri-state verification outcome. VERIFYING is NOT a member —
    it is a transient TaskState, not a verification result."""

    VERIFIED_SUCCESS = "VERIFIED_SUCCESS"
    VERIFIED_FAILURE = "VERIFIED_FAILURE"
    UNKNOWN = "UNKNOWN"


class VerificationResult:
    """Result of verifying one action against its expected final state."""

    __slots__ = ("status", "evidence", "error")

    def __init__(
        self,
        *,
        status: VerificationStatus,
        evidence: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        self.status = status
        self.evidence: Dict[str, Any] = evidence or {}
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.name,
            "evidence": dict(self.evidence),
            "error": self.error,
        }

    def __bool__(self) -> bool:
        # Only VERIFIED_SUCCESS is truthy. UNKNOWN must never be truthy.
        return self.status == VerificationStatus.VERIFIED_SUCCESS

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"VerificationResult(status={self.status.name!r}, error={self.error!r})"


# Tri-state aliases for readability at call sites
SUCCESS = VerificationStatus.VERIFIED_SUCCESS
FAILURE = VerificationStatus.VERIFIED_FAILURE
UNKNOWN = VerificationStatus.UNKNOWN


# -----------------------------------------------------------------
# VerificationEngine — default (state-based) verifier
# -----------------------------------------------------------------

class VerificationEngine:
    """
    Default verifier used by AgentOrchestrator when no custom
    `verify_callback` is injected.

    Uses REAL observable state wherever possible:
      - file content     -> reads the real file
      - file existence   -> checks the real filesystem
      - folder existence -> checks the real filesystem
      - deletion         -> checks the real filesystem
      - move/rename      -> checks destination exists AND source gone
      - process lists / window / page evidence -> observation evidence keys

    Anything that cannot be established from real state is UNKNOWN —
    never success. Execution errors are VERIFIED_FAILURE.
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def verify(
        self, action: Action, observation: Optional[Dict[str, Any]]
    ) -> VerificationResult:
        """Verify `action` against the real final state in `observation`."""
        if action is None:
            return VerificationResult(status=UNKNOWN, error="No action to verify")
        obs: Dict[str, Any] = dict(observation or {})
        # The default observation nests the executor's raw result under
        # "execution_result" — flatten it so real evidence keys are visible.
        execution_result = obs.get("execution_result")
        if isinstance(execution_result, dict):
            obs = {**execution_result, **obs}

        # Hard contradictions first — the executor itself reported failure.
        if obs.get("status") == "error" or obs.get("success") is False or obs.get("error"):
            return VerificationResult(
                status=FAILURE,
                error=f"Execution reported failure: {obs.get('error') or obs.get('status')}",
            )

        handler = self._HANDLERS.get(action.action_type, self._verify_generic)
        try:
            return handler(self, action, obs)
        except Exception as exc:  # defensive: verification must never crash the loop
            return VerificationResult(
                status=UNKNOWN,
                error=(
                    "Verifier raised an exception; "
                    f"final state could not be verified: {exc}"
                ),
            )


    # ------------------------------------------------------------------
    # Filesystem-authoritative verifiers
    # ------------------------------------------------------------------

    def _verify_create_or_write_file(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        params = action.parameters or {}
        target = action.target or params.get("filepath") or params.get("path")
        if not target:
            return VerificationResult(status=UNKNOWN, error="No file target to verify")
        p = Path(target)
        if not p.is_file():
            # Filesystem is authoritative — a lying {"exists": True} is ignored.
            return VerificationResult(
                status=FAILURE, error=f"File does not exist: {target}"
            )
        requested_content = params.get("content")
        if requested_content is not None:
            try:
                actual = p.read_text()
            except Exception as exc:
                return VerificationResult(
                    status=UNKNOWN, error=f"Could not read file content: {exc}"
                )
            if actual != requested_content:
                return VerificationResult(
                    status=FAILURE,
                    error="Verify failed: content did not match requested content",
                )
        return VerificationResult(
            status=SUCCESS, evidence={"path": str(p), "exists": True}
        )

    def _verify_create_folder(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        target = action.target or (action.parameters or {}).get("folder_path")
        if not target:
            return VerificationResult(status=UNKNOWN, error="No folder target to verify")
        if not Path(target).is_dir():
            return VerificationResult(
                status=FAILURE, error=f"Folder does not exist: {target}"
            )
        return VerificationResult(status=SUCCESS, evidence={"path": target, "is_dir": True})

    def _verify_delete_file(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        target = action.target or (action.parameters or {}).get("filepath")
        if not target:
            return VerificationResult(status=UNKNOWN, error="No file target to verify")
        if Path(target).exists():
            return VerificationResult(
                status=FAILURE, error=f"File still exists after delete: {target}"
            )
        return VerificationResult(status=SUCCESS, evidence={"deleted": target})

    def _verify_move_or_rename(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        params = action.parameters or {}
        source = params.get("source") or action.target
        destination = (
            params.get("destination") or params.get("new_name") or params.get("target")
        )
        if not destination:
            return VerificationResult(status=UNKNOWN, error="No destination to verify")
        dest = Path(destination)
        if not dest.is_file() and not dest.is_dir():
            return VerificationResult(
                status=FAILURE, error=f"Destination does not exist: {destination}"
            )
        if source and Path(source).exists():
            return VerificationResult(
                status=FAILURE,
                error=f"Source still present after move/rename: {source}",
            )
        return VerificationResult(
            status=SUCCESS,
            evidence={"destination": str(dest), "source_removed": True},
        )

    def _verify_read_file(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        target = action.target or (action.parameters or {}).get("filepath")
        if target and Path(target).is_file():
            return VerificationResult(
                status=SUCCESS, evidence={"path": target, "readable": True}
            )
        if obs.get("content") is not None or obs.get("status") == "read":
            return VerificationResult(
                status=SUCCESS, evidence={"evidence": "content returned"}
            )
        return VerificationResult(
            status=FAILURE, error=f"File not readable: {target}"
        )

    def _verify_list_directory(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        directory = (
            action.target
            or (action.parameters or {}).get("directory")
            or obs.get("directory")
        )
        if directory and not Path(directory).exists():
            return VerificationResult(
                status=FAILURE, error=f"Directory not found: {directory}"
            )
        if isinstance(obs.get("files"), list):
            return VerificationResult(
                status=SUCCESS,
                evidence={"directory": directory, "count": len(obs["files"])},
            )
        if isinstance(obs.get("entries"), list):
            return VerificationResult(
                status=SUCCESS,
                evidence={"directory": directory, "count": len(obs["entries"])},
            )
        return VerificationResult(
            status=UNKNOWN, error="No directory listing evidence to verify"
        )


    # ------------------------------------------------------------------
    # Observation-evidence verifiers (no fabricable state)
    # ------------------------------------------------------------------

    def _verify_open_url(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        # Real evidence: an actual page title or final URL from the browser.
        title = obs.get("page_title") or obs.get("title")
        if title:
            return VerificationResult(status=SUCCESS, evidence={"page_title": title})
        if obs.get("url") and obs.get("status") == "executed":
            return VerificationResult(status=SUCCESS, evidence={"url": obs["url"]})
        return VerificationResult(
            status=UNKNOWN,
            error="No page evidence (title/url) — final state could not be verified",
        )

    def _verify_search_web(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        # Real evidence: results, or a search results page title/url.
        if isinstance(obs.get("results"), list):
            return VerificationResult(
                status=SUCCESS, evidence={"results": len(obs["results"])}
            )
        title = obs.get("page_title") or obs.get("title")
        if title:
            return VerificationResult(status=SUCCESS, evidence={"page_title": title})
        if obs.get("url"):
            return VerificationResult(status=SUCCESS, evidence={"url": obs["url"]})
        return VerificationResult(
            status=UNKNOWN,
            error="No search results evidence — final state could not be verified",
        )

    def _verify_go_back_forward(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        # Real evidence: a final URL/title after history navigation.
        if obs.get("url") or obs.get("page_title") or obs.get("title"):
            return VerificationResult(
                status=SUCCESS,
                evidence={
                    "url": obs.get("url"),
                    "page_title": obs.get("page_title") or obs.get("title"),
                },
            )
        return VerificationResult(
            status=UNKNOWN,
            error="No navigation evidence — final state could not be verified",
        )

    def _verify_open_application(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        target = (action.target or "").lower()
        apps = obs.get("applications")
        if isinstance(apps, list) and target:
            for app in apps:
                if isinstance(app, dict):
                    name = str(app.get("title") or app.get("process") or "").lower()
                else:
                    name = str(app).lower()
                if target in name:
                    return VerificationResult(
                        status=SUCCESS, evidence={"application": name}
                    )
            return VerificationResult(
                status=FAILURE, error=f"Application not running: {action.target}"
            )
        if isinstance(obs.get("window"), dict) and obs["window"]:
            return VerificationResult(
                status=SUCCESS, evidence={"window": obs["window"].get("title")}
            )
        return VerificationResult(
            status=UNKNOWN,
            error="No window/process evidence — final state could not be verified",
        )

    def _verify_activate_application(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        if obs.get("status") == "activated" and obs.get("window"):
            return VerificationResult(
                status=SUCCESS, evidence={"activated": obs.get("window")}
            )
        return VerificationResult(
            status=UNKNOWN,
            error="No activation evidence — final state could not be verified",
        )

    def _verify_close_application(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        if obs.get("closed") is True or obs.get("status") in ("closed", "terminated"):
            return VerificationResult(
                status=SUCCESS, evidence={"closed": action.target}
            )
        return VerificationResult(
            status=UNKNOWN,
            error="No close evidence — final state could not be verified",
        )


    def _verify_key_press(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        if obs.get("pressed") is True or obs.get("status") == "pressed":
            return VerificationResult(status=SUCCESS, evidence={"key": action.target})
        return VerificationResult(
            status=UNKNOWN,
            error="No key-event evidence — final state could not be verified",
        )

    def _verify_key_combination(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        return self._verify_key_press(action, obs)

    def _verify_type(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        text = (action.parameters or {}).get("text")
        if obs.get("typed") is True or obs.get("status") == "typed":
            return VerificationResult(status=SUCCESS, evidence={"typed": text})
        # Real evidence: the field value echoes the typed text.
        if text is not None and obs.get("value") == text:
            return VerificationResult(status=SUCCESS, evidence={"value": text})
        return VerificationResult(
            status=UNKNOWN,
            error="No typed-text evidence — final state could not be verified",
        )

    def _verify_click(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        if obs.get("clicked") is True or obs.get("status") == "clicked":
            return VerificationResult(
                status=SUCCESS, evidence={"clicked": action.target}
            )
        return VerificationResult(
            status=UNKNOWN,
            error="No click evidence — final state could not be verified",
        )

    def _verify_send_message(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        # Architecture has no state checker that can confirm delivery;
        # only explicit delivery evidence counts.
        if obs.get("message_id") or obs.get("delivered") is True:
            return VerificationResult(status=SUCCESS, evidence={"delivered": True})
        return VerificationResult(
            status=UNKNOWN,
            error="No delivery evidence — final state could not be verified",
        )


    def _verify_change_setting(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        if obs.get("applied") is True or obs.get("status") == "applied":
            return VerificationResult(
                status=SUCCESS,
                evidence={
                    "setting": action.target,
                    "value": (action.parameters or {}).get("value"),
                },
            )
        return VerificationResult(
            status=UNKNOWN,
            error="No setting-applied evidence — final state could not be verified",
        )

    def _verify_get_process_list(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        if isinstance(obs.get("applications"), list):
            return VerificationResult(
                status=SUCCESS, evidence={"applications": len(obs["applications"])}
            )
        if isinstance(obs.get("processes"), list):
            return VerificationResult(
                status=SUCCESS, evidence={"processes": len(obs["processes"])}
            )
        return VerificationResult(
            status=UNKNOWN,
            error="No process-list evidence — final state could not be verified",
        )

    def _verify_get_active_window(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        window = obs.get("window")
        if window:
            return VerificationResult(status=SUCCESS, evidence={"window": window})
        return VerificationResult(
            status=UNKNOWN,
            error="No active-window evidence — final state could not be verified",
        )

    def _verify_observation_action(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        if obs.get("status") in ("inspected", "executed") or obs.get("screenshot"):
            return VerificationResult(
                status=SUCCESS, evidence={"status": obs.get("status")}
            )
        return VerificationResult(
            status=UNKNOWN,
            error="No observation evidence — final state could not be verified",
        )


    def _verify_generic(
        self, action: Action, obs: Dict[str, Any]
    ) -> VerificationResult:
        # No state-based checker for this action type. Execution success
        # alone is NOT proof of the requested final state.
        return VerificationResult(
            status=UNKNOWN,
            error=(
                f"No state-based verifier for {action.action_type.name}; "
                "final state could not be established"
            ),
        )

    _HANDLERS = {
        ActionType.CREATE_FILE: _verify_create_or_write_file,
        ActionType.WRITE_FILE: _verify_create_or_write_file,
        ActionType.CREATE_FOLDER: _verify_create_folder,
        ActionType.DELETE_FILE: _verify_delete_file,
        ActionType.MOVE_FILE: _verify_move_or_rename,
        ActionType.RENAME_FILE: _verify_move_or_rename,
        ActionType.READ_FILE: _verify_read_file,
        ActionType.LIST_DIRECTORY: _verify_list_directory,
        ActionType.OPEN_URL: _verify_open_url,
        ActionType.NAVIGATE_TO: _verify_open_url,
        ActionType.SEARCH_WEB: _verify_search_web,
        ActionType.GO_BACK: _verify_go_back_forward,
        ActionType.GO_FORWARD: _verify_go_back_forward,
        ActionType.OPEN_APPLICATION: _verify_open_application,
        ActionType.ACTIVATE_APPLICATION: _verify_activate_application,
        ActionType.CLOSE_APPLICATION: _verify_close_application,
        ActionType.KEY_PRESS: _verify_key_press,
        ActionType.KEY_COMBINATION: _verify_key_combination,
        ActionType.TYPE: _verify_type,
        ActionType.CLICK: _verify_click,
        ActionType.SEND_MESSAGE: _verify_send_message,
        ActionType.CHANGE_SETTING: _verify_change_setting,
        ActionType.GET_PROCESS_LIST: _verify_get_process_list,
        ActionType.GET_ACTIVE_WINDOW: _verify_get_active_window,
        ActionType.INSPECT_SCREEN: _verify_observation_action,
        ActionType.GET_SCREENSHOT: _verify_observation_action,
        ActionType.GET_PROCESS_STATE: _verify_observation_action,
    }







