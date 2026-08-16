"""
============================================================
AVORA Tool Contract & Registry
============================================================

A Tool is a single, verifiable capability AVORA can invoke.

Every tool declares:
- name / description        -> so the planner can choose it
- scope                     -> which permission domain it needs
- risk                      -> how dangerous it is
- parameters                -> JSON-schema-ish spec for validation
- handler                   -> the real implementation
- verifier (optional)       -> proves the action actually worked
- undo (optional)           -> reverses the action

ToolResult is deliberately explicit about the difference between
"ran and succeeded", "ran and failed", and "did not run".
That distinction is what stops AVORA from lying.
"""

from __future__ import annotations

import logging
import time
import traceback
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("AgentTools")


class RiskLevel(IntEnum):
    """
    Risk tiers drive confirmation behaviour.

    SAFE      - read-only inspection, no side effects
    MODERATE  - changes project files, installs packages
    HIGH      - deletes data, changes system/security settings
    BLOCKED   - never executed
    """

    SAFE = 0
    MODERATE = 1
    HIGH = 2
    BLOCKED = 3


class ToolOutcome:
    """Outcome markers for a tool invocation."""

    SUCCESS = "success"
    FAILED = "failed"
    # Did NOT run:
    DENIED = "denied"
    NEEDS_CONFIRMATION = "needs_confirmation"
    INVALID_ARGS = "invalid_args"
    UNAVAILABLE = "unavailable"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ToolResult:
    """
    Result of a tool invocation.

    `executed` is the honesty flag: False means the underlying
    action never actually happened, regardless of `outcome`.
    """

    outcome: str
    executed: bool
    summary: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    verified: Optional[bool] = None
    verification_note: str = ""
    tool: str = ""
    duration_ms: int = 0
    undo_token: Optional[Dict[str, Any]] = None

    @property
    def ok(self) -> bool:
        return self.outcome == ToolOutcome.SUCCESS

    @property
    def needs_user(self) -> bool:
        return self.outcome in (
            ToolOutcome.NEEDS_CONFIRMATION,
            ToolOutcome.DENIED,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "outcome": self.outcome,
            "executed": self.executed,
            "summary": self.summary,
            "data": self.data,
            "error": self.error,
            "verified": self.verified,
            "verification_note": self.verification_note,
            "duration_ms": self.duration_ms,
        }

    # -- Convenience constructors ---------------------------------

    @classmethod
    def success(cls, summary: str, **data: Any) -> "ToolResult":
        return cls(ToolOutcome.SUCCESS, True, summary, data=data)

    @classmethod
    def failure(cls, summary: str, error: str = "", **data: Any) -> "ToolResult":
        return cls(ToolOutcome.FAILED, True, summary, data=data, error=error or summary)

    @classmethod
    def denied(cls, summary: str) -> "ToolResult":
        return cls(ToolOutcome.DENIED, False, summary, error=summary)

    @classmethod
    def needs_confirmation(cls, summary: str, **data: Any) -> "ToolResult":
        return cls(ToolOutcome.NEEDS_CONFIRMATION, False, summary, data=data)

    @classmethod
    def invalid(cls, summary: str) -> "ToolResult":
        return cls(ToolOutcome.INVALID_ARGS, False, summary, error=summary)

    @classmethod
    def unavailable(cls, summary: str) -> "ToolResult":
        """
        The capability is architecturally present but a real external
        requirement is missing (module, credential, OS permission).
        This is how AVORA reports missing access without faking it.
        """
        return cls(ToolOutcome.UNAVAILABLE, False, summary, error=summary)


@dataclass
class ToolParam:
    """Declared parameter for a tool."""

    name: str
    type: type = str
    required: bool = False
    default: Any = None
    description: str = ""


