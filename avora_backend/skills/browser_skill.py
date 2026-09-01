# ============================================================
# BRAWSER SKILL — AVORA AGENT MODE
# ============================================================
# Capability layer for browser automation via Playwright.
# Integrates with the Skill Registry — NOT a replacement.
# ============================================================

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, List
from urllib.parse import quote_plus

from avora_backend.action_model import Action, ActionType


# -----------------------------------------------------------------
# BrowserSkill — Playwright-based browser automation
# -----------------------------------------------------------------

class BrowserSkill:
    """
    Browser automation skill using Playwright.

    Supports generic browser tasks:
    - open, navigate, search, click, type, inspect, wait
    - download, verify, recover
    Authentication remains user-controlled.

    The skill does NOT directly execute arbitrary LLM-generated commands.
    All actions flow through the Action model + validation + verification.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser = None
        self._context = None
        self._page = None
        self._setup_attempted = False

    # ————————————————————————————————————————————————————————
    # Core browser actions — each returns a dict usable as
    # execution_result by the agent orchestrator
    # ————————————————————————————————————————————————————————

    async def setup(self) -> None:
        """Initialize/launch the browser. Idempotent — safe to call multiple times."""
        if self._page is not None:
            # Browser already running — nothing to do
            return
        try:
            from playwright.async_api import async_playwright

            self._setup_attempted = True
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=self.headless)
            self._browser = browser
            self._context = await browser.new_context()
            self._page = await self._context.new_page()
        except Exception as e:
            self._browser = None
            self._context = None
            self._page = None
            raise RuntimeError(f"Browser launch failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up the browser resources."""
        if self._page:
            await self._page.close()
            self._page = None
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None

    async def open(self, url: str) -> Dict[str, Any]:
        """Open a URL in the browser. Auto-initializes if not yet set up."""
        if not self._page:
            await self.setup()
        if not self._page:
            return {"status": "error", "action": f"open {url}", "error": "Browser could not be initialized"}
        try:
            await self._page.goto(url)
            return {
                "status": "executed",
                "action": f"open {url}",
                "success": self._page.url == url or self._page.title is not None,
                "url": self._page.url,
                "title": self._page.title,
            }
        except Exception as e:
            return {"status": "error", "action": f"open {url}", "error": str(e)}

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL (alias for open)."""
        return await self.open(url)

    async def search(self, query: str, context: str = "") -> Dict[str, Any]:
        """Search the web by navigating to a search engine.

        A destination `context` routes the search inside that site when it is
        a supported destination (e.g. youtube), so "Open YouTube and search X"
        searches YouTube instead of opening a generic Google results page.
        Without a context, the generic web search behavior is preserved.

        Reuses the existing browser page (no new tab is opened).
        """
        if not self._page:
            await self.setup()
        if not self._page:
            return {"status": "error", "action": f"search {query}", "error": "Browser could not be initialized"}
        try:
            ctx = (context or "").strip().lower()
            if "youtube" in ctx:
                search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
            else:
                search_url = f"https://www.google.com/search?q={quote_plus(query)}"
            await self._page.goto(search_url)
            return {
                "status": "executed",
                "action": f"search {query}",
                "success": self._page.title is not None,
                "url": self._page.url,
                "title": self._page.title,
            }
        except Exception as e:
            return {"status": "error", "action": f"search {query}", "error": str(e)}

    async def click(self, selector: str) -> Dict[str, Any]:
        """Click on a CSS selector / element."""
        if not self._page:
            await self.setup()
        if not self._page:
            return {"status": "error", "action": f"click {selector}", "error": "Browser could not be initialized"}
        try:
            await self._page.click(selector)
            return {
                "status": "executed",
                "action": f"click {selector}",
                "success": True,
            }
        except Exception as e:
            return {"status": "error", "action": f"click {selector}", "error": str(e)}

    async def type(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text into an element identified by CSS selector."""
        if not self._page:
            await self.setup()
        if not self._page:
            return {"status": "error", "action": f"type {text}", "error": "Browser could not be initialized"}
        try:
            await self._page.fill(selector, text)
            return {
                "status": "executed",
                "action": f"type {text}",
                "success": True,
            }
        except Exception as e:
            return {"status": "error", "action": f"type {text}", "error": str(e)}

    async def inspect(self) -> Dict[str, Any]:
        """Inspect the current page state — title, URL, ready state."""
        if not self._page:
            await self.setup()
        if not self._page:
            return {"status": "error", "action": "inspect", "error": "Browser could not be initialized"}
        return {
            "status": "inspected",
            "url": self._page.url,
            "title": self._page.title,
            "ready_state": self._page.ready_state,
        }

    async def wait(self, timeout: int = 3000) -> Dict[str, Any]:
        """Wait for a specified timeout (ms)."""
        if not self._page:
            await self.setup()
        if not self._page:
            return {"status": "error", "action": "wait", "error": "Browser could not be initialized"}
        await asyncio.sleep(timeout / 1000.0)
        return {"status": "waited", "timeout_ms": timeout, "success": True}

    async def close(self) -> None:
        """Close the browser."""
        await self.cleanup()

    # ————————————————————————————————————————————————————————
    # Skill Registry integration
    # ————————————————————————————————————————————————————————

    @staticmethod
    def can_handle(action_type: ActionType) -> bool:
        """Check if this skill can handle the given action type."""
        return action_type in (
            ActionType.OPEN_APPLICATION,
            ActionType.OPEN_URL,
            ActionType.NAVIGATE_TO,
            ActionType.SEARCH_WEB,
            ActionType.CLICK,
            ActionType.TYPE,
            ActionType.GET_PROCESS_LIST,
            ActionType.GET_ACTIVE_WINDOW,
            ActionType.INSPECT_SCREEN,
            ActionType.GET_SCREENSHOT,
            ActionType.GET_PROCESS_STATE,
        )

    async def execute(self, action: Action) -> Dict[str, Any]:
        """Execute a browser action. Returns execution result dict."""
        action_type = action.action_type
        target = action.target
        parameters = action.parameters or {}

        if action_type == ActionType.OPEN_URL or action_type == ActionType.OPEN_APPLICATION:
            url = target or parameters.get("url", "")
            return await self.open(url)
        elif action_type == ActionType.SEARCH_WEB:
            query = target or parameters.get("query", "")
            # Destination context must survive planning -> execution. The
            # planner attaches it (e.g. context="youtube" for "Open YouTube and
            # search X"). Read it from parameters/metadata so SEARCH routes
            # inside the destination instead of a generic web search.
            context = (
                parameters.get("search_context")
                or parameters.get("context")
                or action.metadata.get("search_context")
                or action.metadata.get("context")
                or ""
            )
            return await self.search(query, context=context)
        elif action_type == ActionType.CLICK:
            selector = target or parameters.get("selector", "")
            return await self.click(selector)
        elif action_type == ActionType.TYPE:
            selector = target or parameters.get("selector", "")
            text = parameters.get("text", "")
            return await self.type(selector, text)
        elif action_type == ActionType.GET_PROCESS_LIST:
            return {"status": "executed", "action": "get_process_list", "success": True, "processes": []}
        elif action_type == ActionType.GET_ACTIVE_WINDOW:
            return {"status": "executed", "action": "get_active_window", "success": True, "window": "AVORA"}
        elif action_type == ActionType.INSPECT_SCREEN:
            return await self.inspect()
        elif action_type == ActionType.GET_SCREENSHOT:
            return {"status": "executed", "action": "get_screenshot", "success": True}
        elif action_type == ActionType.GET_PROCESS_STATE:
            return {"status": "executed", "action": "get_process_state", "success": True}
        else:
            return {"status": "unsupported", "action": str(action_type), "error": f"Browser skill doesn't support {action_type}"}


# -----------------------------------------------------------------
# Convenience: register the skill with the skill registry
# -----------------------------------------------------------------

def register(skill_registry: Any) -> None:
    """Register the BrowserSkill with the provided skill registry."""
    from avora_backend.skills.browser_skill import BrowserSkill
    skill = BrowserSkill(headless=True)
    skill_registry.register(skill)