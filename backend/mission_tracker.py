"""
========================================================================
AVORA MISSIONS - Mission Tracking System
========================================================================

Missions represent something the user wants to accomplish.
This module provides the core data model, storage, and CRUD operations.

Architecture:
  Mission to Milestone to Task to Action

Features:
  - Hierarchical mission structure
  - Progress tracking
  - Deadline management
  - Priority levels
  - Category organization
  - Thread-safe operations
  - Atomic JSON storage
  - Automatic backups
  - Corrupted-state recovery

Integration:
  - Companion Intelligence (proactive mission suggestions)
  - Memory System (mission context persistence)
  - Automation System (task execution)
  - Character System (mission reactions)
  - AI Logic (mission understanding)

Example:
    from mission_tracker import get_mission_tracker

    tracker = get_mission_tracker()
    mission = tracker.create_mission(
        title="Build My Website",
        description="Launch a personal portfolio website",
        category="project"
    )
    tracker.add_milestone(mission.id, "Learn HTML/CSS")
    tracker.add_task(mission.id, "Complete HTML tutorial")
"""

from __future__ import annotations

import json
import os
import time
import threading
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from app_paths import APP_DATA_DIR
from settings import get_setting, set_setting

logger = logging.getLogger("MissionTracker")

# =========================================================================
# PATHS
# =========================================================================

MISSIONS_FILE = APP_DATA_DIR / "missions.json"
MISSION_BACKUP_DIR = APP_DATA_DIR / "mission_backups"
MISSION_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================================
# DATA MODELS
# =========================================================================

class Task:
    """A single actionable task within a milestone."""
    def __init__(self, title: str, description: str = "", estimated_minutes: int = 30):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.description = description
        self.estimated_minutes = estimated_minutes
        self.status = "pending"  # pending, in_progress, completed, skipped
        self.created_at = time.time()
        self.completed_at = None
        self.result = None
        self.tags = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "estimated_minutes": self.estimated_minutes,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        task = cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            estimated_minutes=data.get("estimated_minutes", 30),
        )
        task.id = data.get("id", task.id)
        task.status = data.get("status", "pending")
        task.created_at = data.get("created_at", time.time())
        task.completed_at = data.get("completed_at")
        task.result = data.get("result")
        task.tags = data.get("tags", [])
        return task


class Milestone:
    """A milestone within a mission - represents a significant checkpoint."""
    def __init__(self, title: str, description: str = ""):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.description = description
        self.status = "pending"  # pending, in_progress, completed
        self.created_at = time.time()
        self.completed_at = None
        self.tasks: List[Task] = []
        self.order = 0

    def add_task(self, task: Task) -> None:
        """Add a task to this milestone."""
        self.tasks.append(task)
        self.tasks.sort(key=lambda t: t.created_at)

    def get_progress(self) -> float:
        """Calculate milestone progress (0.0 to 1.0)."""
        if not self.tasks:
            return 0.0
        completed = sum(1 for t in self.tasks if t.status == "completed")
        return completed / len(self.tasks)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "tasks": [t.to_dict() for t in self.tasks],
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Milestone:
        milestone = cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
        )
        milestone.id = data.get("id", milestone.id)
        milestone.status = data.get("status", "pending")
        milestone.created_at = data.get("created_at", time.time())
        milestone.completed_at = data.get("completed_at")
        milestone.order = data.get("order", 0)
        try:
            milestone.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        except Exception:
            milestone.tasks = []
        return milestone


