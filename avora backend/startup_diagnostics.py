"""
============================================================
AVORA Startup Diagnostics
============================================================

Provides a clean startup report showing the state of all
critical AVORA subsystems. Designed to be called once after
application bootstrap to give the user/developer a clear
picture of what's available.

Example output:
    AI provider: configured
    Fallback provider: configured
    Voice: available
    Gmail: unavailable
    Analytics: connected
"""

import logging
import platform
import shutil
import time
from typing import Dict, Any, Optional

logger = logging.getLogger("StartupDiagnostics")


def _check_ai_providers() -> Dict[str, str]:
    """Check AI provider configuration."""
    result = {"primary": "unknown", "fallback": "unknown"}
    try:
        from ai_logic import GEMINI_KEY, GROQ_KEY, gemini, groq, GEMINI_MODEL, GROQ_MODEL

        # Primary (Gemini)
        if GEMINI_KEY and gemini is not None:
            result["primary"] = f"configured ({GEMINI_MODEL})"
        elif GEMINI_KEY:
            result["primary"] = "configured (client failed to init)"
        else:
            result["primary"] = "unavailable"

        # Fallback (Groq)
        if GROQ_KEY and groq is not None:
            result["fallback"] = f"configured ({GROQ_MODEL})"
        elif GROQ_KEY:
            result["fallback"] = "configured (client failed to init)"
        else:
            result["fallback"] = "unavailable"

    except Exception as e:
        logger.warning("AI provider check failed: %s", e)
        result["primary"] = "error"
        result["fallback"] = "error"

    return result


def _check_gmail() -> str:
    """Check Gmail availability."""
    try:
        from skills.email import is_gmail_available
        try:
            available = is_gmail_available()
            return "connected" if available else "unavailable"
        except Exception:
            return "unavailable"
    except Exception:
        return "unavailable"


def _check_analytics() -> str:
    """Check analytics connectivity (desktop only)."""
    try:
        from analytics import is_connected, is_enabled
        if is_enabled():
            if is_connected():
                return "connected"
            return "configured (offline)"
        return "disabled"
    except Exception:
        return "not configured"


def _check_voice_engine() -> str:
    """Check voice engine (TTS + STT)."""
    try:
        import voice
        has_tts = hasattr(voice, "speak")
        has_stt = hasattr(voice, "listen")
        if has_tts and has_stt:
            return "available"
        if has_tts:
            return "tts only"
        return "unavailable"
    except Exception:
        return "unavailable"


def get_startup_diagnostics() -> Dict[str, Any]:
    """
    Build a structured startup diagnostics report.

    Returns a dict with a summary line per subsystem.
    """
    ai = _check_ai_providers()

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "subsystems": {
            "ai_primary": ai["primary"],
            "ai_fallback": ai["fallback"],
            "voice": _check_voice_engine(),
            "gmail": _check_gmail(),
            "analytics": _check_analytics(),
            "internet": _check_internet(),
            "secure_storage": _check_secure_storage(),
        },
        "warnings": [],
    }

    # Build warning list
    if "unavailable" in report["subsystems"]["ai_primary"]:
        report["warnings"].append("Primary AI provider is unavailable - add a Gemini or Groq key in Settings")
    if "unavailable" in report["subsystems"]["ai_fallback"]:
        report["warnings"].append("No fallback AI provider configured")
    if report["subsystems"]["voice"] == "unavailable":
        report["warnings"].append("Voice system unavailable - TTS may not work")

    # Log a compact startup summary (no secrets)
    logger.info("STARTSUM | AI=%s/%s | Voice=%s | Gmail=%s | Analytics=%s | Net=%s",
        report["subsystems"]["ai_primary"],
        report["subsystems"]["ai_fallback"],
        report["subsystems"]["voice"],
        report["subsystems"]["gmail"],
        report["subsystems"]["analytics"],
        report["subsystems"]["internet"],
    )

    return report


def _check_internet() -> str:
    """Check internet connectivity (non-blocking, cached)."""
    try:
        from ai_logic import _check_internet
        return "connected" if _check_internet() else "offline"
    except Exception:
        return "unknown"


def _check_secure_storage() -> str:
    """Check secure storage availability."""
    try:
        from secure_storage import get_secure_storage
        storage = get_secure_storage()
        return "available" if storage else "unavailable"
    except Exception:
        return "unavailable"


def print_startup_diagnostics() -> None:
    """Print a human-readable startup report (no secrets)."""
    report = get_startup_diagnostics()
    print("\n" + "=" * 50)
    print("AVORA STARTUP DIAGNOSTICS")
    print("=" * 50)
    for name, value in report["subsystems"].items():
        print(f"  {name.replace('_', ' ').title()}: {value}")
    if report["warnings"]:
        print("\nWarnings:")
        for w in report["warnings"]:
            print(f"  ⚠ {w}")
    print("=" * 50 + "\n")


__all__ = [
    "get_startup_diagnostics",
    "print_startup_diagnostics",
]