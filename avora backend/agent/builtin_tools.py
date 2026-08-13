"""
Minimal built-in agent tools that plug into the existing AVORA stack.

These stay intentionally thin: they delegate to the current project
inspection, executor, and browser skill modules instead of creating a
parallel tool system.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from agent.executor import get_executor
from agent.project import detect_project, diagnose_deployment
from agent.tools import RiskLevel, Tool, ToolParam, ToolResult
from skills.browser_skill import BrowserSkill


def _resolve_project_path(project_path: Optional[str] = None) -> Path:
    """Resolve the target project directory for a tool call."""
    if project_path:
        candidate = Path(project_path).expanduser()
        if candidate.exists():
            return candidate.resolve()

    for candidate in (
        Path.cwd(),
        Path.home() / "OneDrive" / "Desktop",
        Path.home() / "Desktop",
    ):
        if candidate.exists() and (candidate / "package.json").exists():
            return candidate.resolve()

    if project_path:
        return Path(project_path).expanduser().resolve()
    return Path.cwd().resolve()


def inspect_project(project_path: Optional[str] = None) -> ToolResult:
    """Read the project metadata for the target path."""
    target = _resolve_project_path(project_path)
    info = detect_project(str(target), quick=True)
    return ToolResult.success(
        f"Inspected project at {target}",
        project_path=str(target),
        project=info.to_dict(),
    )


def diagnose_vercel(project_path: Optional[str] = None) -> ToolResult:
    """Read-only Vercel diagnosis using the existing project intelligence."""
    target = _resolve_project_path(project_path)
    report = diagnose_deployment(str(target), platform="vercel")
    return ToolResult.success(
        f"Vercel diagnosis complete for {target}",
        project_path=str(target),
        report=report,
    )


def open_browser_url(url: str, browser: str = "brave") -> ToolResult:
    """Open a URL in the visible Brave browser when available."""
    if not url:
        return ToolResult.invalid("A URL is required")

    skill = BrowserSkill()
    result = skill.open_visible_browser(url, browser_name=browser)
    if result.get("success"):
        return ToolResult.success(
            result.get("message", f"Opened {url}"),
            url=url,
            browser=browser,
            details=result,
        )
    return ToolResult.failure(
        result.get("message", f"Failed to open {url}"),
        url=url,
        browser=browser,
        error=result.get("error"),
    )


def run_vercel_deploy(project_path: Optional[str] = None, prod: bool = True) -> ToolResult:
    """Run a Vercel deploy command for the project using the existing executor."""
    target = _resolve_project_path(project_path)
    cmd = "vercel --prod --yes" if prod else "vercel --yes"
    result = get_executor().run(cmd, cwd=str(target), timeout=180)
    if result.ok:
        return ToolResult.success(
            "Vercel deployment completed",
            project_path=str(target),
            command=cmd,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    detail = result.output or result.stderr or result.stdout or "Deployment failed"
    return ToolResult.failure(
        "Vercel deployment failed",
        project_path=str(target),
        command=cmd,
        error=detail,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def register_all(registry) -> None:
    """Register the built-in tools with the shared registry."""
    registry.register(
        Tool(
            name="inspect_project",
            description="Inspect an existing project directory and expose its framework, scripts, and deployment metadata.",
            scope="filesystem_read",
            risk=RiskLevel.SAFE,
            params=[
                ToolParam("project_path", str, False, None, "Project directory to inspect"),
            ],
            handler=inspect_project,
        )
    )
    registry.register(
        Tool(
            name="diagnose_vercel",
            description="Diagnose a local Vercel deployment setup without making any network or filesystem changes.",
            scope="deployment",
            risk=RiskLevel.SAFE,
            params=[
                ToolParam("project_path", str, False, None, "Project directory to inspect"),
            ],
            handler=diagnose_vercel,
        )
    )
    registry.register(
        Tool(
            name="browser_open_url",
            description="Open a URL in the visible Brave browser for user-visible web flows and deployment steps.",
            scope="browser",
            risk=RiskLevel.SAFE,
            params=[
                ToolParam("url", str, True, None, "URL to open"),
                ToolParam("browser", str, False, "brave", "Browser channel name"),
            ],
            handler=open_browser_url,
        )
    )
    registry.register(
        Tool(
            name="run_vercel_deploy",
            description="Run the project Vercel deployment command after inspection and validation.",
            scope="deployment",
            risk=RiskLevel.MODERATE,
            params=[
                ToolParam("project_path", str, False, None, "Project directory to deploy"),
                ToolParam("prod", bool, False, True, "Deploy to production"),
            ],
            handler=run_vercel_deploy,
        )
    )


__all__ = ["register_all", "inspect_project", "diagnose_vercel", "open_browser_url", "run_vercel_deploy"]