class Mission:
    """A mission represents something the user wants to accomplish."""
    def __init__(self, title: str, description: str = "", category: str = "general"):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.description = description
        self.category = category
        self.status = "active"  # active, paused, completed, abandoned
        self.priority = 2  # 1-5 (1 = lowest, 5 = highest)
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.deadline = None
        self.milestones: List[Milestone] = []
        self.tags = []
        self.context = {}  # Store relevant context (preferences, references, etc.)
        self.metadata = {}

    def add_milestone(self, milestone: Milestone) -> None:
        """Add a milestone to this mission."""
        milestone.order = len(self.milestones)
        self.milestones.append(milestone)
        self.milestones.sort(key=lambda m: m.order)

    def get_current_milestone(self) -> Optional[Milestone]:
        """Get the current in-progress milestone."""
        for milestone in self.milestones:
            if milestone.status == "in_progress":
                return milestone
        # If no in-progress milestone, return first pending
        for milestone in self.milestones:
            if milestone.status == "pending":
                return milestone
        return None

    def get_next_task(self) -> Optional[Task]:
        """Get the next actionable task."""
        milestone = self.get_current_milestone()
        if not milestone:
            return None
        for task in milestone.tasks:
            if task.status == "pending":
                return task
        return None

    def calculate_progress(self) -> float:
        """Calculate overall mission progress (0.0 to 1.0)."""
        if not self.milestones:
            return 0.0
        total_tasks = sum(len(m.tasks) for m in self.milestones)
        if total_tasks == 0:
            return 0.0
        completed_tasks = sum(
            1 for m in self.milestones for t in m.tasks if t.status == "completed"
        )
        return completed_tasks / total_tasks

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "deadline": self.deadline,
            "milestones": [m.to_dict() for m in self.milestones],
            "tags": self.tags,
            "context": self.context,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Mission:
        mission = cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            category=data.get("category", "general"),
        )
        mission.id = data.get("id", mission.id)
        mission.status = data.get("status", "active")
        mission.priority = data.get("priority", 2)
        mission.created_at = data.get("created_at", time.time())
        mission.started_at = data.get("started_at")
        mission.completed_at = data.get("completed_at")
        mission.deadline = data.get("deadline")
        mission.tags = data.get("tags", [])
        mission.context = data.get("context", {})
        mission.metadata = data.get("metadata", {})
        try:
            mission.milestones = [Milestone.from_dict(m) for m in data.get("milestones", [])]
        except Exception:
            mission.milestones = []
        return mission


# =========================================================================
# MISSION TRACKER
# =========================================================================