class Tool:
    """A single invocable capability."""

    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable[..., ToolResult],
        scope: str = "system",
        risk: RiskLevel = RiskLevel.SAFE,
        params: Optional[List[ToolParam]] = None,
        verifier: Optional[Callable[..., tuple]] = None,
        undo: Optional[Callable[[Dict[str, Any]], bool]] = None,
        offline_capable: bool = True,
        examples: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.handler = handler
        self.scope = scope
        self.risk = risk
        self.params = params or []
        self.verifier = verifier
        self.undo = undo
        self.offline_capable = offline_capable
        self.examples = examples or []

    # -- Validation ------------------------------------------------

    def validate(self, args: Dict[str, Any]) -> tuple:
        """
        Validate and coerce arguments.

        Returns (ok, cleaned_args_or_error_message).
        """
        cleaned: Dict[str, Any] = {}
        declared = {p.name: p for p in self.params}

        for spec in self.params:
            if spec.name not in args or args[spec.name] is None:
                if spec.required:
                    return False, f"Missing required argument '{spec.name}' for {self.name}"
                cleaned[spec.name] = spec.default
                continue

            value = args[spec.name]
            # Coerce simple scalars; be forgiving because args often
            # originate from an LLM that emits strings for everything.
            try:
                if spec.type is bool and isinstance(value, str):
                    value = value.strip().lower() in ("1", "true", "yes", "on")
                elif spec.type in (int, float) and isinstance(value, str):
                    value = spec.type(value.strip())
                elif spec.type is str and not isinstance(value, str):
                    value = str(value)
            except (TypeError, ValueError):
                return False, f"Argument '{spec.name}' must be {spec.type.__name__}"
            cleaned[spec.name] = value

        # Pass through undeclared extras only if no params declared at all,
        # so flexible tools still work while typed tools stay strict.
        if not declared:
            cleaned.update(args)

        return True, cleaned

    def schema(self) -> Dict[str, Any]:
        """Machine-readable description used when prompting the planner."""
        return {
            "name": self.name,
            "description": self.description,
            "scope": self.scope,
            "risk": int(self.risk),
            "offline_capable": self.offline_capable,
            "params": [
                {
                    "name": p.name,
                    "type": getattr(p.type, "__name__", str(p.type)),
                    "required": p.required,
                    "description": p.description,
                }
                for p in self.params
            ],
        }

    def __repr__(self) -> str:
        return f"<Tool {self.name} scope={self.scope} risk={int(self.risk)}>"


