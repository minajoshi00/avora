# ============================================================
# CONTEXT-AWARE SEARCH — REGRESSION TEST
# ============================================================
# Verifies the SEARCH_WEB executor routes to a destination-specific
# search (e.g. YouTube) when the planner attaches a destination
# context, and preserves generic web search otherwise.
#
#   "Open YouTube and search Mr Beast"
#       -> SEARCH_WEB("mr beast", context="youtube")  -> YouTube search
#
#   "Open Chrome and search Minecraft shaders" / "Search Mr Beast"
#       -> SEARCH_WEB(query)  [no context]            -> generic web search
# ============================================================

from __future__ import annotations

import asyncio

from avora_backend.action_model import Action, ActionType
from avora_backend.skills.browser_skill import BrowserSkill


class FakePage:
    """Deterministic stand-in for a Playwright Page (no network)."""

    def __init__(self) -> None:
        self.url = "about:blank"
        self.title = None
        self.goto_calls: list[str] = []

    async def goto(self, url: str) -> None:
        self.goto_calls.append(url)
        self.url = url
        self.title = "Loaded"


def _run(coro):
    return asyncio.run(coro)


def _skill_with_fake_page() -> BrowserSkill:
    skill = BrowserSkill(headless=True)
    skill._page = FakePage()  # bypass real Playwright launch
    return skill


def _search_action(
    query: str,
    *,
    parameters=None,
    metadata=None,
) -> Action:
    return Action(
        action_type=ActionType.SEARCH_WEB,
        target=query,
        parameters=parameters or {},
        metadata=metadata or {},
    )


def test_search_with_youtube_context_routes_to_youtube():
    """'Open YouTube and search Mr Beast' must search INSIDE YouTube."""
    skill = _skill_with_fake_page()
    action = _search_action(
        "mr beast", parameters={"search_context": "youtube"}
    )
    result = _run(skill.execute(action))

    page = skill._page
    assert page.goto_calls, "search navigation should have occurred"
    url = page.goto_calls[0]
    assert "youtube.com/results" in url, f"expected YouTube search URL, got {url}"
    assert "search_query=" in url and "mr+beast" in url
    assert "google.com" not in url, "must NOT open a generic web search"
    assert result.get("status") == "executed"


def test_search_with_context_via_metadata_routes_to_youtube():
    """Context may also arrive via action.metadata."""
    skill = _skill_with_fake_page()
    action = _search_action("minecraft shaders", metadata={"context": "youtube"})
    _run(skill.execute(action))

    url = skill._page.goto_calls[0]
    assert "youtube.com/results" in url
    assert "search_query=minecraft+shaders" in url


def test_search_without_context_stays_generic_google():
    """No destination context => generic web search is preserved."""
    skill = _skill_with_fake_page()
    action = _search_action("Mr Beast")
    _run(skill.execute(action))

    url = skill._page.goto_calls[0]
    assert url.startswith("https://www.google.com/search?q=")
    assert "youtube.com" not in url


def test_open_chrome_then_search_is_generic_web_search():
    """'Open Chrome and search Minecraft shaders' => generic web search."""
    skill = _skill_with_fake_page()
    action = _search_action(
        "minecraft shaders", parameters={"search_context": "chrome"}
    )
    _run(skill.execute(action))

    url = skill._page.goto_calls[0]
    assert url.startswith("https://www.google.com/search?q=")
    assert "youtube.com" not in url


def test_search_query_comes_from_target_when_no_parameters():
    """The planner may pass the query as target with context separately."""
    skill = _skill_with_fake_page()
    action = _search_action("funny cat videos", parameters={"context": "youtube"})
    _run(skill.execute(action))

    url = skill._page.goto_calls[0]
    assert "youtube.com/results" in url
    assert "search_query=funny+cat+videos" in url