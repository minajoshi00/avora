"""
V2 AgentOrchestrator - Real Actions with Safety.

Coordinates goals across the existing tool registry and skill system.

V2 additions over the V1 cancelable orchestrator:
  * Task progress reporting (progress_callback)
  * Permission gate: risky tools require explicit user confirmation
    (permission_callback or confirmed=True) - never silent destructive
    actions
  * Error recovery: transient tool failures are retried once
  * Activity log: every tool invocation is recorded and queryable
"""

import logging
import time
from collections.abc import Callable
from typing import Any

from skills import get_enabled_skills

from agent.tools import RiskLevel, get_registry

logger = logging.getLogger("AgentOrchestrator")

# Tools at or above this risk level require explicit user confirmation.
_CONFIRM_RISK_THRESHOLD = RiskLevel.MODERATE


class AgentOrchestrator:
    """Coordinate a goal across the existing tool registry and skill system."""

    # Tools considered when routing generic natural-language requests.
    # Subclasses/tests may override this list.
    ROUTED_TOOLS = (
        "inspect_project",
        "diagnose_vercel",
        "browser_open_url",
        "run_vercel_deploy",
    )

    def __init__(self, registry=None):
        self.registry = registry or get_registry()
        self.skills = get_enabled_skills()
        self._cancelled = False

        # V2: task progress + activity visibility
        self.progress_callback: Callable[[str, float], None] | None = None
        self.permission_callback: Callable[[str, str], bool] | None = None
        self._activity_log: list[dict[str, Any]] = []
        self._max_activity = 100

    # =========================================================
    # CANCELLATION (V1)
    # =========================================================

    def cancel(self):
        """Request cancellation of the current operation."""
        self._cancelled = True
        logger.info("Cancellation requested")

    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled

    def reset(self):
        """Reset cancellation state for a new operation."""
        self._cancelled = False

    # =========================================================
    # V2: PROGRESS / PERMISSION / ACTIVITY
    # =========================================================

    def _report_progress(self, step: str, fraction: float = 0.0):
        """Report task progress to the UI callback (if registered)."""
        logger.info("PROGRESS %s (%d%%)", step, int(fraction * 100))
        cb = self.progress_callback
        if callable(cb):
            try:
                cb(step, max(0.0, min(1.0, fraction)))
            except Exception as e:
                logger.debug(f"Progress callback error: {e}")

    def _log_activity(self, entry: dict[str, Any]):
        """Record a tool activity entry (visible to the user)."""
        entry["time"] = time.time()
        self._activity_log.append(entry)
        if len(self._activity_log) > self._max_activity:
            self._activity_log.pop(0)

    def get_activity_log(self) -> list[dict[str, Any]]:
        """Get the recent tool activity log."""
        return list(self._activity_log)

    def _request_permission(self, tool_name: str, reason: str) -> bool:
        """
        Ask the user for permission before a risky action.

        Returns True only when the user explicitly approves.
        Never silently performs destructive actions.
        """
        cb = self.permission_callback
        if callable(cb):
            try:
                return bool(cb(tool_name, reason))
            except Exception as e:
                logger.warning(f"Permission callback error: {e}")
                return False

        # No callback registered - deny by default (safe default).
        logger.warning(
            "Permission required for %s but no permission_callback "
            "registered; denying by default.",
            tool_name,
        )
        return False

    def _invoke_with_recovery(self, name: str, args: dict[str, Any]) -> Any:
        """
        Invoke a tool with one retry on transient failure.

        Denials, cancellations, and invalid-argument results are not
        retried - only genuine execution failures get one retry.
        """
        result = self.registry.invoke(name, args)

        if (
            not result.ok
            and result.outcome.name == "FAILURE"
            and not self.is_cancelled()
        ):
            logger.info("Retrying tool %s once after failure", name)
            time.sleep(0.3)
            result = self.registry.invoke(name, args)

        return result

    def handle_request(
        self,
        request: str,
        project_path: str | None = None,
        confirm: bool = False,
        **context: Any,
    ) -> dict[str, Any]:
        """
        Execute a natural-language request using the existing tool stack.

        Args:
            request: Natural language goal.
            project_path: Optional project directory.
            confirm: Explicit user confirmation for risky actions.
                     Without it, risky tools ask permission_callback
                     (or are denied when no callback exists).
        """
        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        goal = (request or "").strip()
        if not goal:
            return {"success": False, "message": "No request provided"}

        self._report_progress("Starting", 0.05)

        lowered = goal.lower()
        project_target = project_path or context.get("project_path")

        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        if "vercel" in lowered and ("deploy" in lowered or "fix" in lowered):
            return self._handle_vercel_fix(goal, project_target, confirm=confirm)

        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        if any(
            word in lowered
            for word in (
                "browser",
                "open",
                "website",
                "url",
                "login",
                "netlify",
                "vercel",
            )
        ):
            url = context.get("url") or self._extract_url(goal)
            if url:
                result = self.registry.invoke(
                    "browser_open_url",
                    {"url": url, "browser": context.get("browser", "brave")},
                )
                return {
                    "success": result.ok,
                    "message": result.summary,
                    "tool": result.tool,
                    "data": result.data,
                }

        # Generic tool-based request: route through registry if a matching tool exists.
        for name in self.ROUTED_TOOLS:
            if self.is_cancelled():
                return {"success": False, "message": "Cancelled", "cancelled": True}
            if lowered.startswith(name.replace("_", " ")) or name in lowered:
                tool = self.registry.get(name)
                if tool is None:
                    continue

                # V2: permission gate for risky tools
                if tool.risk >= _CONFIRM_RISK_THRESHOLD and not confirm:
                    approved = self._request_permission(
                        name,
                        f"Tool '{name}' can make changes. Approve?",
                    )
                    if not approved:
                        self._log_activity(
                            {
                                "tool": name,
                                "outcome": "DENIED",
                                "summary": "User did not approve this action.",
                            }
                        )
                        return {
                            "success": False,
                            "message": (
                                f"I need your approval before running '{name}'. "
                                f"Confirm the action and try again."
                            ),
                            "tool": name,
                            "needs_confirmation": True,
                        }

                self._report_progress(f"Running {name}", 0.5)
                args = {"project_path": project_target}
                if name == "browser_open_url":
                    args["url"] = self._extract_url(goal) or "https://www.google.com"
                result = self._invoke_with_recovery(name, args)
                self._log_activity(
                    {
                        "tool": name,
                        "outcome": result.outcome.name,
                        "summary": result.summary[:200],
                    }
                )
                if self.is_cancelled():
                    return {"success": False, "message": "Cancelled", "cancelled": True}
                self._report_progress("Done", 1.0)
                return {
                    "success": result.ok,
                    "message": result.summary,
                    "tool": result.tool,
                    "data": result.data,
                }

        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        return {
            "success": True,
            "message": f"Request received: {goal}",
            "skills": [s.name for s in self.skills],
            "project_path": project_target,
        }

    def _handle_vercel_fix(
        self,
        goal: str,
        project_path: str | None,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Diagnose Vercel project issues and then deploy if the project is valid."""
        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        self._report_progress("Inspecting project", 0.15)
        project_result = self.registry.invoke(
            "inspect_project", {"project_path": project_path}
        )
        self._log_activity(
            {
                "tool": "inspect_project",
                "outcome": project_result.outcome.name,
                "summary": project_result.summary[:200],
            }
        )
        if not project_result.ok:
            if self.is_cancelled():
                return {"success": False, "message": "Cancelled", "cancelled": True}
            return {
                "success": False,
                "message": project_result.summary,
                "tool": project_result.tool,
                "data": project_result.data,
            }

        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}
        diagnosis = self.registry.invoke(
            "diagnose_vercel", {"project_path": project_path}
        )
        if not diagnosis.ok:
            if self.is_cancelled():
                return {"success": False, "message": "Cancelled", "cancelled": True}
            return {
                "success": False,
                "message": diagnosis.summary,
                "tool": diagnosis.tool,
                "data": diagnosis.data,
            }

        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}
        report = diagnosis.data.get("report", {})
        problems = report.get("problems", [])
        requires_user = report.get("requires_user_action", [])

        if problems:
            if self.is_cancelled():
                return {"success": False, "message": "Cancelled", "cancelled": True}
            result = {
                "success": False,
                "message": "Vercel configuration needs attention before deploy.",
                "diagnosis": report,
                "problems": problems,
                "requires_user_action": requires_user,
            }
            if requires_user:
                result["next_step"] = requires_user[0]
            return result

        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        # Deploy is destructive - always requires explicit confirmation.
        if not confirm:
            approved = self._request_permission(
                "run_vercel_deploy",
                "Deploying to production will publish changes. Approve?",
            )
            if not approved:
                self._log_activity(
                    {
                        "tool": "run_vercel_deploy",
                        "outcome": "DENIED",
                        "summary": "Deployment not approved by user.",
                    }
                )
                return {
                    "success": False,
                    "message": (
                        "Diagnosis complete, but I need your approval "
                        "before deploying to production."
                    ),
                    "diagnosis": report,
                    "needs_confirmation": True,
                }

        self._report_progress("Deploying", 0.7)
        deploy = self.registry.invoke(
            "run_vercel_deploy", {"project_path": project_path, "prod": True}
        )
        self._log_activity(
            {
                "tool": "run_vercel_deploy",
                "outcome": deploy.outcome.name,
                "summary": deploy.summary[:200],
            }
        )
        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}
        self._report_progress("Done", 1.0)
        if deploy.ok:
            return {
                "success": True,
                "message": "Vercel deployment fixed and verified.",
                "tool": deploy.tool,
                "data": deploy.data,
                "diagnosis": report,
            }

        return {
            "success": False,
            "message": deploy.summary,
            "tool": deploy.tool,
            "error": deploy.error,
            "diagnosis": report,
        }

    @staticmethod
    def _extract_url(text: str) -> str | None:
        import re

        match = re.search(r"https?://\S+", text)
        if match:
            return match.group(0).rstrip(').,;"')
        return None


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


__all__ = ["AgentOrchestrator", "get_orchestrator"]
