"""
============================================================
AVORA Browser Skill
============================================================

Handles web browsing operations:
- Opening websites
- Web searches
- Browser management
"""

import os
import re
import logging
import subprocess
from typing import Dict, Any, Optional
from urllib.parse import quote_plus
import webbrowser

try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    sync_playwright = None

from skills.skill_base import BaseSkill, register_skill

logger = logging.getLogger("BrowserSkill")


class BrowserSkill(BaseSkill):
    """Skill for web browsing operations."""
    
    def __init__(self):
        super().__init__(
            name="browser_skill",
            description="Web browsing and search operations"
        )
        self._website_aliases = {
            "google": "https://www.google.com",
            "gmail": "https://mail.google.com",
            "github": "https://github.com",
            "chatgpt": "https://chat.openai.com",
            "youtube": "https://www.youtube.com",
            "netflix": "https://www.netflix.com",
            "wikipedia": "https://www.wikipedia.org",
            "amazon": "https://www.amazon.com",
            "reddit": "https://www.reddit.com",
            "instagram": "https://www.instagram.com",
            "facebook": "https://www.facebook.com",
            "twitter": "https://twitter.com",
            "linkedin": "https://www.linkedin.com",
            "stackoverflow": "https://stackoverflow.com",
            "docs": "https://developer.mozilla.org",
            "stackoverflow": "https://stackoverflow.com",
        }
    
    def can_handle(self, intent: str, params: Dict[str, Any]) -> bool:
        """Can handle browser/web intents."""
        from core.intelligence_engine import IntentType
        return intent in [
            IntentType.SEARCH_WEB,
            IntentType.OPEN_APP,
        ]
    
    def plan(self, intent: str, params: Dict[str, Any],
              context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create plan for web/browser operations."""
        target = params.get("target", "")
        entities = params.get("entities", {})
        
        if not target:
            return None
        
        plan = {
            "skill": "browser_skill",
            "action": "execute",
            "intent": intent,
            "target": target,
            "context": context,
            "steps": []
        }
        
        if intent == "search_web":
            query = target.replace("search for", "").replace("google", "").strip()
            plan["steps"].append({
                "type": "search",
                "query": query
            })
        else:
            # Check if website alias
            target_lower = target.lower()
            if target_lower in self._website_aliases:
                plan["steps"].append({
                    "type": "open_url",
                    "url": self._website_aliases[target_lower]
                })
            elif "://" in target:
                plan["steps"].append({
                    "type": "open_url",
                    "url": target
                })
            else:
                plan["steps"].append({
                    "type": "search",
                    "query": target
                })
        
        return plan
    
    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser plan."""
        steps = plan.get("steps", [])
        results = []
        
        for step in steps:
            step_type = step.get("type")
            
            if step_type == "search":
                result = self._web_search(step.get("query", ""))
            elif step_type == "open_url":
                result = self._open_url(step.get("url", ""))
            else:
                result = {"success": False, "message": f"Unknown browser action: {step_type}"}
            
            results.append(result)
        
        if results:
            last = results[-1]
            return {
                "success": True if last.get("success") else False,
                "message": last.get("message", "Browser action completed"),
                "results": results
            }
        
        return {"success": False, "message": "No valid actions", "results": results}
    
    def open_visible_browser(self, url: str, browser_name: str = "brave") -> Dict[str, Any]:
        """Open a real visible browser window with Playwright when available."""
        if not url:
            return {"success": False, "message": "No URL provided"}

        browser_names = [browser_name.lower(), "brave", "chrome", "chromium"]
        try:
            if sync_playwright is not None:
                with sync_playwright() as p:
                    browser = None
                    for name in browser_names:
                        try:
                            browser = p.chromium.launch(channel=name, headless=False)
                            break
                        except Exception:
                            continue
                    if browser is None:
                        for name in browser_names:
                            try:
                                browser = p.chromium.launch(headless=False)
                                break
                            except Exception:
                                continue
                    if browser is None:
                        raise RuntimeError("No Playwright browser could be launched")
                    page = browser.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    browser.contexts[0].pages[0].bring_to_front()
                    return {"success": True, "message": f"Opened {url} in visible {browser_name} browser"}
        except Exception as exc:
            logger.warning("Playwright browser launch failed, falling back to default browser: %s", exc)

        try:
            webbrowser.open(url)
            return {"success": True, "message": f"Opening: {url}"}
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            return {"success": False, "message": f"Failed to open: {e}"}

    def _web_search(self, query: str) -> Dict[str, Any]:
        """Perform a web search."""
        if not query:
            return {"success": False, "message": "No search query provided"}
        
        encoded_query = quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        
        try:
            return self.open_visible_browser(url)
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"success": False, "message": f"Failed to open search: {e}"}
    
    def _open_url(self, url: str) -> Dict[str, Any]:
        """Open a specific URL."""
        if not url:
            return {"success": False, "message": "No URL provided"}
        
        try:
            return self.open_visible_browser(url)
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            return {"success": False, "message": f"Failed to open: {e}"}

    def extract_youtube_video_info(self, url: str) -> Dict[str, Any]:
        """Extract title, upload date, and view count from a YouTube video URL."""
        if not url:
            return {"success": False, "message": "No URL provided"}
        
        if sync_playwright is None:
            return {"success": False, "message": "Playwright not available"}
        
        try:
            with sync_playwright() as p:
                browser = None
                for name in ["brave", "chrome", "chromium"]:
                    try:
                        browser = p.chromium.launch(channel=name, headless=True)
                        break
                    except Exception:
                        continue
                if browser is None:
                    browser = p.chromium.launch(headless=True)
                
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Try to extract title
                title = "I couldn't read that value"
                try:
                    # YouTube title selector: h1.title yt-formatted-string
                    title_element = page.wait_for_selector('h1.title yt-formatted-string', timeout=5000)
                    title = title_element.inner_text().strip()
                except Exception:
                    try:
                        # Alternative selector
                        title_element = page.wait_for_selector('#title h1 yt-formatted-string', timeout=5000)
                        title = title_element.inner_text().strip()
                    except Exception:
                        pass
                
                # Upload date
                upload_date = "I couldn't read that value"
                try:
                    # YouTube upload date: #info-strings yt-formatted-string
                    date_element = page.wait_for_selector('#info-strings yt-formatted-string', timeout=5000)
                    upload_date = date_element.inner_text().strip()
                except Exception:
                    try:
                        # Alternative
                        date_element = page.wait_for_selector('#date yt-formatted-string', timeout=5000)
                        upload_date = date_element.inner_text().strip()
                    except Exception:
                        pass
                
                # View count
                view_count = "I couldn't read that value"
                try:
                    # View count is in the same info-strings, often the first yt-formatted-string
                    view_elements = page.query_selector_all('#info-strings yt-formatted-string')
                    if view_elements:
                        # Sometimes the first is views, second is date
                        view_count = view_elements[0].inner_text().strip()
                        # If the view count doesn't contain a number, try the next
                        if not any(c.isdigit() for c in view_count):
                            if len(view_elements) > 1:
                                view_count = view_elements[1].inner_text().strip()
                    else:
                        # Try another selector
                        view_element = page.wait_for_selector('.view-count', timeout=5000)
                        view_count = view_element.inner_text().strip()
                except Exception:
                    pass
                
                browser.close()
                
                return {
                    "success": True,
                    "title": title,
                    "upload_date": upload_date,
                    "view_count": view_count,
                    "message": "Extraction completed"
                }
        except Exception as exc:
            logger.error(f"Failed to extract YouTube info: {exc}")
            return {"success": False, "message": f"Failed to extract data: {exc}"}

    def extract_general_data(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data from a URL using provided CSS selectors."""
        if not url:
            return {"success": False, "message": "No URL provided"}
        if not selectors:
            return {"success": False, "message": "No selectors provided"}
        
        if sync_playwright is None:
            return {"success": False, "message": "Playwright not available"}
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                extracted = {}
                for key, selector in selectors.items():
                    value = "I couldn't read that value"
                    try:
                        element = page.wait_for_selector(selector, timeout=5000)
                        value = element.inner_text().strip()
                    except Exception:
                        # Keep the default message
                        pass
                    extracted[key] = value
                
                browser.close()
                
                return {
                    "success": True,
                    "data": extracted,
                    "message": "Extraction completed"
                }
        except Exception as exc:
            logger.error(f"Failed to extract general data: {exc}")
            return {"success": False, "message": f"Failed to extract data: {exc}"}

    def _scroll_page(self, page, times=2, delay=1000):
        """Scroll down the page to load more content."""
        for _ in range(times):
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(delay)


skill = BrowserSkill()
register_skill("browser_skill", skill)

__all__ = ["BrowserSkill", "skill"]