class ToolRegistry:
    """
    Central registry of every capability AVORA can perform.

    The planner is only ever allowed to choose from here, which
    bounds what the agent can do by construction.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.debug("Tool %s re-registered", tool.name)
        self._tools[tool.name] = tool

    def add(self, **kwargs: Any) -> Tool:
        """Build and register a tool in one call."""
        tool = Tool(**kwargs)
        self.register(tool)
        return tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def all(self) -> List[Tool]:
        return list(self._tools.values())

    def names(self) -> List[str]:
        return sorted(self._tools.keys())

    def by_scope(self, scope: str) -> List[Tool]:
        return [t for t in self._tools.values() if t.scope == scope]

    def describe(self, max_risk: RiskLevel = RiskLevel.HIGH) -> List[Dict[str, Any]]:
        """Schemas for all usable tools, for planner prompting."""
        return [
            t.schema()
            for t in self._tools.values()
            if t.risk <= max_risk and t.risk != RiskLevel.BLOCKED
        ]

    # -- Execution -------------------------------------------------

    def invoke(
        self,
        name: str,
        args: Optional[Dict[str, Any]] = None,
        *,
        confirmed: bool = False,
        dry_run: bool = False,
        verify: bool = True,
    ) -> ToolResult:
        """
        Invoke a tool with validation, permission check, execution,
        and verification. Never raises: failures become ToolResults.
        """
        args = dict(args or {})
        started = time.time()

        tool = self.get(name)
        if tool is None:
            return ToolResult.invalid(f"Unknown tool '{name}'")

        def finish(result: ToolResult) -> ToolResult:
            result.tool = name
            result.duration_ms = int((time.time() - started) * 1000)
            return result

        if tool.risk == RiskLevel.BLOCKED:
            return finish(ToolResult.denied(f"'{name}' is blocked and will not be run."))

        ok, cleaned = tool.validate(args)
        if not ok:
            return finish(ToolResult.invalid(str(cleaned)))
        args = cleaned

        # Permission gate (imported lazily to avoid a circular import).
        try:
            from agent.permissions import get_permission_manager

            path_hint = (
                args.get("project_path")
                or args.get("path")
                or args.get("cwd")
                or args.get("target")
            )
            decision = get_permission_manager().check(
                scope=tool.scope,
                risk=tool.risk,
                action=name,
                details=_summarize_args(args),
                path=str(path_hint) if path_hint else None,
                confirmed=confirmed,
            )
            if not decision.allowed:
                if decision.needs_confirmation:
                    return finish(
                        ToolResult.needs_confirmation(
                            decision.reason,
                            scope=tool.scope,
                            risk=int(tool.risk),
                            tool=name,
                            args=_redact_args(args),
                        )
                    )
                return finish(ToolResult.denied(decision.reason))
        except ImportError:
            logger.debug("Permission manager unavailable; proceeding read-only only")
            if tool.risk > RiskLevel.SAFE:
                return finish(
                    ToolResult.denied("Permission system unavailable; refusing mutating action.")
                )

        if dry_run:
            return finish(
                ToolResult(
                    ToolOutcome.SUCCESS,
                    executed=False,
                    summary=f"[dry-run] would run {name}",
                    data={"args": _redact_args(args)},
                )
            )

        # Execute for real.
        try:
            result = tool.handler(**args)
            if not isinstance(result, ToolResult):
                # Tolerate handlers that return plain data.
                result = ToolResult.success(str(result) if result else "Done", raw=result)
        except TimeoutError as exc:
            return finish(ToolResult(ToolOutcome.TIMEOUT, True, "Tool timed out", error=str(exc)))
        except PermissionError as exc:
            return finish(ToolResult.denied(f"OS denied permission: {exc}"))
        except FileNotFoundError as exc:
            return finish(ToolResult.failure("Target not found", error=str(exc)))
        except Exception as exc:
            logger.warning("Tool %s raised: %s", name, exc)
            logger.debug("%s", traceback.format_exc())
            return finish(ToolResult.failure(f"{name} failed: {exc}", error=str(exc)))

        # Verification: only claim verified when we truly checked.
        if verify and result.ok and tool.verifier is not None:
            try:
                verified, note = tool.verifier(**args)
                result.verified = bool(verified)
                result.verification_note = str(note or "")
                if not verified:
                    result.outcome = ToolOutcome.FAILED
                    result.error = f"Verification failed: {note}"
            except Exception as exc:
                result.verified = False
                result.verification_note = f"Verification error: {exc}"

        return finish(result)


def _summarize_args(args: Dict[str, Any], limit: int = 160) -> str:
    try:
        text = ", ".join(f"{k}={v!r}" for k, v in _redact_args(args).items())
    except Exception:
        text = "<unprintable args>"
    return text[:limit]


_SECRET_HINTS = ("key", "token", "secret", "password", "passwd", "credential", "auth")


def _redact_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """Redact secret-looking values before logging or displaying args."""
    safe: Dict[str, Any] = {}
    for key, value in args.items():
        if any(hint in key.lower() for hint in _SECRET_HINTS):
            safe[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 300:
            safe[key] = value[:300] + "...[truncated]"
        else:
            safe[key] = value
    return safe


_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """
    Get the shared tool registry, populating it on first use.

    Tool modules self-register via register_all() so that importing
    this module alone stays cheap and side-effect free.
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        try:
            from agent import builtin_tools

            builtin_tools.register_all(_registry)
            logger.info("Registered %d agent tools", len(_registry.all()))
        except Exception as exc:
            logger.warning("Builtin tool registration failed: %s", exc)
            logger.debug("%s", traceback.format_exc())
    return _registry


__all__ = [
    "Tool",
    "ToolParam",
    "ToolResult",
    "ToolOutcome",
    "ToolRegistry",
    "RiskLevel",
    "get_registry",
]
