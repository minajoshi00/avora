"""
===============================================================
                    AI FRIEND SETTINGS SYSTEM
===============================================================

Central configuration manager for the entire AI Friend application.

Features:
    • Persistent JSON settings
    • Safe default values
    • Automatic missing-setting repair
    • Corrupted JSON recovery
    • Atomic file saving
    • Automatic backup system
    • Nested setting access using dot notation
    • Thread-safe operations
    • Settings change listeners
    • Import/export support
    • Category reset
    • Full settings reset
    • Validation and normalization
    • Version migration support

Example:

    from settings import (
        get_setting,
        set_setting,
        update_settings,
    )

    voice_enabled = get_setting("voice.enabled")

    set_setting("voice.enabled", False)

    set_setting("voice.volume", 0.8)

    update_settings({
        "voice": {
            "enabled": True,
            "volume": 0.9,
        }
    })

===============================================================
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app_paths import APP_DATA_DIR, BASE_DIR, ICON_PATH


# =============================================================
# PATHS
# =============================================================

SETTINGS_FILE = APP_DATA_DIR / "settings.json"

BACKUP_DIR = APP_DATA_DIR / "settings_backups"

BACKUP_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================
# SETTINGS VERSION
# =============================================================

CURRENT_SETTINGS_VERSION = 1


# =============================================================
# DEFAULT SETTINGS
# =============================================================

DEFAULT_SETTINGS: Dict[str, Any] = {

    # =========================================================
    # GENERAL
    # =========================================================

    "general": {
        "first_run": True,
        "language": "en",
        "startup_enabled": True,
        "start_minimized": False,
        "check_for_updates": True,
    },


    # =========================================================
    # VOICE & AUDIO
    # =========================================================

    "voice": {
        "enabled": True,
        "volume": 1.0,
        "speed": 1.0,
        "voice_name": "default",

        # Speak only after the entire AI response is complete
        "speak_after_response": True,

        # Future streaming voice feature
        "speak_while_generating": False,

        "auto_stop_previous": True,

        "mute_when_window_minimized": False,

        "test_voice_text": (
            "Hey brooo, this is a test of my AI Friend voice."
        ),
    },


    # =========================================================
    # AI ENGINE
    # =========================================================

    "ai": {
        "primary_provider": "gemini",

        "fallback_provider": "groq",

        "automatic_fallback": True,

        "temperature": 0.7,

        "response_length": "balanced",

        "response_style": "friendly",

        "command_understanding": True,

        "show_processing_status": True,

        "show_provider_status": False,

        "max_conversation_messages": 12,

        "request_timeout": 30,

        "retry_attempts": 2,

        "retry_delay": 1.5,
    },


    # =========================================================
    # MEMORY
    # =========================================================

    "memory": {
        "enabled": True,

        "auto_save": True,

        "ask_before_saving": False,

        "save_important_information": True,

        "save_preferences": True,

        "save_projects": True,

        "save_goals": True,

        "max_memories": 500,

        "show_memory_notifications": False,
    },


    # =========================================================
    # CHARACTER
    # =========================================================

    "character": {
        "enabled": True,

        "size": 1.0,

        "always_on_top": False,

        "eye_tracking": True,

        "blinking": True,

        "head_movement": True,

        "emotions": True,

        "idle_animation": True,

        "talking_animation": True,

        "cursor_tracking": True,

        "animation_intensity": 1.0,

        "expression": "idle",
    },


    # =========================================================
    # APPEARANCE
    # =========================================================

    "appearance": {
        "theme": "dark",

        "accent_color": "#8B7AFF",

        "font_size": 14,

        "animation_intensity": "high",

        "glass_effect": True,

        "transparency": 0.95,

        "compact_mode": False,

        "show_timestamps": True,

        "show_message_animations": True,

        "rounded_corners": True,
    },


    # =========================================================
    # PRIVACY & SECURITY
    # =========================================================

    "privacy": {
        "confirm_power_actions": True,

        "confirm_file_deletion": True,

        "confirm_email_sending": True,

        "confirm_email_deletion": True,

        "confirm_system_changes": True,

        "allow_ai_file_creation": True,

        "allow_ai_file_opening": True,

        "allow_ai_file_deletion": False,

        "allow_ai_system_commands": True,

        "store_conversation_history": True,

        "clear_cache_on_exit": False,
    },


    # =========================================================
    # POWER & AUTOMATION
    # =========================================================

    "power": {
        "allow_shutdown": True,

        "allow_restart": True,

        "allow_sleep": True,

        "allow_hibernate": True,

        "allow_lock": True,

        "confirm_shutdown": True,

        "confirm_restart": True,

        "confirm_sleep": True,

        "confirm_hibernate": True,

        "confirm_lock": False,

        "allow_scheduled_actions": True,
    },


    # =========================================================
    # GMAIL
    # =========================================================

    "gmail": {
        "enabled": False,

        "auto_check": False,

        "check_interval": 300,

        "recent_email_count": 5,

        "confirm_send": True,

        "confirm_delete": True,

        "default_signature": "",

        "mark_as_read_after_reading": False,
    },


    # =========================================================
    # FILES & COMPUTER
    # =========================================================

    "files": {
        "enabled": True,

        "default_folder": str(Path.home() / "Documents"),

        "allow_create": True,

        "allow_open": True,

        "allow_delete": False,

        "allow_move": True,

        "allow_rename": True,

        "confirm_delete": True,

        "show_hidden_files": False,
    },


    # =========================================================
    # ADVANCED
    # =========================================================

    "advanced": {
        "debug_mode": False,

        "show_api_errors": False,

        "show_internal_errors": False,

        "api_timeout": 30,

        "max_log_files": 5,

        "enable_logging": True,

        "enable_crash_recovery": True,

        "developer_mode": False,
    },


    # =========================================================
    # SYSTEM
    # =========================================================

    "system": {
        "settings_version": CURRENT_SETTINGS_VERSION,

        "last_updated": None,

        "last_backup": None,
    },


    # =========================================================
    # SAFETY
    # =========================================================

    "safety": {
        "permission_level": 3,

        "enable_panic_hotkey": True,

        "panic_hotkey": "Ctrl+Alt+F12",

        "confirm_dangerous_actions": True,

        "sandbox_untrusted_scripts": True,

        "redact_sensitive_data": True,

        "activity_logging": True,

        "max_activity_log_entries": 500,

        "auto_clear_activity_log_days": 7,
    },


    # =========================================================
    # CLIPBOARD
    # =========================================================

    "clipboard": {
        "enabled": True,

        "max_history": 100,

        "save_images": True,

        "save_links": True,

        "save_code": True,

        "exclude_sensitive": True,

        "sync_to_cloud": False,

        "preview_enabled": True,
    },


    # =========================================================
    # AUTOMATION
    # =========================================================

    "automation": {
        "enabled": True,

        "max_concurrent_tasks": 3,

        "auto_confirm_safe_actions": False,

        "retry_failed_steps": True,

        "max_retries_per_step": 2,

        "step_timeout_seconds": 30,

        "show_step_progress": True,

        "allow_autonomous_mode": False,

        "require_confirmation_for": [
            "file_delete",
            "system_shutdown",
            "git_push",
            "email_send",
        ],
    },


    # =========================================================
    # CHARACTER CUSTOMIZATION
    # =========================================================

    "character_custom": {
        "gender": "neutral",

        "style": "robotic",

        "skin_color": "#4A90D9",

        "hair_style": "default",

        "hair_color": "#2C3E50",

        "eye_color": "#3498DB",

        "outfit": "casual",

        "accessories": [],

        "voice_profile": "default",

        "weather_clothing": True,

        "time_based_outfit": True,
    },


    # =========================================================
    # WEATHER / ENVIRONMENT
    # =========================================================

    "environment": {
        "enabled": True,

        "auto_detect_location": True,

        "default_location": "",

        "api_provider": "openweather",

        "update_interval_minutes": 30,

        "cache_duration_minutes": 60,

        "adapt_character": True,

        "adapt_voice": True,

        "adapt_behavior": True,

        "show_weather_notifications": True,
    },


    # =========================================================
    # MODES
    # =========================================================

    "modes": {
        "current_mode": "chat",

        "auto_detect_mode": True,

        "coding": {
            "enabled": True,
            "personality": "coding_expert",
            "tools": ["code_reader", "terminal", "git", "debugger"],
            "auto_save": True,
            "show_line_numbers": True,
        },
        "student": {
            "enabled": True,
            "personality": "friendly",
            "tools": ["flashcards", "quizzes", "study_plans"],
            "adaptive_difficulty": True,
            "track_progress": True,
        },
        "gamer": {
            "enabled": True,
            "personality": "gamer",
            "tools": ["screen_reader", "coach", "object_detection"],
            "permission_level": 2,
        },
        "productivity": {
            "enabled": True,
            "personality": "professional",
            "tools": ["file_organizer", "calendar", "macros"],
            "focus_hours": True,
            "app_blocker": True,
        },
    },


    # =========================================================
    # PERSONALITY STUDIO (CONSOLIDATED - single definition)
    # =========================================================

    "personality": {
        "current_personality": "friendly",

        "friendly_bro": {
            "name": "Friendly Bro",
            "description": "Casual, slang-heavy, hype friend vibes",
            "tone": "casual",
            "emoji_usage": 0.9,
            "slang_usage": 0.9,
            "proactivity": 0.6,
            "formality": 0.1,
        },
        "professional": {
            "name": "Professional",
            "description": "Polished, efficient, business-like",
            "tone": "professional",
            "emoji_usage": 0.2,
            "slang_usage": 0.0,
            "proactivity": 0.4,
            "formality": 0.9,
        },
        "calm_companion": {
            "name": "Calm Companion",
            "description": "Peaceful, zen-like, supportive",
            "tone": "calm",
            "emoji_usage": 0.3,
            "slang_usage": 0.1,
            "proactivity": 0.3,
            "formality": 0.3,
        },
        "funny_friend": {
            "name": "Funny Friend",
            "description": "Jokes, memes, playful humor",
            "tone": "playful",
            "emoji_usage": 0.8,
            "slang_usage": 0.5,
            "proactivity": 0.5,
            "formality": 0.1,
            "humor_level": 0.9,
        },
        "study_buddy": {
            "name": "Study Buddy",
            "description": "Patient tutor, encouraging teacher",
            "tone": "educational",
            "emoji_usage": 0.5,
            "slang_usage": 0.2,
            "proactivity": 0.7,
            "formality": 0.4,
            "humor_level": 0.4,
        },
        "coding_partner": {
            "name": "Coding Partner",
            "description": "Senior dev, technical but friendly",
            "tone": "technical",
            "emoji_usage": 0.3,
            "slang_usage": 0.3,
            "proactivity": 0.5,
            "formality": 0.3,
        },
        "custom": {
            "name": "Custom",
            "description": "Fully customizable personality",
            "tone": "custom",
            "emoji_usage": 0.5,
            "slang_usage": 0.3,
            "proactivity": 0.5,
            "formality": 0.5,
        },
    },


    # =========================================================
    # GAMING
    # =========================================================

    "gaming": {
        "enabled": False,

        "screen_capture_fps": 5,

        "object_detection": False,

        "voice_tips": True,

        "mouse_control": False,

        "keyboard_control": False,

        "supported_games": ["minecraft", "roblox"],

        "permission_level": 2,

        "panic_stop": True,
    },


    # =========================================================
    # STUDENT
    # =========================================================

    "student": {
        "enabled": True,

        "study_plans": True,

        "flashcards": True,

        "quizzes": True,

        "adaptive_difficulty": True,

        "mock_exams": True,

        "weak_topic_tracking": True,

        "progress_tracking": True,

        "focus_timer": True,

        "revision_support": True,

        "daily_goal_minutes": 30,
    },


    # =========================================================
    # DEVELOPER
    # =========================================================

    "developer": {
        "enabled": False,

        "project_awareness": True,

        "bug_detection": True,

        "terminal_diagnostics": True,

        "test_execution": True,

        "git_integration": True,

        "code_flowcharts": True,

        "ui_to_code": True,

        "persistent_workspaces": True,
    },


    # =========================================================
    # NOTIFICATIONS
    # =========================================================

    "notifications": {
        "enabled": True,

        "email_notifications": True,

        "reminder_notifications": True,

        "automation_notifications": True,

        "weather_notifications": True,

        "do_not_disturb": False,

        "quiet_hours_start": "22:00",

        "quiet_hours_end": "08:00",

        "notification_sound": True,

        "notification_position": "bottom_right",
    },


    # =========================================================
    # POWER & AUTOMATION (extended)
    # =========================================================

    "power_automation": {
        "allow_automation": True,

        "energy_aware_scheduling": True,

        "cpu_threshold": 80,

        "ram_threshold": 70,

        "battery_threshold": 20,

        "auto_pause_when_battery_low": True,

        "auto_pause_when_high_cpu": True,
    },


    # =========================================================
    # OFFLINE / HYBRID
    # =========================================================

    "offline": {
        "enabled": True,

        "local_ai_fallback": True,

        "local_voice": True,

        "local_file_ops": True,

        "local_computer_control": True,

        "show_mode_indicator": True,

        "privacy_mode": False,
    },


    # =========================================================
    # VOICE & AUDIO (extended)
    # =========================================================

    "voice_extended": {
        "wake_word": "hey avora",

        "wake_word_sensitivity": 0.7,

        "continuous_listening": False,

        "voice_interruption": True,

        "multiple_voices": True,

        "emotion_aware_tone": True,

        "listening_state_indicator": True,

        "speaking_state_indicator": True,

        "available_voices": {
            "en-US-AriaNeural": "Aria (Female)",
            "en-US-JennyNeural": "Jenny (Female)",
            "en-US-GuyNeural": "Guy (Male)",
            "en-US-ChristopherNeural": "Christopher (Male)",
            "en-GB-SoniaNeural": "Sonia (Female)",
            "en-GB-RyanNeural": "Ryan (Male)",
            "en-IN-NeerjaNeural": "Neerja (Female)",
            "en-IN-PrabhatNeural": "Prabhat (Male)",
        },
    },


    # =========================================================
    # MEETINGS / LECTURES
    # =========================================================

    "meetings": {
        "enabled": False,

        "transcription": False,

        "auto_summarize": True,

        "extract_action_items": True,

        "create_notes": True,

        "permission_required": True,

        "supported_formats": ["mp3", "wav", "m4a"],
    },


    # =========================================================
    # ACTIVITY AWARENESS
    # =========================================================

    "activity_awareness": {
        "enabled": True,

        "check_interval_seconds": 5,

        "idle_threshold_minutes": 3,

        "proactive_notifications": True,

        "proactive_cooldown_minutes": 15,

        "show_activity_notifications": True,

        "notify_on_activity_change": False,

        "long_session_warning_minutes": 60,

        "break_reminder_enabled": True,

        "break_reminder_interval_minutes": 45,

        "privacy_mode": False,
    },


    # =========================================================
    # COMPANION INTELLIGENCE
    # =========================================================

    "companion": {
        "enabled": True,

        "emotion_engine": True,

        "proactive_messages": True,

        "silent_awareness": True,

        "context_tracking": True,

        "goal_tracking": True,

        "achievement_celebrations": True,

        "break_reminders": True,

        "anti_annoyance": True,

        "personality_influence": True,

        "max_proactive_per_hour": 4,

        "cooldown_multiplier": 1.0,

        "intensity_multiplier": 1.0,

        "detailed_analysis_interval_seconds": 60,
    },


    # =========================================================
    # TIMER
    # =========================================================

    "timer": {
        "enabled": True,

        "notification_on_finish": True,

        "notification_sound": True,

        "notification_volume": 0.8,

        "notification_sound_path": "",

        "emotion_on_finish": "surprised",

        "speak_on_finish": True,

        "auto_restart": False,

        "auto_restart_minutes": 0,

        "default_duration_minutes": 25,
    },
}


# =============================================================
# VALIDATION RULES
# =============================================================

VALID_THEMES = {
    "light",
    "dark",
    "system",
}


VALID_PROVIDERS = {
    "gemini",
    "groq",
    "automatic",
}


VALID_RESPONSE_LENGTHS = {
    "short",
    "balanced",
    "detailed",
}


VALID_RESPONSE_STYLES = {
    "friendly",
    "professional",
    "casual",
    "creative",
}


# =============================================================
# INTERNAL STATE
# =============================================================

_settings: Dict[str, Any] = {}

_lock = threading.RLock()

_listeners: list[Callable[[str, Any, Any], None]] = []


# =============================================================
# UTILITY FUNCTIONS
# =============================================================

def _deep_merge(
    original: Dict[str, Any],
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Recursively merge dictionaries.

    Existing settings are preserved unless explicitly updated.
    """

    result = copy.deepcopy(original)

    for key, value in updates.items():

        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)

        else:
            result[key] = copy.deepcopy(value)

    return result


