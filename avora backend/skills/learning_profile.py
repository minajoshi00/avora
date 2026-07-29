"""
========================================================================
learning_profile.py
NOVA - Personal Learning & Memory Profile System
========================================================================
Tracks user preferences, learning habits, study patterns, and
provides smart context for personalized AI responses.

Key Features:
- Learning preferences (style, pace, difficulty)
- Topic tracking (what subjects user studies)
- Mistake patterns (repeated errors to help correct)
- User preferences (communication style, format preferences)
- Smart memory filtering (only save useful context)
========================================================================
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from settings import get_setting, set_setting
from app_paths import APP_DATA_DIR, BASE_DIR, ICON_PATH

PROFILE_FILE = APP_DATA_DIR / "learning_profile.json"

_profile_lock = threading.RLock()
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default empty profile structure
DEFAULT_PROFILE = {
    "learning": {
        "preferred_style": "",  # visual, auditory, reading, kinesthetic
        "preferred_pace": "",   # slow, moderate, fast
        "difficulty_level": "",  # beginner, intermediate, advanced
        "subjects_studied": [],  # list of topics/subjects explored
        "last_study_topic": "",
        "repeated_mistakes": [],  # concepts user repeatedly gets wrong
        "learning_strengths": [],  # areas user excels in
    },
    "preferences": {
        "communication_style": "friendly",  # friendly, professional, casual
        "response_detail": "balanced",      # short, balanced, detailed
        "likes_examples": True,
        "likes_analogies": True,
        "likes_quizzes": False,
        "use_emoji": True,
        "preferred_name": "",
        "language": "en",
    },
    "project_memory": {
        "current_projects": [],
        "completed_projects": [],
        "tech_stack": [],
        "project_context": {},  # key-value store for project details
    },
    "context": {
        "last_conversation_topic": "",
        "frequently_asked": [],  # repeated question patterns
        "recent_interests": [],  # topics user has shown interest in
        "daily_routine": {},     # time-based patterns
    },
    "metadata": {
        "created": "",
        "last_updated": "",
        "version": 1,
        "total_interactions": 0,
    },
}


def _load_profile() -> dict:
    """Load the learning profile from disk."""
    with _profile_lock:
        if not PROFILE_FILE.exists():
            profile = dict(DEFAULT_PROFILE)
            now = datetime.now().isoformat(timespec="seconds")
            profile["metadata"]["created"] = now
            profile["metadata"]["last_updated"] = now
            _save_profile(profile)
            return profile

        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                profile = json.load(f)
            # Merge with defaults to handle missing keys
            merged = dict(DEFAULT_PROFILE)
            _deep_merge(merged, profile)
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(DEFAULT_PROFILE)


def _save_profile(profile: dict) -> bool:
    """Save the learning profile to disk."""
    try:
        profile["metadata"]["last_updated"] = datetime.now().isoformat(timespec="seconds")
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=4, ensure_ascii=False)
        return True
    except OSError as e:
        print("[LEARNING PROFILE SAVE ERROR]", e)
        return False


def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge override dict into base dict."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# ============================================================
# PUBLIC API
# ============================================================

def get_profile() -> dict:
    """Get the full learning profile."""
    return _load_profile()


def update_learning(data: dict) -> bool:
    """Update learning-related fields."""
    profile = _load_profile()
    profile["learning"].update(data)
    return _save_profile(profile)


def update_preferences(data: dict) -> bool:
    """Update user preferences."""
    profile = _load_profile()
    profile["preferences"].update(data)
    return _save_profile(profile)


def update_project(data: dict) -> bool:
    """Update project memory fields."""
    profile = _load_profile()
    for key, value in data.items():
        if key in profile["project_memory"]:
            if isinstance(value, list):
                for item in value:
                    if item not in profile["project_memory"][key]:
                        profile["project_memory"][key].append(item)
            else:
                profile["project_memory"][key] = value
    return _save_profile(profile)


def track_topic(topic: str) -> bool:
    """Track a studied topic."""
    if not topic:
        return False
    profile = _load_profile()
    topic_lower = topic.lower().strip()
    # Check if similar topic already exists
    subjects = profile["learning"].get("subjects_studied", [])
    if not any(topic_lower in s.lower() for s in subjects):
        subjects.append(topic)
        # Keep max 50 subjects
        profile["learning"]["subjects_studied"] = subjects[-50:]
    profile["learning"]["last_study_topic"] = topic
    profile["context"]["recent_interests"].append(topic)
    profile["context"]["recent_interests"] = profile["context"]["recent_interests"][-20:]
    profile["context"]["last_conversation_topic"] = topic
    profile["metadata"]["total_interactions"] = profile["metadata"].get("total_interactions", 0) + 1
    return _save_profile(profile)


def track_mistake(concept: str) -> bool:
    """Track a repeated mistake for a concept."""
    if not concept:
        return False
    profile = _load_profile()
    mistakes = profile["learning"].get("repeated_mistakes", [])
    # Increment count if exists
    found = False
    for m in mistakes:
        if isinstance(m, dict) and m.get("concept", "").lower() == concept.lower():
            m["count"] = m.get("count", 0) + 1
            m["last_seen"] = datetime.now().isoformat(timespec="seconds")
            found = True
            break
    if not found:
        mistakes.append({
            "concept": concept,
            "count": 1,
            "last_seen": datetime.now().isoformat(timespec="seconds"),
        })
    profile["learning"]["repeated_mistakes"] = mistakes[-20:]  # Keep last 20
    return _save_profile(profile)


def add_strength(strength: str) -> bool:
    """Record a learning strength."""
    if not strength:
        return False
    profile = _load_profile()
    strengths = profile["learning"].get("learning_strengths", [])
    if strength not in strengths:
        strengths.append(strength)
        profile["learning"]["learning_strengths"] = strengths[-10:]
    return _save_profile(profile)


def get_learning_context() -> str:
    """Get a formatted string of learning context for AI prompts."""
    profile = _load_profile()

    parts = []

    # Learning preferences
    lp = profile.get("learning", {})
    prefs = []
    if lp.get("preferred_style"):
        prefs.append(f"Style: {lp['preferred_style']}")
    if lp.get("preferred_pace"):
        prefs.append(f"Pace: {lp['preferred_pace']}")
    if lp.get("difficulty_level"):
        prefs.append(f"Level: {lp['difficulty_level']}")
    if prefs:
        parts.append("Learning Preferences: " + ", ".join(prefs))

    # Subjects studied
    subjects = lp.get("subjects_studied", [])
    if subjects:
        parts.append("Subjects studied: " + ", ".join(subjects[-5:]))

    # Recent topics
    ctx = profile.get("context", {})
    recent = ctx.get("recent_interests", [])
    if recent:
        parts.append("Recent interests: " + ", ".join(recent[-3:]))

    # User preferences
    up = profile.get("preferences", {})
    name = up.get("preferred_name", "")
    if name:
        parts.append(f"User's name: {name}")

    # Repeated mistakes
    mistakes = lp.get("repeated_mistakes", [])
    if mistakes:
        mistake_texts = []
        for m in mistakes[-3:]:
            if isinstance(m, dict):
                mistake_texts.append(f"{m['concept']} (x{m.get('count', 1)})")
        if mistake_texts:
            parts.append("Concepts needing practice: " + ", ".join(mistake_texts))

    return "\n".join(parts) if parts else "No learning profile data yet."


def get_preference(key: str, default: Any = None) -> Any:
    """Get a specific preference value."""
    profile = _load_profile()
    for section in ("preferences", "learning"):
        if key in profile.get(section, {}):
            return profile[section][key]
    return default


def clear_profile() -> bool:
    """Reset the learning profile to defaults."""
    profile = dict(DEFAULT_PROFILE)
    now = datetime.now().isoformat(timespec="seconds")
    profile["metadata"]["created"] = now
    profile["metadata"]["last_updated"] = now
    return _save_profile(profile)


def export_profile(filepath: str) -> bool:
    """Export profile to a JSON file."""
    try:
        profile = _load_profile()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=4, ensure_ascii=False)
        return True
    except OSError:
        return False


# ============================================================
# SMART MEMORY FILTER
# ============================================================

def should_save_memory(text: str) -> bool:
    """Determine if a piece of information is worth saving as a long-term memory."""
    if not text or len(text) < 10:
        return False

    lower = text.lower()

    # Always save
    important_patterns = [
        "my name is",
        "i am",
        "i work",
        "i study",
        "i like",
        "i love",
        "i hate",
        "i prefer",
        "my favorite",
        "i need",
        "i want to learn",
        "i'm learning",
        "i am building",
        "my project",
        "i use",
        "my email",
        "my phone",
        "remember that",
        "don't forget",
    ]

    if any(p in lower for p in important_patterns):
        return True

    # Never save trivial messages
    trivial_patterns = [
        "ok",
        "okay",
        "thanks",
        "thank you",
        "lol",
        "haha",
        "good",
        "nice",
        "yes",
        "no",
        "cool",
        "hello",
        "hi",
        "hey",
    ]

    if lower.strip() in trivial_patterns:
        return False

    # Save if it contains substantive information (has verbs and nouns)
    word_count = len(lower.split())
    if word_count < 5:
        return False

    return True


# ============================================================
# INTEGRATION INTO AI RESPONSE
# ============================================================

def get_smart_context() -> str:
    """Get enhanced context combining memories and learning profile."""
    from memory import get_memory_text

    memory_context = get_memory_text()
    learning_context = get_learning_context()

    parts = []
    if memory_context and "No memories" not in memory_context:
        parts.append("LONG-TERM MEMORIES:\n" + memory_context)
    if learning_context and "No learning profile" not in learning_context:
        parts.append("LEARNING PROFILE:\n" + learning_context)

    return "\n\n".join(parts) if parts else ""


def track_interaction(user_message: str, ai_reply: str) -> None:
    """Track a user interaction for learning."""
    profile = _load_profile()
    profile["metadata"]["total_interactions"] = profile["metadata"].get("total_interactions", 0) + 1
    _save_profile(profile)