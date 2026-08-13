import re
from typing import Any, Optional, Union


def sanitize_user_text(text: Any) -> str:
    """Normalize user input for safer display and processing."""
    if text is None:
        return ""
    cleaned = str(text).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def clean_ai_reply(text: Any) -> str:
    """Normalize assistant replies and collapse excessive whitespace.
    Always returns a string for safe downstream consumption."""
    if text is None:
        return ""
    if isinstance(text, dict):
        payload_type = text.get("type")
        if payload_type == "image":
            # Return a descriptive string so callers always get str
            caption = text.get("caption") or "Here is your generated image 🎨"
            path = text.get("path")
            if path:
                return f"{caption}\nSaved at: {path}"
            return caption
        # For other dict types, return string representation
        return str(text)
    cleaned = str(text).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def format_status(state: str, fallback: Optional[str] = None) -> str:
    """Convert internal status tokens into user-friendly labels."""
    mapping = {
        "ready": "Ready",
        "thinking": "Thinking",
        "speaking": "Speaking",
        "error": "Error",
        "idle": "Idle",
    }
    if fallback is not None:
        return fallback
    if not state:
        return "Ready"
    return mapping.get(state, state.replace("_", " ").title())