class MissionTracker:
    """
    Central manager for all missions.
    Handles CRUD operations, persistence, and queries.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._missions: Dict[str, Mission] = {}
        self._save_count = 0
        self._load_missions()

    def _load_missions(self) -> None:
        """Load missions from disk with corruption recovery."""
        if not MISSIONS_FILE.exists():
            self._save_missions()
            return

        try:
            with open(MISSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for mission_data in data.get("missions", []):
                    try:
                        mission = Mission.from_dict(mission_data)
                        self._missions[mission.id] = mission
                    except Exception as e:
                        logger.warning("Skipping corrupted mission entry: %s", e)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Missions file corrupted (%s). Attempting recovery from backup...", e)
            self._recover_from_backup()

    def _recover_from_backup(self) -> bool:
        """Attempt to recover missions from the most recent valid backup."""
        try:
            if not MISSION_BACKUP_DIR.exists():
                logger.warning("No mission backup directory found")
                return False

            # Find most recent backup file
            backups = sorted(
                MISSION_BACKUP_DIR.glob("missions_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if not backups:
                logger.warning("No mission backups found")
                return False

            for backup in backups:
                try:
                    with open(backup, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if not isinstance(data, dict) or "missions" not in data:
                        continue
                    self._missions.clear()
                    for mission_data in data.get("missions", []):
                        try:
                            mission = Mission.from_dict(mission_data)
                            self._missions[mission.id] = mission
                        except Exception:
                            continue
                    logger.info("Recovered %d missions from backup: %s", len(self._missions), backup.name)
                    # Restore the recovered file as the primary
                    self._save_missions()
                    return True
                except (json.JSONDecodeError, OSError):
                    continue

            logger.warning("All mission backups were invalid")
            return False
        except Exception as e:
            logger.error("Backup recovery failed: %s", e)
            return False

    def create_backup(self) -> Optional[str]:
        """Create a timestamped backup of the current missions state."""
        try:
            MISSION_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = MISSION_BACKUP_DIR / f"missions_{timestamp}.json"
            data = {
                "version": 1,
                "missions": [m.to_dict() for m in self._missions.values()],
                "last_updated": time.time(),
            }
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # Keep only the last 10 backups
            backups = sorted(MISSION_BACKUP_DIR.glob("missions_*.json"))
            for old in backups[:-10]:
                try:
                    old.unlink()
                except OSError:
                    pass
            return str(backup_path)
        except Exception as e:
            logger.error("Backup creation failed: %s", e)
            return None

    def _save_missions(self) -> bool:
        """Save missions to disk atomically with periodic backup."""
        try:
            MISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": 1,
                "missions": [m.to_dict() for m in self._missions.values()],
                "last_updated": time.time(),
            }
            # Atomic save
            temp_file = MISSIONS_FILE.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(MISSIONS_FILE)

            # Create a backup every ~10 saves (lightweight)
            self._save_count += 1
            if self._save_count % 10 == 0:
                self.create_backup()

            return True
        except Exception as e:
            logger.error("Missions save failed: %s", e)
            return False

    def create_mission(
        self,
        title: str,
        description: str = "",
        category: str = "general",
        priority: int = 2,
        deadline_days: Optional[int] = None,
    ) -> Mission:
        """Create a new mission."""
        with self._lock:
            mission = Mission(
                title=title,
                description=description,
                category=category,
            )
            mission.priority = max(1, min(5, priority))
            if deadline_days:
                mission.deadline = time.time() + (deadline_days * 86400)

            self._missions[mission.id] = mission
            self._save_missions()
            return mission

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Get a mission by ID."""
        with self._lock:
            return self._missions.get(mission_id)

    def get_all_missions(self) -> List[Mission]:
        """Get all missions."""
        with self._lock:
            return list(self._missions.values())

    def get_active_missions(self) -> List[Mission]:
        """Get active (non-completed, non-abandoned) missions."""
        with self._lock:
            return [m for m in self._missions.values() if m.status == "active"]

    def get_mission_by_title(self, title: str) -> Optional[Mission]:
        """Find a mission by title (fuzzy match)."""
        with self._lock:
            title_lower = title.lower()
            for mission in self._missions.values():
                if title_lower in mission.title.lower():
                    return mission
            return None

    def update_mission(self, mission_id: str, **kwargs) -> bool:
        """Update mission properties."""
        with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                return False

            for key, value in kwargs.items():
                if hasattr(mission, key):
                    setattr(mission, key, value)

            self._save_missions()
            return True

    def delete_mission(self, mission_id: str) -> bool:
        """Delete a mission."""
        with self._lock:
            if mission_id in self._missions:
                del self._missions[mission_id]
                self._save_missions()
                return True
            return False

    def complete_mission(self, mission_id: str) -> bool:
        """Mark a mission as completed."""
        with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                return False
            mission.status = "completed"
            mission.completed_at = time.time()
            self._save_missions()
            return True

    def abandon_mission(self, mission_id: str) -> bool:
        """Mark a mission as abandoned."""
        with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                return False
            mission.status = "abandoned"
            self._save_missions()
            return True

    def add_milestone(
        self,
        mission_id: str,
        title: str,
        description: str = "",
    ) -> Optional[Milestone]:
        """Add a milestone to a mission."""
        with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                return None

            milestone = Milestone(title=title, description=description)
            mission.add_milestone(milestone)
            self._save_missions()
            return milestone

    def add_task(
        self,
        mission_id: str,
        milestone_id: str,
        title: str,
        description: str = "",
        estimated_minutes: int = 30,
    ) -> Optional[Task]:
        """Add a task to a milestone."""
        with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                return None

            for milestone in mission.milestones:
                if milestone.id == milestone_id:
                    task = Task(
                        title=title,
                        description=description,
                        estimated_minutes=estimated_minutes,
                    )
                    milestone.add_task(task)
                    self._save_missions()
                    return task
            return None

    def complete_task(self, mission_id: str, task_id: str) -> bool:
        """Mark a task as completed."""
        with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                return False

            for milestone in mission.milestones:
                for task in milestone.tasks:
                    if task.id == task_id:
                        task.status = "completed"
                        task.completed_at = time.time()

                        # Check if milestone is complete
                        if all(t.status == "completed" for t in milestone.tasks):
                            milestone.status = "completed"
                            milestone.completed_at = time.time()

                        # Check if mission is complete
                        if mission.calculate_progress() >= 1.0:
                            mission.status = "completed"
                            mission.completed_at = time.time()

                        self._save_missions()
                        return True
            return False

    def skip_task(self, mission_id: str, task_id: str) -> bool:
        """Mark a task as skipped."""
        with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                return False

            for milestone in mission.milestones:
                for task in milestone.tasks:
                    if task.id == task_id:
                        task.status = "skipped"
                        task.completed_at = time.time()
                        self._save_missions()
                        return True
            return False

    def get_next_action(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get the recommended next action for a mission."""
        with self._lock:
            mission = self._missions.get(mission_id)
            if not mission or mission.status != "active":
                return None

            task = mission.get_next_task()
            if not task:
                return None

            milestone = mission.get_current_milestone()
            return {
                "mission_id": mission.id,
                "mission_title": mission.title,
                "milestone_id": milestone.id if milestone else None,
                "milestone_title": milestone.title if milestone else None,
                "task_id": task.id,
                "task_title": task.title,
                "task_description": task.description,
                "estimated_minutes": task.estimated_minutes,
                "progress": mission.calculate_progress(),
            }

    def get_mission_summary(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of mission progress."""
        with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                return None

            total_tasks = sum(len(m.tasks) for m in mission.milestones)
            completed_tasks = sum(
                1 for m in mission.milestones for t in m.tasks if t.status == "completed"
            )
            current_task = mission.get_next_task()

            return {
                "id": mission.id,
                "title": mission.title,
                "description": mission.description,
                "category": mission.category,
                "status": mission.status,
                "priority": mission.priority,
                "progress": mission.calculate_progress(),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "total_milestones": len(mission.milestones),
                "completed_milestones": sum(1 for m in mission.milestones if m.status == "completed"),
                "deadline": mission.deadline,
                "days_remaining": (mission.deadline - time.time()) / 86400 if mission.deadline else None,
                "current_task": current_task.title if current_task else None,
                "next_action": self.get_next_action(mission_id),
            }

    def search_missions(self, query: str) -> List[Mission]:
        """Search missions by title or description."""
        with self._lock:
            query_lower = query.lower()
            results = []
            for mission in self._missions.values():
                if (query_lower in mission.title.lower() or
                    query_lower in mission.description.lower() or
                    query_lower in mission.category.lower()):
                    results.append(mission)
            return results

    def get_missions_by_category(self, category: str) -> List[Mission]:
        """Get all missions in a category."""
        with self._lock:
            return [m for m in self._missions.values() if m.category == category]

    def cleanup_completed(self, older_than_days: int = 30) -> int:
        """Remove completed missions older than specified days."""
        with self._lock:
            cutoff = time.time() - (older_than_days * 86400)
            to_remove = [
                mid for mid, m in self._missions.items()
                if m.status == "completed" and m.completed_at and m.completed_at < cutoff
            ]
            for mid in to_remove:
                del self._missions[mid]
            if to_remove:
                self._save_missions()
            return len(to_remove)


# =========================================================================
# GLOBAL INSTANCE
# =========================================================================

_tracker: Optional[MissionTracker] = None
_tracker_lock = threading.Lock()


def get_mission_tracker() -> MissionTracker:
    """Get the global mission tracker instance."""
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:
                _tracker = MissionTracker()
    return _tracker


# =========================================================================
# PUBLIC API
# =========================================================================

__all__ = [
    "Task",
    "Milestone",
    "Mission",
    "MissionTracker",
    "get_mission_tracker",
]