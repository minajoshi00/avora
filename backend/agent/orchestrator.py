"""
Cancelable AgentOrchestrator
Adds cancellation support to the existing orchestrator.
"""

import logging
from typing import Any, Dict, Optional

from agent.tools import get_registry
from skills import get_enabled_skills

logger = logging.getLogger("AgentOrchestrator")


class AgentOrchestrator:
    """Coordinate a goal across the existing tool registry and skill system."""

    def __init__(self, registry=None):
        self.registry = registry or get_registry()
        self.skills = get_enabled_skills()
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the current operation."""
        self._cancelled = True
        logger.info("Cancellation requested")

    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled

    def handle_request(self, request: str, project_path: Optional[str] = None, **context: Any) -> Dict[str, Any]:
        """Execute a natural-language request using the existing tool and skill stack."""
        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        goal = (request or "").strip()
        if not goal:
            return {"success": False, "message": "No request provided"}

        lowered = goal.lower()
        project_target = project_path or context.get("project_path")

        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        if "vercel" in lowered and ("deploy" in lowered or "fix" in lowered):
            return self._handle_vercel_fix(goal, project_target)

        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        if any(word in lowered for word in ("browser", "open", "website", "url", "login", "netlify", "vercel")):
            url = context.get("url") or self._extract_url(goal)
            if url:
                result = self.registry.invoke("browser_open_url", {"url": url, "browser": context.get("browser", "brave")})
                return {"success": result.ok, "message": result.summary, "tool": result.tool, "data": result.data}

        # Generic tool-based request: route through registry if a matching tool exists.
        for name in ("inspect_project", "diagnose_vercel", "browser_open_url", "run_vercel_deploy"):
            if self.is_cancelled():
                return {"success": False, "message": "Cancelled", "cancelled": True}
            if lowered.startswith(name.replace("_", " ")) or name in lowered:
                tool = self.registry.get(name)
                if tool is None:
                    continue
                args = {"project_path": project_target}
                if name == "browser_open_url":
                    args["url"] = self._extract_url(goal) or "https://www.google.com"
                result = self.registry.invoke(name, args)
                if self.is_cancelled():
                    return {"success": False, "message": "Cancelled", "cancelled": True}
                return {"success": result.ok, "message": result.summary, "tool": result.tool, "data": result.data}

        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        return {
            "success": True,
            "message": f"Request received: {goal}",
            "skills": [s.name for s in self.skills],
            "project_path": project_target,
        }

    def _handle_vercel_fix(self, goal: str, project_path: Optional[str]) -> Dict[str, Any]:
        """Diagnose Vercel project issues and then deploy if the project is valid."""
        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}
        project_result = self.registry.invoke("inspect_project", {"project_path": project_path})
        if not project_result.ok:
            if self.is_cancelled():
                return {"success": False, "message": "Cancelled", "cancelled": True}
            return {"success": False, "message": project_result.summary, "tool": project_result.tool, "data": project_result.data}

        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}
        diagnosis = self.registry.invoke("diagnose_vercel", {"project_path": project_path})
        if not diagnosis.ok:
            if self.is_cancelled():
                return {"success": False, "message": "Cancelled", "cancelled": True}
            return {"success": False, "message": diagnosis.summary, "tool": diagnosis.tool, "data": diagnosis.data}

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
        deploy = self.registry.invoke("run_vercel_deploy", {"project_path": project_path, "prod": True})
        if self.is_cancelled():
            return {"success": False, "message": "Cancelled", "cancelled": True}
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
    def _extract_url(text: str) -> Optional[str]:
        import re

        match = re.search(r"https?://\S+", text)
        if match:
            return match.group(0).rstrip(").,;\"")
        return None


_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


__all__ = ["AgentOrchestrator", "get_orchestrator"]