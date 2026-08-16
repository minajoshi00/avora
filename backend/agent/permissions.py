"""
============================================================
AVORA Permission Manager
============================================================

Goal: powerful autonomy without permission fatigue.

Model
-----
- Permissions are granted per (scope, path-scope) pair.
- A grant can be remembered, so AVORA asks once per project
  instead of once per action.
- Risk still wins: HIGH-risk actions always require explicit
  confirmation for that specific action, even inside a granted
  scope. Remembering "modify files in this project" must never
  silently authorise "delete this folder".
- BLOCKED patterns are never executed under any grant.

Storage lives beside AVORA's other state in APP_DATA_DIR so it
survives restarts and can be revoked from Settings.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("AgentPermissions")

try:
    from agent.tools import RiskLevel
except ImportError:  # pragma: no cover
    from enum import IntEnum

    class RiskLevel(IntEnum):  # type: ignore
        SAFE = 0
        MODERATE = 1
        HIGH = 2
        BLOCKED = 3


class Scope:
    """Permission scopes. Users can revoke any of these individually."""

    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    TERMINAL = "terminal"
    BROWSER = "browser"
    NETWORK = "network"
    GIT = "git"
    PACKAGES = "packages"
    SYSTEM_SETTINGS = "system_settings"
    APPS = "apps"
    DEPLOYMENT = "deployment"
    EMAIL = "email"
    AUTOMATION = "automation"
    SYSTEM = "system"

    ALL = (
        FILESYSTEM_READ,
        FILESYSTEM_WRITE,
        TERMINAL,
        BROWSER,
        NETWORK,
        GIT,
        PACKAGES,
        SYSTEM_SETTINGS,
        APPS,
        DEPLOYMENT,
        EMAIL,
        AUTOMATION,
        SYSTEM,
    )

    #: Scopes that are read-only and therefore safe to auto-allow.
    READ_ONLY = (FILESYSTEM_READ, SYSTEM, NETWORK)

    LABELS = {
        FILESYSTEM_READ: "read files",
        FILESYSTEM_WRITE: "create, modify or delete files",
        TERMINAL: "run terminal commands",
        BROWSER: "open and control the browser",
        NETWORK: "make network requests",
        GIT: "run Git operations",
        PACKAGES: "install project dependencies",
        SYSTEM_SETTINGS: "change Windows settings",
        APPS: "launch and close applications",
        DEPLOYMENT: "run deployments",
        EMAIL: "access email",
        AUTOMATION: "run saved automations",
        SYSTEM: "read system information",
    }


@dataclass
class PermissionDecision:
    """Outcome of a permission check."""

    allowed: bool
    reason: str = ""
    needs_confirmation: bool = False
    scope: str = ""
    risk: int = 0

    def __bool__(self) -> bool:
        return self.allowed


@dataclass
class Grant:
    """A remembered permission grant."""

    scope: str
    path_scope: str = "*"
    granted_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None

    def matches(self, scope: str, path: Optional[str]) -> bool:
        if self.scope != scope:
            return False
        if self.expires_at and time.time() > self.expires_at:
            return False
        if self.path_scope in ("*", ""):
            return True
        if not path:
            return False
        try:
            target = Path(path).resolve()
            root = Path(self.path_scope).resolve()
            return target == root or root in target.parents
        except (OSError, ValueError):
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scope": self.scope,
            "path_scope": self.path_scope,
            "granted_at": self.granted_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Grant":
        return cls(
            scope=data.get("scope", ""),
            path_scope=data.get("path_scope", "*"),
            granted_at=data.get("granted_at", time.time()),
            expires_at=data.get("expires_at"),
        )


# ============================================================
# HARD BLOCKS - never executed regardless of permissions
# ============================================================

BLOCKED_PATTERNS: List[tuple] = [
    (r"\bformat\s+[a-z]:", "disk format"),
    (r"\bmkfs\b", "filesystem creation"),
    (r"\bfdisk\b", "disk partitioning"),
    (r"dd\s+if=", "raw disk write"),
    (r"rm\s+-rf\s+/(?:\s|$)", "recursive root delete"),
    (r"rm\s+-rf\s+~", "recursive home delete"),
    (r"del\s+/[fsq]\s+.*[a-z]:\\\\?(?:\s|$)", "recursive drive delete"),
    (r"\brd\s+/s\s+/q\s+[a-z]:\\\\?(?:\s|$)", "recursive drive delete"),
    (r":\(\)\s*\{.*\};:", "fork bomb"),
    (r"\bvssadmin\s+delete\s+shadows", "shadow copy deletion"),
    (r"\bbcdedit\b.*\b(safeboot|bootstatuspolicy)\b", "boot configuration tampering"),
    (r"\bcipher\s+/w", "free space wipe"),
    (r"\bschtasks\b.*\b/create\b.*\b(system|highest)\b", "privileged persistence"),
    (r"reg\s+(add|delete).*\\\\(Run|RunOnce)\b", "startup persistence via registry"),
    (r"\bnetsh\s+advfirewall\s+set\s+.*\boff\b", "disabling the firewall"),
    (r"Set-MpPreference.*DisableRealtimeMonitoring\s*\$?true", "disabling antivirus"),
    (r"\bmimikatz\b", "credential theft tooling"),
    (r"\b(?:sekurlsa|lsadump)\b", "credential dumping"),
    # Credential exfiltration patterns
    (r"(?i)copy.*\\\\(Login Data|Cookies|Web Data)\b", "browser credential theft"),
    (r"(?i)(curl|wget|Invoke-WebRequest).*(\.ssh|\.env|id_rsa|credentials)", "credential exfiltration"),
    (r"(?i)(Invoke-Expression|iex)\s*\(.*(DownloadString|WebClient)", "remote code execution"),
    (r"(?i)(curl|wget).*\|\s*(bash|sh|powershell)", "pipe-to-shell execution"),
]

#: Commands that mutate state and therefore need a real grant.
_MUTATING_COMMAND_HINTS = (
    "install", "uninstall", "remove", "delete", "del ", "rm ", "rmdir",
    "move", "mv ", "copy", "cp ", "write", "set-", "new-item", "mkdir",
    "push", "commit", "reset", "checkout", "merge", "rebase", "clean",
    "kill", "taskkill", "stop-", "start-", "restart", "shutdown",
    "chmod", "chown", "icacls", "attrib", "reg ", "netsh", "sc ",
)


def check_blocked(command: str) -> Optional[str]:
    """
    Return the reason a command is hard-blocked, or None if not blocked.

    This is intentionally independent of the permission store so no
    grant, setting, or prompt-injected instruction can bypass it.
    """
    if not command:
        return None
    text = str(command)
    for pattern, reason in BLOCKED_PATTERNS:
        try:
            if re.search(pattern, text, re.IGNORECASE):
                return reason
        except re.error:
            continue
    return None


class PermissionManager:
    """Scoped, persistent permission store with risk-aware gating."""

    _instance: Optional["PermissionManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_ready", False):
            return
        self._ready = True
        self._grants: List[Grant] = []
        self._denied: List[Grant] = []
        self._state_lock = threading.RLock()
        self._confirm_callback: Optional[Callable[[str, str, int], bool]] = None
        self._audit: List[Dict[str, Any]] = []
        self._store = self._resolve_store()
        self._load()

    # -- Storage ---------------------------------------------------

    def _resolve_store(self) -> Path:
        try:
            from app_paths import APP_DATA_DIR

            base = Path(APP_DATA_DIR)
        except Exception:
            base = Path(
                os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            ) / "AVORA"
        base.mkdir(parents=True, exist_ok=True)
        return base / "agent_permissions.json"

    def _load(self) -> None:
        try:
            if not self._store.exists():
                return
            data = json.loads(self._store.read_text(encoding="utf-8"))
            with self._state_lock:
                self._grants = [Grant.from_dict(g) for g in data.get("grants", [])]
                self._denied = [Grant.from_dict(g) for g in data.get("denied", [])]
        except Exception as exc:
            logger.warning("Could not load permissions: %s", exc)

    def _save(self) -> None:
        try:
            with self._state_lock:
                payload = {
                    "grants": [g.to_dict() for g in self._grants],
                    "denied": [g.to_dict() for g in self._denied],
                }
            tmp = self._store.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp.replace(self._store)
        except Exception as exc:
            logger.warning("Could not save permissions: %s", exc)

    # -- Confirmation hook ----------------------------------------

    def set_confirm_callback(self, callback: Optional[Callable[[str, str, int], bool]]) -> None:
        """
        Install a UI callback used to ask the user in real time.

        Signature: callback(action, details, risk) -> bool
        When absent, HIGH-risk actions are refused rather than assumed.
        """
        self._confirm_callback = callback

    # -- Core check ------------------------------------------------

    def check(
        self,
        scope: str,
        risk: RiskLevel,
        action: str = "",
        details: str = "",
        path: Optional[str] = None,
        confirmed: bool = False,
    ) -> PermissionDecision:
        """Decide whether an action may proceed."""
        risk_int = int(risk)

        # 1. Hard blocks always win.
        blocked_reason = check_blocked(details) or check_blocked(action)
        if blocked_reason:
            self._log(action, scope, risk_int, "blocked", blocked_reason)
            return PermissionDecision(
                False,
                f"Blocked: this looks like {blocked_reason}. I won't do that.",
                scope=scope,
                risk=risk_int,
            )

        if risk >= RiskLevel.BLOCKED:
            return PermissionDecision(False, "This action is blocked.", scope=scope, risk=risk_int)

        # 2. Panic / kill switch from the existing safety module.
        try:
            from avora_safety import is_panic

            if is_panic():
                return PermissionDecision(
                    False,
                    "AVORA is in panic mode. All actions are suspended.",
                    scope=scope,
                    risk=risk_int,
                )
        except Exception:
            pass

        # 3. Explicit user confirmation for this call satisfies any risk.
        if confirmed:
            self._log(action, scope, risk_int, "allowed", "user confirmed")
            return PermissionDecision(True, "Confirmed by user.", scope=scope, risk=risk_int)

        # 4. Read-only work needs no prompting.
        if risk == RiskLevel.SAFE and scope in Scope.READ_ONLY:
            return PermissionDecision(True, "Read-only action.", scope=scope, risk=risk_int)

        # 5. Explicit denials.
        with self._state_lock:
            for grant in self._denied:
                if grant.matches(scope, path):
                    return PermissionDecision(
                        False,
                        f"You previously denied permission to {Scope.LABELS.get(scope, scope)}. "
                        "You can re-enable it in Settings.",
                        scope=scope,
                        risk=risk_int,
                    )

        # 6. HIGH risk always needs per-action confirmation, even when
        #    the scope was granted. This is the key safety property.
        if risk >= RiskLevel.HIGH:
            if self._confirm_callback:
                try:
                    if self._confirm_callback(action, details, risk_int):
                        self._log(action, scope, risk_int, "allowed", "confirmed via UI")
                        return PermissionDecision(True, "Confirmed.", scope=scope, risk=risk_int)
                    return PermissionDecision(
                        False, "You declined this action.", scope=scope, risk=risk_int
                    )
                except Exception as exc:
                    logger.warning("Confirm callback failed: %s", exc)
            return PermissionDecision(
                False,
                f"This is a high-risk action ({Scope.LABELS.get(scope, scope)}) and needs your "
                "explicit confirmation first.",
                needs_confirmation=True,
                scope=scope,
                risk=risk_int,
            )

        # 7. MODERATE risk: a remembered scope grant is enough.
        if self.has_grant(scope, path):
            return PermissionDecision(True, "Previously granted.", scope=scope, risk=risk_int)

        if self._confirm_callback:
            try:
                if self._confirm_callback(action, details, risk_int):
                    self.grant(scope, path=path, remember=True)
                    return PermissionDecision(True, "Granted.", scope=scope, risk=risk_int)
                return PermissionDecision(
                    False, "You declined this action.", scope=scope, risk=risk_int
                )
            except Exception as exc:
                logger.warning("Confirm callback failed: %s", exc)

        return PermissionDecision(
            False,
            f"I need your permission to {Scope.LABELS.get(scope, scope)}"
            + (f" in {path}" if path else "")
            + ".",
            needs_confirmation=True,
            scope=scope,
            risk=risk_int,
        )

    # -- Grant management -----------------------------------------

    def has_grant(self, scope: str, path: Optional[str] = None) -> bool:
        with self._state_lock:
            return any(g.matches(scope, path) for g in self._grants)

    def grant(
        self,
        scope: str,
        path: Optional[str] = None,
        remember: bool = True,
        duration_hours: Optional[float] = None,
    ) -> None:
        """Grant a scope, optionally limited to a path and/or duration."""
        path_scope = "*"
        if path:
            try:
                candidate = Path(path)
                path_scope = str(
                    (candidate if candidate.is_dir() else candidate.parent).resolve()
                )
            except (OSError, ValueError):
                path_scope = "*"

        expires = time.time() + duration_hours * 3600 if duration_hours else None
        grant = Grant(scope=scope, path_scope=path_scope, expires_at=expires)

        with self._state_lock:
            self._denied = [d for d in self._denied if not (d.scope == scope and d.path_scope == path_scope)]
            if not any(g.scope == scope and g.path_scope == path_scope for g in self._grants):
                self._grants.append(grant)
        if remember:
            self._save()
        self._log(f"grant:{scope}", scope, 0, "granted", path_scope)

    def deny(self, scope: str, path: Optional[str] = None, remember: bool = True) -> None:
        path_scope = str(Path(path).resolve()) if path else "*"
        with self._state_lock:
            self._grants = [
                g for g in self._grants if not (g.scope == scope and g.path_scope == path_scope)
            ]
            self._denied.append(Grant(scope=scope, path_scope=path_scope))
        if remember:
            self._save()

    def revoke(self, scope: str, path: Optional[str] = None) -> int:
        """Revoke matching grants. Returns how many were removed."""
        with self._state_lock:
            before = len(self._grants)
            if path:
                target = str(Path(path).resolve())
                self._grants = [
                    g for g in self._grants if not (g.scope == scope and g.path_scope == target)
                ]
            else:
                self._grants = [g for g in self._grants if g.scope != scope]
            removed = before - len(self._grants)
        self._save()
        return removed

    def revoke_all(self) -> None:
        with self._state_lock:
            self._grants = []
            self._denied = []
        self._save()

    def summary(self) -> Dict[str, Any]:
        """Data for the Settings permission manager UI."""
        with self._state_lock:
            return {
                "grants": [
                    {
                        "scope": g.scope,
                        "label": Scope.LABELS.get(g.scope, g.scope),
                        "path_scope": g.path_scope,
                        "expires_at": g.expires_at,
                    }
                    for g in self._grants
                ],
                "denied": [
                    {"scope": d.scope, "path_scope": d.path_scope} for d in self._denied
                ],
                "available_scopes": [
                    {"scope": s, "label": Scope.LABELS.get(s, s)} for s in Scope.ALL
                ],
            }

    # -- Audit -----------------------------------------------------

    def _log(self, action: str, scope: str, risk: int, outcome: str, note: str = "") -> None:
        entry = {
            "ts": time.time(),
            "action": action,
            "scope": scope,
            "risk": risk,
            "outcome": outcome,
            "note": note[:200],
        }
        with self._state_lock:
            self._audit.append(entry)
            if len(self._audit) > 500:
                self._audit = self._audit[-500:]

        # Mirror into AVORA's existing activity log when available.
        try:
            from avora_safety import log_activity

            log_activity(
                f"PERMISSION_{outcome.upper()}",
                f"{scope}:{action} {note}",
                level="info" if outcome == "allowed" else "warning",
            )
        except Exception:
            pass

    def audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._state_lock:
            return list(self._audit[-limit:])


_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    global _manager
    if _manager is None:
        _manager = PermissionManager()
    return _manager


__all__ = [
    "PermissionManager",
    "PermissionDecision",
    "Scope",
    "Grant",
    "get_permission_manager",
    "check_blocked",
    "BLOCKED_PATTERNS",
]
