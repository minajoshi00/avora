"""
============================================================
AVORA Ranking Engine
============================================================

Ranks applications by relevance for search queries.
"""

import logging
import time
from typing import List, Dict, Any, Optional

from launch_history import get_launch_history, LaunchHistory

logger = logging.getLogger("RankingEngine")


class RankingEngine:
    """Ranks applications based on multiple factors."""

    def __init__(self):
        self._launch_history = get_launch_history()
        self._app_scores: Dict[str, float] = {}

    def rank_apps(self, apps: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank a list of apps by relevance to the query."""
        if not apps:
            return []

        query_lower = query.lower()
        scored = []

        for app in apps:
            score = self._calculate_score(app, query_lower)
            scored.append({**app, "_score": score})

        scored.sort(key=lambda x: x.get("_score", 0), reverse=True)
        return scored

    def _calculate_score(self, app: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for an app."""
        score = 0.0
        name = app.get("name", "").lower()
        path = app.get("path", "").lower()

        if query in name:
            score += 100.0
        if query in path:
            score += 50.0

        name_parts = name.split()
        for part in name_parts:
            if part.startswith(query):
                score += 30.0
                break

        launch_count = self._launch_history.get_count(app.get("name", ""))
        score += min(launch_count * 2, 20.0)

        return score

    def get_top_apps(self, apps: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top ranked apps."""
        ranked = self.rank_apps(apps, "")
        return ranked[:limit]


_instance = None


def get_ranking_engine() -> RankingEngine:
    """Get the singleton ranking engine."""
    global _instance
    if _instance is None:
        _instance = RankingEngine()
    return _instance


__all__ = ["RankingEngine", "get_ranking_engine"]