def _get_nested(
    data: Dict[str, Any],
    path: str,
) -> Any:
    """
    Read nested setting using dot notation.

    Example:

        _get_nested(data, "voice.volume")
    """

    current = data

    for part in path.split("."):

        if not isinstance(current, dict):

            return None

        if part not in current:

            return None

        current = current[part]

    return current


def _set_nested(
    data: Dict[str, Any],
    path: str,
    value: Any,
) -> None:
    """
    Set nested setting using dot notation.

    Example:

        _set_nested(data, "voice.volume", 0.8)
    """

    parts = path.split(".")

    current = data

    for part in parts[:-1]:

        if part not in current:

            current[part] = {}

        if not isinstance(current[part], dict):

            current[part] = {}

        current = current[part]

    current[parts[-1]] = value


def _delete_nested(
    data: Dict[str, Any],
    path: str,
) -> bool:
    """
    Delete a nested setting.
    """

    parts = path.split(".")

    current = data

    for part in parts[:-1]:

        if not isinstance(current, dict) or part not in current:

            return False

        current = current[part]

    final_key = parts[-1]

    if final_key in current:

        del current[final_key]

        return True

    return False


# =============================================================
# VALIDATION
# =============================================================

def _validate_settings(
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate and normalize settings.
    """

    # ---------------------------------------------------------
    # VOICE
    # ---------------------------------------------------------

    voice = settings.get("voice", {})

    voice["enabled"] = bool(
        voice.get("enabled", True)
    )

    try:

        voice["volume"] = float(
            voice.get("volume", 1.0)
        )

    except (TypeError, ValueError):

        voice["volume"] = 1.0

    voice["volume"] = max(
        0.0,
        min(1.0, voice["volume"])
    )

    try:

        voice["speed"] = float(
            voice.get("speed", 1.0)
        )

    except (TypeError, ValueError):

        voice["speed"] = 1.0

    voice["speed"] = max(
        0.5,
        min(2.0, voice["speed"])
    )


    # ---------------------------------------------------------
    # AI
    # ---------------------------------------------------------

    ai = settings.get("ai", {})

    if ai.get("primary_provider") not in VALID_PROVIDERS:

        ai["primary_provider"] = "gemini"

    if ai.get("fallback_provider") not in VALID_PROVIDERS:

        ai["fallback_provider"] = "groq"

    if ai.get("response_length") not in VALID_RESPONSE_LENGTHS:

        ai["response_length"] = "balanced"

    if ai.get("response_style") not in VALID_RESPONSE_STYLES:

        ai["response_style"] = "friendly"

    try:

        ai["temperature"] = float(
            ai.get("temperature", 0.7)
        )

    except (TypeError, ValueError):

        ai["temperature"] = 0.7

    ai["temperature"] = max(
        0.0,
        min(2.0, ai["temperature"])
    )


    # ---------------------------------------------------------
    # CHARACTER
    # ---------------------------------------------------------

    character = settings.get("character", {})

    try:

        character["size"] = float(
            character.get("size", 1.0)
        )

    except (TypeError, ValueError):

        character["size"] = 1.0

    character["size"] = max(
        0.5,
        min(3.0, character["size"])
    )


    # ---------------------------------------------------------
    # APPEARANCE
    # ---------------------------------------------------------

    appearance = settings.get("appearance", {})

    if appearance.get("theme") not in VALID_THEMES:

        appearance["theme"] = "dark"

    try:

        appearance["font_size"] = int(
            appearance.get("font_size", 14)
        )

    except (TypeError, ValueError):

        appearance["font_size"] = 14

    appearance["font_size"] = max(
        8,
        min(32, appearance["font_size"])
    )

    try:

        appearance["transparency"] = float(
            appearance.get("transparency", 0.95)
        )

    except (TypeError, ValueError):

        appearance["transparency"] = 0.95

    appearance["transparency"] = max(
        0.3,
        min(1.0, appearance["transparency"])
    )


    # ---------------------------------------------------------
    # MEMORY
    # ---------------------------------------------------------

    memory = settings.get("memory", {})

    try:

        memory["max_memories"] = int(
            memory.get("max_memories", 500)
        )

    except (TypeError, ValueError):

        memory["max_memories"] = 500

    memory["max_memories"] = max(
        1,
        min(10000, memory["max_memories"])
    )


    # ---------------------------------------------------------
    # SYSTEM
    # ---------------------------------------------------------

    settings.setdefault("system", {})

    settings["system"][
        "settings_version"
    ] = CURRENT_SETTINGS_VERSION

    settings["system"][
        "last_updated"
    ] = datetime.now().isoformat(
        timespec="seconds"
    )

    return settings


# =============================================================
# FILE OPERATIONS
# =============================================================

def _create_backup() -> Optional[Path]:
    """
    Create a timestamped backup of the current settings.
    """

    if not SETTINGS_FILE.exists():

        return None

    try:

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup_path = (
            BACKUP_DIR
            / f"settings_{timestamp}.json"
        )

        shutil.copy2(
            SETTINGS_FILE,
            backup_path
        )

        return backup_path

    except Exception:

        return None


def _atomic_save(
    settings: Dict[str, Any],
) -> bool:
    """
    Save settings safely using atomic replacement.

    This prevents settings.json from being corrupted
    if the application crashes during saving.
    """

    try:

        SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=SETTINGS_FILE.parent,
            delete=False,
            suffix=".tmp",
        ) as temporary_file:

            json.dump(
                settings,
                temporary_file,
                indent=4,
                ensure_ascii=False,
            )

            temporary_file.flush()

            os.fsync(
                temporary_file.fileno()
            )

            temporary_path = Path(
                temporary_file.name
            )

        os.replace(
            temporary_path,
            SETTINGS_FILE
        )

        return True

    except Exception:

        try:

            if (
                "temporary_path" in locals()
                and temporary_path.exists()
            ):

                temporary_path.unlink()

        except Exception:

            pass

        return False


# =============================================================
# LOADING
# =============================================================

def _load_settings() -> Dict[str, Any]:
    """
    Load settings from disk.

    If the file is missing:
        Create default settings.

    If corrupted:
        Backup corrupted file and recover defaults.

    If settings are incomplete:
        Automatically repair missing values.
    """

    global _settings

    with _lock:

        # -----------------------------------------------------
        # FILE DOES NOT EXIST
        # -----------------------------------------------------

        if not SETTINGS_FILE.exists():

            _settings = copy.deepcopy(
                DEFAULT_SETTINGS
            )

            _settings = _validate_settings(
                _settings
            )

            _atomic_save(
                _settings
            )

            return copy.deepcopy(
                _settings
            )


        # -----------------------------------------------------
        # LOAD EXISTING FILE
        # -----------------------------------------------------

        try:

            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8",
            ) as file:

                loaded = json.load(file)

            if not isinstance(
                loaded,
                dict
            ):

                raise ValueError(
                    "Settings must be a dictionary."
                )


        except Exception:

            # -------------------------------------------------
            # CORRUPTED SETTINGS RECOVERY
            # -------------------------------------------------

            try:

                corrupted_backup = (
                    BACKUP_DIR
                    / (
                        "corrupted_"
                        + datetime.now().strftime(
                            "%Y%m%d_%H%M%S"
                        )
                        + ".json"
                    )
                )

                if SETTINGS_FILE.exists():
                    shutil.copy2(
                        SETTINGS_FILE,
                        corrupted_backup
                    )

            except Exception:

                pass

            loaded = {}


        # -----------------------------------------------------
        # REPAIR MISSING SETTINGS
        # -----------------------------------------------------

        _settings = _deep_merge(
            DEFAULT_SETTINGS,
            loaded
        )

        _settings = _validate_settings(
            _settings
        )

        _atomic_save(
            _settings
        )

        return copy.deepcopy(
            _settings
        )


# =============================================================
# SAVE
# =============================================================

def save_settings(
    create_backup: bool = False,
) -> bool:
    """
    Save the current settings.

    Args:
        create_backup:
            Whether to create a backup before saving.
    """

    global _settings

    with _lock:

        if create_backup:

            _create_backup()

        _settings = _validate_settings(
            _settings
        )

        return _atomic_save(
            _settings
        )


# =============================================================
# GET SETTING
# =============================================================

def get_setting(
    path: str,
    default: Any = None,
) -> Any:
    """
    Get a setting using dot notation.

    Example:

        get_setting("voice.enabled")

        get_setting("voice.volume")

        get_setting(
            "unknown.setting",
            False
        )
    """

    if not path:

        return default

    with _lock:

        value = _get_nested(
            _settings,
            path
        )

        if value is None:

            return default

        return copy.deepcopy(
            value
        )


# =============================================================
# SET SETTING
# =============================================================

def set_setting(
    path: str,
    value: Any,
    save: bool = True,
) -> bool:
    """
    Change one setting.

    Example:

        set_setting(
            "voice.enabled",
            False
        )
    """

    if not path:

        return False

    with _lock:

        old_value = _get_nested(
            _settings,
            path
        )

        _set_nested(
            _settings,
            path,
            value
        )

        _validate_settings(
            _settings
        )

        new_value = _get_nested(
            _settings,
            path
        )

        if save:

            save_settings()

        _notify_listeners(
            path,
            old_value,
            new_value
        )

        return True


# =============================================================
# UPDATE MULTIPLE SETTINGS
# =============================================================

def update_settings(
    updates: Dict[str, Any],
    save: bool = True,
) -> bool:
    """
    Update multiple settings at once.

    Example:

        update_settings({
            "voice": {
                "enabled": False,
                "volume": 0.8,
            },

            "character": {
                "enabled": True,
            },
        })
    """

    if not isinstance(
        updates,
        dict
    ):

        return False

    with _lock:

        old_settings = copy.deepcopy(
            _settings
        )

        _settings.clear()

        _settings.update(
            _deep_merge(
                old_settings,
                updates
            )
        )

        _validate_settings(
            _settings
        )

        if save:

            save_settings()

        _notify_all_changes(
            old_settings,
            _settings
        )

        return True


# =============================================================
# GET ALL SETTINGS
# =============================================================

def get_all_settings() -> Dict[str, Any]:
    """
    Return a safe copy of every setting.
    """

    with _lock:

        return copy.deepcopy(
            _settings
        )


# =============================================================
# DELETE SETTING
# =============================================================

def delete_setting(
    path: str,
    save: bool = True,
) -> bool:
    """
    Delete a setting.

    Usually used for advanced settings.
    """

    with _lock:

        deleted = _delete_nested(
            _settings,
            path
        )

        if deleted and save:

            save_settings()

        return deleted


# =============================================================
# RESET ONE SETTING
# =============================================================

def reset_setting(
    path: str,
    save: bool = True,
) -> bool:
    """
    Reset one setting to its default value.
    """

    default_value = _get_nested(
        DEFAULT_SETTINGS,
        path
    )

    if default_value is None:

        return False

    return set_setting(
        path,
        copy.deepcopy(
            default_value
        ),
        save=save
    )


# =============================================================
# RESET CATEGORY
# =============================================================

def reset_category(
    category: str,
    save: bool = True,
) -> bool:
    """
    Reset an entire category.

    Example:

        reset_category("voice")
    """

    if category not in DEFAULT_SETTINGS:

        return False

    with _lock:

        _settings[category] = copy.deepcopy(
            DEFAULT_SETTINGS[category]
        )

        if save:

            save_settings()

        return True


# =============================================================
# RESET EVERYTHING
# =============================================================

def reset_all_settings(
    create_backup: bool = True,
) -> bool:
    """
    Reset the entire application to factory defaults.
    """

    global _settings

    with _lock:

        if create_backup:

            _create_backup()

        old_settings = copy.deepcopy(
            _settings
        )

        _settings = copy.deepcopy(
            DEFAULT_SETTINGS
        )

        _settings = _validate_settings(
            _settings
        )

        success = _atomic_save(
            _settings
        )

        if success:

            _notify_all_changes(
                old_settings,
                _settings
            )

        return success


# =============================================================
# CHANGE LISTENERS
# =============================================================

def add_settings_listener(
    callback: Callable[
        [str, Any, Any],
        None
    ],
) -> None:
    """
    Register a callback that runs whenever a setting changes.

    Example:

        def on_setting_changed(
            path,
            old_value,
            new_value
        ):
            print(
                path,
                old_value,
                new_value
            )

        add_settings_listener(
            on_setting_changed
        )
    """

    if not callable(callback):

        return

    with _lock:

        if callback not in _listeners:

            _listeners.append(
                callback
            )


def remove_settings_listener(
    callback: Callable,
) -> None:
    """
    Remove a settings listener.
    """

    with _lock:

        if callback in _listeners:

            _listeners.remove(
                callback
            )


def _notify_listeners(
    path: str,
    old_value: Any,
    new_value: Any,
) -> None:
    """
    Notify listeners safely.
    """

    if old_value == new_value:

        return

    for listener in list(
        _listeners
    ):

        try:

            listener(
                path,
                old_value,
                new_value
            )

        except Exception:

            # One broken listener should never
            # crash the application.
            pass


def _notify_all_changes(
    old_settings: Dict[str, Any],
    new_settings: Dict[str, Any],
    prefix: str = "",
) -> None:
    """
    Recursively detect setting changes.
    """

    all_keys = set(
        old_settings.keys()
    ) | set(
        new_settings.keys()
    )

    for key in all_keys:

        path = (
            f"{prefix}.{key}"
            if prefix
            else key
        )

        old_value = old_settings.get(
            key
        )

        new_value = new_settings.get(
            key
        )

        if (
            isinstance(old_value, dict)
            and isinstance(new_value, dict)
        ):

            _notify_all_changes(
                old_value,
                new_value,
                path
            )

        elif old_value != new_value:

            _notify_listeners(
                path,
                old_value,
                new_value
            )


# =============================================================
# IMPORT / EXPORT
# =============================================================

def export_settings(
    file_path: str | Path,
) -> bool:
    """
    Export all settings to another JSON file.
    """

    try:

        file_path = Path(
            file_path
        )

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            file_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                get_all_settings(),
                file,
                indent=4,
                ensure_ascii=False,
            )

        return True

    except Exception:

        return False


def import_settings(
    file_path: str | Path,
) -> bool:
    """
    Import settings from another JSON file.

    Missing settings are automatically repaired
    using the default settings.
    """

    try:

        file_path = Path(
            file_path
        )

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            imported = json.load(
                file
            )

        if not isinstance(
            imported,
            dict
        ):

            return False

        old_settings = get_all_settings()

        new_settings = _deep_merge(
            DEFAULT_SETTINGS,
            imported
        )

        new_settings = _validate_settings(
            new_settings
        )

        with _lock:

            _settings.clear()

            _settings.update(
                new_settings
            )

            save_settings(
                create_backup=True
            )

        _notify_all_changes(
            old_settings,
            new_settings
        )

        return True

    except Exception:

        return False


# =============================================================
# BACKUP MANAGEMENT
# =============================================================

def create_settings_backup() -> Optional[str]:
    """
    Manually create a backup.
    """

    backup = _create_backup()

    if backup:

        return str(
            backup
        )

    return None


def get_available_backups() -> list[str]:
    """
    Return available settings backups.
    """

    try:

        backups = sorted(
            BACKUP_DIR.glob(
                "*.json"
            ),
            reverse=True
        )

        return [
            str(
                backup
            )
            for backup in backups
        ]

    except Exception:

        return []


# =============================================================
# RESTORE BACKUP
# =============================================================

def restore_backup(
    backup_path: str | Path,
) -> bool:
    """
    Restore settings from a backup.
    """

    backup_path = Path(
        backup_path
    )

    if not backup_path.exists():

        return False

    return import_settings(
        backup_path
    )


# =============================================================
# UTILITY CHECKS
# =============================================================

def is_voice_enabled() -> bool:

    return bool(
        get_setting(
            "voice.enabled",
            True
        )
    )


def is_character_enabled() -> bool:

    return bool(
        get_setting(
            "character.enabled",
            True
        )
    )


def is_memory_enabled() -> bool:

    return bool(
        get_setting(
            "memory.enabled",
            True
        )
    )


def should_confirm_power_action() -> bool:

    return bool(
        get_setting(
            "privacy.confirm_power_actions",
            True
        )
    )


def should_confirm_file_deletion() -> bool:

    return bool(
        get_setting(
            "privacy.confirm_file_deletion",
            True
        )
    )


def should_confirm_email_sending() -> bool:

    return bool(
        get_setting(
            "privacy.confirm_email_sending",
            True
        )
    )


# =============================================================
# INITIALIZE SETTINGS
# =============================================================

_load_settings()


# =============================================================
# PUBLIC API
# =============================================================

__all__ = [

    # Core
    "get_setting",
    "set_setting",
    "update_settings",
    "get_all_settings",
    "save_settings",

    # Reset
    "reset_setting",
    "reset_category",
    "reset_all_settings",

    # Delete
    "delete_setting",

    # Listeners
    "add_settings_listener",
    "remove_settings_listener",

    # Import / Export
    "export_settings",
    "import_settings",

    # Backups
    "create_settings_backup",
    "get_available_backups",
    "restore_backup",

    # Helpers
    "is_voice_enabled",
    "is_character_enabled",
    "is_memory_enabled",
    "should_confirm_power_action",
    "should_confirm_file_deletion",
    "should_confirm_email_sending",

    # Constants
    "DEFAULT_SETTINGS",
    "SETTINGS_FILE",
]