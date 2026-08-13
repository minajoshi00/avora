"""
============================================================
                    AI FRIEND
                  AI LOGIC ENGINE
============================================================

ADVANCED CONNECTED SYSTEMS
------------------------------------------------------------
• Gemini AI
• Groq AI fallback
• Automatic provider routing
• Settings system
• Long-term memory
• AI image generation
• Gmail
• Windows power commands
• Universal application launching
• Installed app discovery
• Start Menu app discovery
• Browser launching
• Website launching
• Google searching
• YouTube searching
• File operations
• Folder operations
• Conversation history
• Safe error handling
============================================================
"""

from __future__ import annotations

# ============================================================
# IMPORTS
# ============================================================

import os
import re
import json
import time
import shutil
import webbrowser
import subprocess
import sys
import platform
import socket
import traceback
import logging

from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus

from app_utils import clean_ai_reply, sanitize_user_text

logger = logging.getLogger("AILogic")

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv():
        return False

try:
    from google import genai
except ImportError:  # pragma: no cover - optional dependency
    genai = None

try:
    from groq import Groq
except ImportError:  # pragma: no cover - optional dependency
    Groq = None


# ============================================================
# CROSS-PLATFORM HELPERS
# ============================================================

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


def _open_path(path: str) -> bool:
    """Open a file or folder with the system default application."""
    try:
        if IS_WINDOWS:
            os.startfile(path)
        elif IS_MACOS:
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception as e:
        print(f"[OPEN PATH ERROR] {e}")
        return False

# Backward compatibility aliases
_open_file_explorer = _open_path
_open_file_default = _open_path


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

_ENV_LOADED = False
_ENV_ERRORS = []

try:
    from app_paths import APP_DATA_DIR, BASE_DIR
    _env_candidates = [
        APP_DATA_DIR / ".env",
        BASE_DIR / ".env",
        Path.cwd() / ".env",
    ]
    if getattr(sys, "_MEIPASS", None):
        _env_candidates.insert(0, Path(sys._MEIPASS) / ".env")

    for _env_path in _env_candidates:
        if _env_path.exists():
            try:
                load_dotenv(_env_path)
                if os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY"):
                    _ENV_LOADED = True
                    print(f"[AI] Loaded .env from: {_env_path}")
                    break
            except Exception as e:
                _ENV_ERRORS.append(f"{_env_path}: {e}")

    if not _ENV_LOADED:
        try:
            load_dotenv()
            if os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY"):
                _ENV_LOADED = True
                print("[AI] Loaded .env from current directory")
        except Exception as e:
            _ENV_ERRORS.append(f"CWD: {e}")

    if not _ENV_LOADED:
        print("[AI] .env not found. Will try secure storage for API keys.")
        if _ENV_ERRORS:
            print(f"[AI] .env load errors: {_ENV_ERRORS}")

except Exception as e:
    print("[AI] Environment loading error:", e)

# ============================================================
# SECURE STORAGE FALLBACK
# ============================================================

try:
    from secure_storage import get_secure_storage, mask_key as secure_mask_key
    
    _secure_storage = get_secure_storage()
    _stored_keys = _secure_storage.load_keys()
    
    # Use stored keys if not in environment
    if not os.getenv("GEMINI_API_KEY") and _stored_keys.get("gemini"):
        os.environ["GEMINI_API_KEY"] = _stored_keys["gemini"]
        print("[AI] Loaded GEMINI_API_KEY from secure storage")
    
    if not os.getenv("GROQ_API_KEY") and _stored_keys.get("groq"):
        os.environ["GROQ_API_KEY"] = _stored_keys["groq"]
        print("[AI] Loaded GROQ_API_KEY from secure storage")
    
    if not os.getenv("POLLINATIONS_API_KEY") and _stored_keys.get("pollinations"):
        os.environ["POLLINATIONS_API_KEY"] = _stored_keys["pollinations"]
        print("[AI] Loaded POLLINATIONS_API_KEY from secure storage")
    
    if not os.getenv("OPENAI_API_KEY") and _stored_keys.get("openai"):
        os.environ["OPENAI_API_KEY"] = _stored_keys["openai"]
        print("[AI] Loaded OPENAI_API_KEY from secure storage")
    
    _HAS_SECURE_STORAGE = True
    
except ImportError:
    print("[AI] Secure storage not available")
    _HAS_SECURE_STORAGE = False


# ============================================================
# SETTINGS SYSTEM
# ============================================================

try:
    from settings import get_setting
except Exception as error:
    print("[Settings Import Error]", error)
    def get_setting(key: str, default: Any = None):
        return default


# ============================================================
# MEMORY SYSTEM
# ============================================================

try:
    from memory import (
        get_memory_text,
        add_memory,
        get_memories,
        clear_memories,
    )
except Exception as error:
    print("[Memory Import Error]", error)
    def get_memory_text():
        return ""
    def add_memory(text: str):
        return None
    def get_memories():
        return []
    def clear_memories():
        return None


# ============================================================
# IMAGE GENERATION
# ============================================================

try:
    from skills.image import generate_image
except Exception as error:
    print("[Image Skill Import Error]", error)
    generate_image = None


# ============================================================
# WEATHER SYSTEM
# ============================================================

try:
    from skills.weather import get_weather_info
except Exception as error:
    print("[Weather Skill Import Error]", error)
    get_weather_info = None


# ============================================================
# REMINDER SYSTEM
# ============================================================

try:
    from skills.reminders import (
        create_timer,
        list_timers,
        cancel_timer,
    )
except Exception as error:
    print("[Reminder Skill Import Error]", error)
    create_timer = None
    list_timers = None
    cancel_timer = None


# ============================================================
# EMAIL SYSTEM
# ============================================================

try:
    from skills.email import (
        get_recent_emails,
        search_emails,
        is_gmail_available,
    )
except Exception as error:
    print("[Email Skill Import Error]", error)
    get_recent_emails = None
    search_emails = None
    is_gmail_available = None


# ============================================================
# POWER SYSTEM
# ============================================================

try:
    from skills.power import (
        shutdown,
        restart,
        sleep,
        hibernate,
        lock,
    )
except Exception as error:
    print("[Power Skill Import Error]", error)
    shutdown = None
    restart = None
    sleep = None
    hibernate = None
    lock = None


# ============================================================
# FILE SYSTEM
# ============================================================

try:
    from skills.files import (
        read_file,
        open_file,
        create_file,
        create_folder,
        list_folder,
        find_files,
        delete_file,
        get_file_info,
    )
except Exception as error:
    print("[Files Skill Import Error]", error)
    read_file = None
    open_file = None
    create_file = None
    create_folder = None
    list_folder = None
    find_files = None
    delete_file = None
    get_file_info = None


# ============================================================
# API CONFIGURATION
# ============================================================

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
POLLINATIONS_KEY = os.getenv("POLLINATIONS_API_KEY", "").strip()
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()


# ============================================================
# DIAGNOSTIC HELPERS
# ============================================================

def _mask_key(key: str) -> str:
    """Mask API key for safe logging (first 6 + last 4 chars)."""
    if not key or len(key) < 10:
        return "***MISSING***" if not key else key[:6] + "****"
    return key[:6] + "..." + key[-4:]

_INTERNET_CACHE: Optional[bool] = None
_INTERNET_CACHE_TIME: float = 0.0
_INTERNET_CACHE_TTL: float = 15.0  # cache for 15 seconds

def _check_internet(force_refresh: bool = False) -> bool:
    """Check if internet is available by attempting to connect to public DNS.
    Results are cached to avoid repeated DNS lookups on every call."""
    global _INTERNET_CACHE, _INTERNET_CACHE_TIME
    now = time.time()
    if not force_refresh and _INTERNET_CACHE is not None and (now - _INTERNET_CACHE_TIME < _INTERNET_CACHE_TTL):
        return _INTERNET_CACHE

    result = False
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        result = True
    except OSError:
        pass
    if not result:
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=3)
            result = True
        except OSError:
            result = False

    _INTERNET_CACHE = result
    _INTERNET_CACHE_TIME = now
    if not result:
        logger.info("Internet connectivity check returned False")
    return result

def _log_ai_status():
    """Log detailed AI provider status for debugging."""
    # Use globals to safely check client status
    gemini_client = globals().get("gemini")
    groq_client = globals().get("groq")
    
    print("\n" + "="*60)
    print("[AI DIAGNOSTICS]")
    print("="*60)
    print(f"  .env loaded: {_ENV_LOADED}")
    print(f"  Secure storage available: {_HAS_SECURE_STORAGE}")
    print(f"  Internet: {_check_internet()}")
    print()
    print(f"  GEMINI_API_KEY:")
    print(f"    Exists: {bool(GEMINI_KEY)}")
    if GEMINI_KEY:
        print(f"    Masked: {_mask_key(GEMINI_KEY)}")
        print(f"    Length: {len(GEMINI_KEY)}")
        print(f"    Format valid: {GEMINI_KEY.startswith('AI') or GEMINI_KEY.startswith('AQ')}")
    print()
    print(f"  GROQ_API_KEY:")
    print(f"    Exists: {bool(GROQ_KEY)}")
    if GROQ_KEY:
        print(f"    Masked: {_mask_key(GROQ_KEY)}")
        print(f"    Length: {len(GROQ_KEY)}")
        print(f"    Format valid: {GROQ_KEY.startswith('gsk_')}")
    print()
    print(f"  POLLINATIONS_API_KEY:")
    print(f"    Exists: {bool(POLLINATIONS_KEY)}")
    print()
    print(f"  OPENWEATHER_API_KEY:")
    print(f"    Exists: {bool(OPENWEATHER_KEY)}")
    print()
    print(f"  OPENAI_API_KEY:")
    print(f"    Exists: {bool(OPENAI_KEY)}")
    print()
    print(f"  gemini client: {'Initialized' if gemini_client else 'None'}")
    print(f"  groq client: {'Initialized' if groq_client else 'None'}")
    print(f"  google.genai module: {'Available' if genai else 'Missing'}")
    print(f"  groq module: {'Available' if Groq else 'Missing'}")
    print("="*60 + "\n")


# ============================================================
# AI CLIENTS
# ============================================================

gemini = None
groq = None

if GEMINI_KEY and genai is not None:
    try:
        gemini = genai.Client(api_key=GEMINI_KEY)
        print(f"[AI] Gemini connected. Key: {_mask_key(GEMINI_KEY)}")
    except Exception as error:
        print("[Gemini Initialization Error]", error)
        traceback.print_exc()

if GROQ_KEY and Groq is not None:
    try:
        groq = Groq(api_key=GROQ_KEY)
        print(f"[AI] Groq connected. Key: {_mask_key(GROQ_KEY)}")
    except Exception as error:
        print("[Groq Initialization Error]", error)
        traceback.print_exc()


# ============================================================
# CONVERSATION HISTORY
# ============================================================

conversation_history: list[dict[str, str]] = []

def get_history_limit():
    try:
        return max(2, int(get_setting("ai.max_conversation_messages", 12)))
    except Exception:
        return 12

def add_to_history(role: str, content: Any):
    if isinstance(content, dict):
        if content.get("type") == "image":
            content = "[An image was generated and displayed to the user.]"
        else:
            content = str(content)
    conversation_history.append({"role": role, "content": str(content)})
    limit = get_history_limit()
    if len(conversation_history) > limit:
        conversation_history[:] = conversation_history[-limit:]

def get_history_text(max_chars: int = 2000):
    """Get conversation history, truncating intelligently to stay within token limits."""
    if not conversation_history:
        return "No previous conversation."
    
    # Build from most recent to oldest, stopping when we exceed max_chars
    lines = []
    current_len = 0
    summary_added = False
    
    for msg in reversed(conversation_history):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if not content:
            continue
        line = f"{role}: {content}"
        line_len = len(line) + 1  # +1 for newline
        
        if current_len + line_len > max_chars:
            if not summary_added and lines:
                lines.insert(0, "[Earlier conversation summarized]")
                summary_added = True
            break
        
        lines.insert(0, line)
        current_len += line_len
    
    return "\n".join(lines) if lines else "No previous conversation."

def clear_conversation():
    conversation_history.clear()

def get_conversation_history():
    return list(conversation_history)


# ============================================================
# TEXT UTILITIES
# ============================================================

def clean_text(text: Any):
    return sanitize_user_text(text)

def normalize_name(text: str):
    text = str(text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s+.#_-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============================================================
# TEMPERATURE
# ============================================================

def get_temperature():
    try:
        value = float(get_setting("ai.temperature", 0.7))
        return max(0.0, min(2.0, value))
    except Exception:
        return 0.7


# ============================================================
# SMART CONTEXT
# ============================================================

def get_context():
    try:
        enabled = get_setting("memory.enabled", True)
        if not enabled:
            return "Long-term memory is disabled."
        try:
            from skills.learning_profile import get_smart_context
            smart = get_smart_context()
            if smart:
                return smart
        except Exception:
            pass
        memory = get_memory_text()
        if not memory:
            return "No saved memories."
        
        # Add context engine info if available
        try:
            from core.context_engine import get_context_engine
            engine = get_context_engine()
            ctx = engine.get_context(["user", "system"])
            user_ctx = ctx.get("user", {})
            sys_ctx = ctx.get("system", {})
            
            # Add relevant dynamic context
            extras = []
            if user_ctx.get("is_weekend"):
                extras.append("User is on a weekend")
            if sys_ctx.get("battery_level") is not None and sys_ctx["battery_level"] < 30:
                extras.append(f"Battery is low ({sys_ctx['battery_level']}%)")
            if sys_ctx.get("cpu_usage", 0) > 80:
                extras.append(f"CPU usage is high ({sys_ctx['cpu_usage']}%)")
            
            if extras:
                memory += "\n\n[Current Context]\n" + "\n".join(f"- {e}" for e in extras)
        except Exception:
            pass
            
        return memory
    except Exception:
        return "No saved memories."


# ============================================================
# SYSTEM PROMPT
# ============================================================

def get_system_prompt():
    style = get_setting("ai.response_style", "friendly")
    length = get_setting("ai.response_length", "balanced")
    length_instruction = {
        "short": "Keep responses concise and direct. 1-2 sentences max.",
        "balanced": "Give useful medium-length responses. 2-4 sentences typically.",
        "detailed": "Give detailed explanations when helpful. Use multiple paragraphs for complex topics.",
    }.get(length, "Give useful medium-length responses.")

    current_personality = get_setting("personality.current_personality", "friendly")
    personalities = get_setting("personality", {})
    personality_settings = personalities.get(current_personality, {})
    if not personality_settings:
        personality_settings = personalities.get("friendly", {})

    emoji_usage = float(personality_settings.get("emoji_usage", 0.7))
    slang_usage = float(personality_settings.get("slang_usage", 0.3))
    proactivity = float(personality_settings.get("proactivity", 0.5))
    formality = float(personality_settings.get("formality", 0.5))
    tone = personality_settings.get("tone", "casual")

    personality_instructions = []
    if tone == "casual":
        personality_instructions.append("- Be very casual, relaxed, and friendly. Use 'bro', 'yo', 'hey' naturally.")
    elif tone == "professional":
        personality_instructions.append("- Be professional, polished, and efficient. Use proper grammar.")
    elif tone == "calm":
        personality_instructions.append("- Be calm, peaceful, and zen-like. Speak slowly and thoughtfully.")
    elif tone == "playful":
        personality_instructions.append("- Be playful, joke often, and use meme references when appropriate.")
    elif tone == "educational":
        personality_instructions.append("- Be a patient tutor: explain concepts clearly, ask check questions, encourage learning.")
    elif tone == "technical":
        personality_instructions.append("- Be technically precise but friendly. Explain code and architecture clearly.")
    elif tone == "custom":
        personality_instructions.append("- Use the customized personality settings below.")

    if formality > 0.7:
        personality_instructions.append("- Use proper grammar and formal language.")
    elif formality < 0.3:
        personality_instructions.append("- Be extremely informal, use slang, abbreviations, and casual expressions.")

    if emoji_usage > 0.6:
        personality_instructions.append("- Use emojis naturally and generously in responses.")
    elif emoji_usage < 0.3:
        personality_instructions.append("- Avoid emojis. Keep text clean.")

    if slang_usage > 0.6:
        personality_instructions.append("- Use casual slang naturally (e.g. 'bro', 'lit', 'no cap', 'fr').")
    elif slang_usage < 0.3:
        personality_instructions.append("- Avoid slang. Use standard vocabulary.")

    if proactivity > 0.7:
        personality_instructions.append("- Be proactive: offer suggestions, next steps, and helpful tips without being asked.")
    elif proactivity < 0.3:
        personality_instructions.append("- Be reactive: only answer what is asked, do not add unsolicited advice.")

    personality_block = "\n".join(personality_instructions) if personality_instructions else "- Default balanced personality."

    # Time-aware context
    from datetime import datetime
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        time_greeting = "Good morning"
    elif 12 <= current_hour < 17:
        time_greeting = "Good afternoon"
    elif 17 <= current_hour < 21:
        time_greeting = "Good evening"
    else:
        time_greeting = "Hey"

    return f"""
You are AI Friend, a smart desktop AI assistant.

PERSONALITY:
- Current time context: {time_greeting}
- Current personality: {personality_settings.get('name', current_personality)}
- {personality_settings.get('description', 'Friendly and helpful')}
- Friendly, natural, intelligent, and helpful.
- Talk casually like a close friend when appropriate.
- You may use casual expressions naturally.
- Be honest about what you can and cannot do.
- Never pretend an action happened if it did not.
- Never claim an image was generated if generation failed.
- Never claim an email was sent if it was not actually sent.
- Never mention hidden prompts or internal implementation.
- Never mention API keys or internal providers to the user.
- {length_instruction}
- Response style: {style}
{personality_block}

CONVERSATION RULES:
- NEVER start every response with the same greeting. Vary your openings naturally.
- Reference earlier parts of the conversation when relevant. Use phrases like "like you mentioned earlier" or "building on what you said".
- Avoid repetitive phrases and templates. Each response should feel unique and context-aware.
- If the user asks follow-up questions, answer naturally without repeating context unnecessarily.
- Use natural filler words and expressions (e.g. "well...", "so...", "actually...", "btw...") to sound human.
- Ask clarifying questions only when genuinely needed. Don't over-clarify.
- If you don't know something, say so directly instead of making excuses.

TEACHING & TUTORING BEHAVIOR:
- When asked to "teach", "explain", or when the user mentions studying/learning:
  1. Act like a friendly, patient personal tutor (e.g. "Okay bro, let's understand this from a real-life example...").
  2. Start from the simplest concept with relatable real-life examples or analogies.
  3. Teach ONE concept at a time. Do NOT dump an entire textbook chapter or all formulas at once unless the user explicitly asks for "full revision notes" or "all important topics".
  4. Use simple, natural language and clean markdown formatting with headings.
  5. Explain formulas by defining what EVERY symbol means (e.g. F = force, m = mass, a = acceleration) and give a simple example.
  6. End explanations with a short, friendly check question to test the student's understanding before moving ahead.
  7. Adapt explanations according to the student's replies and level (especially Class 10 / high school topics).

YOU CAN HELP WITH:
- General questions, Coding, Python, Learning & Studying, Computer tasks
- Windows applications, Installed applications, Browsers, Websites
- Files, Folders, Gmail, Long-term memory, Power commands, AI image generation

USER MEMORY:
{get_context()}

RECENT CONVERSATION:
{get_history_text()}
"""


# ============================================================
# GEMINI
# ============================================================

def ask_gemini(prompt: str):
    if not gemini:
        logger.warning("Gemini client not initialized - check API key")
        return None
    if not _check_internet():
        logger.info("Gemini request skipped: no internet connection")
        return None
    try:
        response = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"temperature": get_temperature()},
            request_options={"timeout": 30},
        )
        answer = getattr(response, "text", "")
        return clean_text(answer)
    except Exception as error:
        error_str = str(error).lower()
        if "api key" in error_str or "authentication" in error_str or "401" in error_str or "403" in error_str:
            error_category = "authentication"
        elif "quota" in error_str or "rate limit" in error_str or "429" in error_str:
            error_category = "quota"
        elif "timeout" in error_str or "timed out" in error_str:
            error_category = "timeout"
        elif "network" in error_str or "connection" in error_str:
            error_category = "network"
        else:
            error_category = "unknown"
        logger.warning(
            "Gemini request failed",
            extra={"provider": "gemini", "model": GEMINI_MODEL, "error_type": type(error).__name__, "category": error_category},
        )
        logger.debug("Gemini error detail: %s", str(error))
        return None


# ============================================================
# GROQ
# ============================================================

def ask_groq(prompt: str):
    if not groq:
        logger.warning("Groq client not initialized - check API key")
        return None
    if not _check_internet():
        logger.info("Groq request skipped: no internet connection")
        return None
    try:
        response = groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=get_temperature(),
            timeout=30,
        )
        answer = response.choices[0].message.content
        return clean_text(answer)
    except Exception as error:
        error_str = str(error).lower()
        if "api key" in error_str or "authentication" in error_str or "401" in error_str or "403" in error_str:
            error_category = "authentication"
        elif "quota" in error_str or "rate limit" in error_str or "429" in error_str:
            error_category = "quota"
        elif "timeout" in error_str or "timed out" in error_str:
            error_category = "timeout"
        elif "network" in error_str or "connection" in error_str:
            error_category = "network"
        else:
            error_category = "unknown"
        logger.warning(
            "Groq request failed",
            extra={"provider": "groq", "model": GROQ_MODEL, "error_type": type(error).__name__, "category": error_category},
        )
        logger.debug("Groq error detail: %s", str(error))
        return None


# ============================================================
# AI PROVIDER ROUTER
# ============================================================

def ask_ai(prompt: str):
    """Route prompt to the configured AI provider with exponential backoff and fallback."""
    primary = get_setting("ai.primary_provider", "gemini")
    fallback = get_setting("ai.fallback_provider", "groq")
    automatic_fallback = get_setting("ai.automatic_fallback", True)

    providers = {"gemini": ask_gemini, "groq": ask_groq}

    logger.info(
        "AI request routed",
        extra={"primary": primary, "fallback": fallback, "auto_fallback": automatic_fallback},
    )

    # Build provider chain: primary first, fallback second
    provider_chain = []
    first_provider = providers.get(primary)
    if first_provider:
        provider_chain.append(primary)
    if automatic_fallback and fallback != primary:
        fb_provider = providers.get(fallback)
        if fb_provider:
            provider_chain.append(fallback)

    if not provider_chain:
        if not GEMINI_KEY and not GROQ_KEY:
            return (
                "Brooo, I could not connect to my AI right now.\n\n"
                "No API keys configured.\n\n"
                "Please add a Gemini or Groq API key in Settings."
            )
        return "Brooo, I could not connect to my AI right now."


    backoff_base = 1.0

    for idx, provider_name in enumerate(provider_chain):
        provider_func = providers[provider_name]
        max_attempts = 2 if idx == 0 else 1

        for attempt in range(1, max_attempts + 1):
            answer = provider_func(prompt)
            if answer:
                logger.info("Provider succeeded", extra={"provider": provider_name, "attempt": attempt})
                return answer

            if attempt < max_attempts:
                backoff = backoff_base * (2 ** (attempt - 1))
                logger.debug("Retrying %s (attempt %d/%d) after %.1fs", provider_name, attempt + 1, max_attempts, backoff)
                time.sleep(backoff)

        logger.warning("Provider exhausted retries", extra={"provider": provider_name, "attempts": max_attempts})

    if not _check_internet(force_refresh=True):
        return "Brooo, I couldn't connect to my AI right now. Internet connection unavailable."
    if not GEMINI_KEY and not GROQ_KEY:
        return "Brooo, I couldn't connect to my AI right now. No API keys configured."

    return (
        "Brooo, I could not connect to my AI right now.\n\n"
        "All AI providers failed. This could be due to:\n"
        "API quota, invalid keys, or network issues."
    )


# ====
# ============================================================
# REQUEST CLASSIFICATION
# ============================================================

def classify_request(text: str) -> dict[str, Any]:
    if not text:
        return {"intent": "unknown", "confidence": 0.0}
    lower = str(text).strip().lower()
    
    # Image generation
    if is_image_request(lower):
        return {"intent": "image", "confidence": 0.98}
    
    # Weather
    if any(phrase in lower for phrase in ["weather", "temperature", "rain", "humidity", "wind", "forecast", "umbrella", "sunrise", "sunset"]):
        return {"intent": "weather", "confidence": 0.95}
    
    # Timer
    if any(phrase in lower for phrase in ["timer", "remind", "reminder", "alarm", "countdown"]):
        return {"intent": "timer", "confidence": 0.94}
    
    # Memory
    if any(phrase in lower for phrase in ["remember", "memory", "forget", "memories"]):
        return {"intent": "memory", "confidence": 0.92}
    
    # Email
    if any(phrase in lower for phrase in ["gmail", "email", "mail"]):
        return {"intent": "email", "confidence": 0.9}
    
    # Power
    if any(phrase in lower for phrase in ["shutdown", "restart", "sleep", "hibernate", "lock"]):
        return {"intent": "power", "confidence": 0.9}
    
    # Files
    if any(phrase in lower for phrase in ["open ", "launch ", "start ", "run ", "find file", "create file", "create folder", "search file"]):
        return {"intent": "files", "confidence": 0.86}
    
    # Teaching/learning
    if any(phrase in lower for phrase in [
        "teach me", "teach ", "explain ", "explain to me", "help me understand",
        "help me study", "i am studying", "iam studying", "studying ", "study ", "how does", "what is", "what are"
    ]):
        return {"intent": "teach", "confidence": 0.9}
    
    # Coding help
    if any(phrase in lower for phrase in ["code", "program", "function", "debug", "error in", "python", "javascript"]):
        return {"intent": "coding", "confidence": 0.85}
    
    # System info
    if any(phrase in lower for phrase in ["system info", "system status", "cpu usage", "ram usage", "battery status"]):
        return {"intent": "system_info", "confidence": 0.9}
    
    # Questions (high confidence for question marks)
    if "?" in text:
        return {"intent": "question", "confidence": 0.8}
    
    return {"intent": "conversation", "confidence": 0.6}


def _analyze_user_input(text: str) -> dict[str, Any]:
    """
    Internal analysis of user input to guide response strategy.
    This remains internal and is not exposed to the user.
    """
    if not text:
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "emotion": "neutral",
            "urgency": "normal",
            "needs_clarification": False,
            "multi_step": False,
            "memory_relevant": False,
            "history_relevant": False,
        }
    
    lower = str(text).strip().lower()
    classification = classify_request(text)
    
    # Detect emotion
    emotion = "neutral"
    if any(word in lower for word in ["please", "thanks", "thank you", "appreciate"]):
        emotion = "polite"
    elif any(word in lower for word in ["help", "stuck", "confused", "don't understand", "frustrated", "annoyed", "angry"]):
        emotion = "frustrated"
    elif any(word in lower for word in ["excited", "awesome", "amazing", "great", "wonderful", "happy"]):
        emotion = "excited"
    elif any(word in lower for word in ["sad", "depressed", "lonely", "tired", "exhausted", "stressed"]):
        emotion = "upset"
    elif any(word in lower for word in ["urgent", "asap", "quickly", "right now", "immediately", "emergency"]):
        emotion = "urgent"
    
    # Detect urgency
    urgency = "normal"
    if any(word in lower for word in ["urgent", "asap", "quickly", "right now", "immediately", "emergency"]):
        urgency = "high"
    elif any(word in lower for word in ["whenever", "no rush", "take your time", "later"]):
        urgency = "low"
    
    # Detect if clarification needed
    needs_clarification = False
    if classification["confidence"] < 0.7 and classification["intent"] not in ["conversation", "question"]:
        needs_clarification = True
    
    # Detect multi-step requests
    multi_step = False
    step_indicators = ["then", "after that", "and then", "next", "followed by", "afterwards"]
    if any(indicator in lower for indicator in step_indicators):
        multi_step = True
    # Also check for multiple commands separated by commas or "and"
    if text.count(",") >= 2 or (", " in text and " and " in text):
        multi_step = True
    
    # Check if memory is relevant
    memory_relevant = False
    if classification["intent"] in ["memory", "teach", "question"]:
        memory_relevant = True
    if any(phrase in lower for phrase in ["remember", "forgot", "mentioned", "said before", "told me"]):
        memory_relevant = True
    
    # Check if history is relevant
    history_relevant = False
    if classification["intent"] == "conversation":
        history_relevant = True
    if any(phrase in lower for phrase in ["earlier", "before", "previous", "like i said", "as i mentioned"]):
        history_relevant = True
    
    return {
        "intent": classification["intent"],
        "confidence": classification["confidence"],
        "emotion": emotion,
        "urgency": urgency,
        "needs_clarification": needs_clarification,
        "multi_step": multi_step,
        "memory_relevant": memory_relevant,
        "history_relevant": history_relevant,
    }


# ============================================================
# TEACHING INTENT DETECTION
# ============================================================

def is_teaching_request(text: str) -> bool:
    if not text:
        return False
    lower = str(text).strip().lower()
    teaching_triggers = [
        "teach me", "teach ", "explain ", "explain to me", "help me understand",
        "help me study", "i am studying", "iam studying", "studying ", "study ",
        "help me learn", "how does", "what is", "what are",
        "class 10", "class 9", "class 11", "class 12", "grade 10", "chapter", "lesson",
    ]
    return any(trigger in lower for trigger in teaching_triggers)

def is_full_notes_request(text: str) -> bool:
    if not text:
        return False
    lower = str(text).strip().lower()
    notes_triggers = [
        "full revision notes", "revision notes", "all important topics", "all topics",
        "full notes", "complete notes", "everything at once", "give me all",
        "entire chapter", "full chapter", "summary of all", "complete chapter",
    ]
    return any(trigger in lower for trigger in notes_triggers)


# ============================================================
# WEATHER COMMANDS
# ============================================================

def handle_weather(text: str):
    if not get_weather_info:
        return None
    classification = classify_request(text)
    if classification.get("intent") != "weather":
        return None
    location = None
    match = re.search(r"(?:in|for|at)\s+([A-Za-z ,.-]+)", text, re.IGNORECASE)
    if match:
        location = match.group(1).strip(" ,.-")
    else:
        location = get_setting("weather.default_location", "")
    if not location:
        return "Tell me the city or place you want the weather for."
    try:
        return get_weather_info(location, text)
    except Exception as error:
        print("[Weather Error]", error)
        return "I couldn't fetch weather information right now."


# ============================================================
# TIMER / REMINDER COMMANDS
# ============================================================

def handle_timers(text: str):
    if not create_timer:
        return None
    classification = classify_request(text)
    if classification.get("intent") != "timer":
        return None
    lower = str(text).lower()
    if any(phrase in lower for phrase in ["show my timers", "list my timers", "active timers"]):
        try:
            timers = list_timers()
            if not timers:
                return "You don't have any active timers."
            return "Active timers:\n" + "\n".join(timers)
        except Exception as error:
            print("[Timer List Error]", error)
            return "I couldn't list your timers."
    if any(phrase in lower for phrase in ["cancel timer", "cancel my timer", "stop timer"]):
        try:
            return cancel_timer(text) or "I couldn't cancel that timer."
        except Exception as error:
            print("[Timer Cancel Error]", error)
            return "I couldn't cancel that timer."
    duration_minutes = None
    if re.search(r"(\d+)\s*(m|min|mins|minute|minutes)", lower):
        duration_minutes = int(re.search(r"(\d+)\s*(m|min|mins|minute|minutes)", lower).group(1))
    elif re.search(r"(\d+)\s*(h|hr|hrs|hour|hours)", lower):
        duration_minutes = int(re.search(r"(\d+)\s*(h|hr|hrs|hour|hours)", lower).group(1)) * 60
    elif re.search(r"(\d+)\s*(s|sec|secs|second|seconds)", lower):
        duration_minutes = max(1, int(re.search(r"(\d+)\s*(s|sec|secs|second|seconds)", lower).group(1)) // 60)
    if duration_minutes is None:
        return "Tell me how long the timer should be, for example: 10 minutes."
    reminder_text = text
    if re.search(r"(?:timer|remind|reminder)\s+(?:me\s+)?(?:to\s+)?(.+)", lower):
        reminder_text = re.search(r"(?:timer|remind|reminder)\s+(?:me\s+)?(?:to\s+)?(.+)", lower).group(1).strip()
    else:
        reminder_text = "Timer"
    try:
        return create_timer(reminder_text, duration_minutes)
    except Exception as error:
        print("[Timer Create Error]", error)
        return "I couldn't create that timer."


# ============================================================
# MEMORY COMMANDS
# ============================================================

def handle_memory(text: str):
    if not get_setting("memory.enabled", True):
        return None
    lower = text.lower()
    show_phrases = [
        "what do you remember", "show my memories", "show memories",
        "my memories", "what memories do you have", "list my memories",
    ]
    if any(phrase in lower for phrase in show_phrases):
        try:
            memories = get_memories()
            if not memories:
                return "Brooo, I don't have any saved memories yet 🧠"
            return "Here is what I remember:\n\n" + "\n".join(f"• {memory}" for memory in memories)
        except Exception as error:
            print("[Memory Read Error]", error)
            return "I couldn't read your memories right now."
    clear_phrases = [
        "forget everything", "clear all memories", "delete all memories",
        "forget all memories", "erase all memories",
    ]
    if any(phrase in lower for phrase in clear_phrases):
        try:
            clear_memories()
            return "Done brooo, I cleared all saved memories 🧠"
        except Exception as error:
            print("[Memory Clear Error]", error)
            return "I couldn't clear your memories."
    match = re.search(r"(?:remember that|remember this|save this|don't forget that|remember\s+(.+))", text, re.IGNORECASE)
    if match:
        memory = match.group(1).strip() if match.group(1) else text
        memory = re.sub(r"^(?:remember that|remember this|save this|don't forget that)\s*", "", memory, flags=re.IGNORECASE).strip()
        if not memory:
            return "Brooo, what should I remember? 🤔"
        try:
            add_memory(memory)
            return f"Got it brooo, I'll remember: {memory} 🧠"
        except Exception as error:
            print("[Memory Save Error]", error)
            return "I couldn't save that memory."
    return None


# ============================================================
# IMAGE GENERATION
# ============================================================

def is_image_request(text: str):
    patterns = [
        r"\bgenerate\s+(?:an?\s+)?image\b", r"\bgenerate\s+(?:an?\s+)?photo\b",
        r"\bgenerate\s+(?:an?\s+)?picture\b", r"\bcreate\s+(?:an?\s+)?image\b",
        r"\bcreate\s+(?:an?\s+)?photo\b", r"\bcreate\s+(?:an?\s+)?picture\b",
        r"\bmake\s+(?:me\s+)?(?:an?\s+)?image\b", r"\bmake\s+(?:me\s+)?(?:an?\s+)?photo\b",
        r"\bmake\s+(?:me\s+)?(?:an?\s+)?picture\b", r"\bdraw\s+(?:an?\s+)?image\b",
        r"\bcreate\s+art\b", r"\bgenerate\s+art\b",
    ]
    lower = text.lower()
    return any(re.search(pattern, lower) for pattern in patterns)

def extract_image_prompt(text: str):
    patterns = [
        r"generate\s+(?:an?\s+)?image", r"generate\s+(?:an?\s+)?photo",
        r"generate\s+(?:an?\s+)?picture", r"create\s+(?:an?\s+)?image",
        r"create\s+(?:an?\s+)?photo", r"create\s+(?:an?\s+)?picture",
        r"make\s+(?:me\s+)?(?:an?\s+)?image", r"make\s+(?:me\s+)?(?:an?\s+)?photo",
        r"make\s+(?:me\s+)?(?:an?\s+)?picture", r"draw\s+(?:an?\s+)?image",
        r"create\s+art", r"generate\s+art",
    ]
    prompt = text
    for pattern in patterns:
        prompt = re.sub(pattern, "", prompt, flags=re.IGNORECASE)
    return prompt.strip(" :,-")

def normalize_image_result(result: Any):
    if not result:
        return None
    if isinstance(result, dict):
        image_path = result.get("path") or result.get("image_path") or result.get("file") or result.get("url")
        if image_path:
            return {
                "type": "image",
                "path": os.path.abspath(str(image_path)),
                "caption": result.get("caption", "Here is your generated image 🎨"),
            }
        return None
    if isinstance(result, str):
        image_path = result.strip()
        if os.path.exists(image_path):
            return {
                "type": "image",
                "path": os.path.abspath(image_path),
                "caption": "Here is your generated image 🎨",
            }
    return None

def handle_image_generation(text: str):
    if not generate_image:
        return None
    if not is_image_request(text):
        return None
    prompt = extract_image_prompt(text)
    if not prompt:
        return "Brooo, tell me what image you want me to generate 🎨"
    try:
        print("[AI] Generating image:", prompt)
        result = generate_image(prompt)
        normalized = normalize_image_result(result)
        if normalized:
            return normalized
        if isinstance(result, dict):
            return result
        return "Brooo, the image generator did not return a valid image 😭"
    except Exception as error:
        print("[Image Generation Error]", error)
        return "Brooo, image generation failed 😭"


# ============================================================
# WEBSITE SYSTEM
# ============================================================

WEBSITE_ALIASES = {
    "google": "https://www.google.com",
    "google search": "https://www.google.com",
    "bing": "https://www.bing.com",
    "duckduckgo": "https://duckduckgo.com",
    "yahoo": "https://www.yahoo.com",
    "gmail": "https://mail.google.com",
    "google mail": "https://mail.google.com",
    "google drive": "https://drive.google.com",
    "google docs": "https://docs.google.com",
    "google sheets": "https://sheets.google.com",
    "google slides": "https://slides.google.com",
    "google classroom": "https://classroom.google.com",
    "google maps": "https://maps.google.com",
    "chatgpt": "https://chatgpt.com",
    "openai": "https://openai.com",
    "gemini": "https://gemini.google.com",
    "claude": "https://claude.ai",
    "perplexity": "https://www.perplexity.ai",
    "deepseek": "https://chat.deepseek.com",
    "youtube": "https://www.youtube.com",
    "youtube music": "https://music.youtube.com",
    "netflix": "https://www.netflix.com",
    "prime video": "https://www.primevideo.com",
    "disney plus": "https://www.disneyplus.com",
    "twitch": "https://www.twitch.tv",
    "spotify": "https://open.spotify.com",
    "soundcloud": "https://soundcloud.com",
    "crunchyroll": "https://www.crunchyroll.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "tiktok": "https://www.tiktok.com",
    "reddit": "https://www.reddit.com",
    "pinterest": "https://www.pinterest.com",
    "linkedin": "https://www.linkedin.com",
    "threads": "https://www.threads.net",
    "github": "https://github.com",
    "gitlab": "https://gitlab.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "npm": "https://www.npmjs.com",
    "pypi": "https://pypi.org",
    "replit": "https://replit.com",
    "codepen": "https://codepen.io",
    "vercel": "https://vercel.com",
    "netlify": "https://www.netlify.com",
    "amazon": "https://www.amazon.com",
    "daraz": "https://www.daraz.com.np",
    "ebay": "https://www.ebay.com",
    "aliexpress": "https://www.aliexpress.com",
    "walmart": "https://www.walmart.com",
    "discord": "https://discord.com",
    "telegram": "https://web.telegram.org",
    "whatsapp": "https://web.whatsapp.com",
    "zoom": "https://zoom.us",
    "microsoft teams": "https://teams.microsoft.com",
    "wikipedia": "https://www.wikipedia.org",
    "khan academy": "https://www.khanacademy.org",
    "coursera": "https://www.coursera.org",
    "edx": "https://www.edx.org",
    "w3schools": "https://www.w3schools.com",
    "geeksforgeeks": "https://www.geeksforgeeks.org",
    "roblox": "https://www.roblox.com",
    "minecraft": "https://www.minecraft.net",
    "steam": "https://store.steampowered.com",
    "epic games": "https://store.epicgames.com",
    "valorant": "https://playvalorant.com",
    "riot games": "https://www.riotgames.com",
}


# ============================================================
# COMMAND ROUTER
# ============================================================

class CommandRouter:
    _APP_ALIASES = {
        "vs code", "vscode", "visual studio code",
        "chrome", "google chrome",
        "edge", "microsoft edge",
        "firefox",
        "calculator",
        "file explorer", "explorer",
        "settings", "windows settings",
        "notepad",
        "word", "microsoft word",
        "excel", "microsoft excel",
        "powerpoint", "microsoft powerpoint",
        "terminal", "cmd", "powershell", "command prompt",
        "task manager",
        "control panel",
        "gmail",
        "youtube",
        "netflix",
        "spotify",
        "discord",
        "slack",
        "zoom",
        "teams", "microsoft teams",
        "outlook", "microsoft outlook",
        "whatsapp",
        "telegram",
        "steam",
        "epic games",
        "battle.net",
        "origin",
        "uplay",
        "xbox",
        "playstation",
        "cursor",
        "windsurf",
        "github desktop",
        "git bash",
        "jupyter",
        "colab",
        "notion",
        "onenote",
        "evernote",
        "obsidian",
        "anki",
        "duolingo",
        "coursera",
        "udemy",
        "khan academy",
    }

    @classmethod
    def classify(cls, text: str) -> Optional[dict]:
        if not text:
            return None
        lower = text.lower().strip()
        match = re.search(r"^(?:open|launch|start|run|execute)\s+(?:my\s+|the\s+)?(.+?)(?:\s+for\s+me)?$", lower)
        if match:
            target = match.group(1).strip()
            target = re.sub(r"\b(application|app|program|software)\b", "", target).strip()
            if target:
                if target in WEBSITE_ALIASES:
                    return {"intent": "open_website", "target": target, "confidence": 1.0}
                return {"intent": "open_app", "target": target, "confidence": 1.0}
        if lower.startswith(("open file ", "open the file ", "open a file ")):
            target = re.sub(r"^(?:open\s+(?:the\s+|a\s+)?file\s+)", "", lower).strip()
            if target:
                return {"intent": "open_file", "target": target, "confidence": 0.9}
        if lower.startswith(("open folder ", "open the folder ", "open directory ", "show folder ")):
            target = re.sub(r"^(?:open\s+(?:the\s+)?(?:folder|directory)\s+)", "", lower).strip()
            if target:
                return {"intent": "open_folder", "target": target, "confidence": 0.9}
        if lower.startswith("show folder "):
            target = lower.replace("show folder ", "").strip()
            if target:
                return {"intent": "open_folder", "target": target, "confidence": 0.9}
        if any(k in lower for k in ["search the web for", "search for", "google ", "look up ", "find info about", "look up"]):
            target = lower
            for prefix in ["search the web for", "search for", "google ", "look up ", "find info about"]:
                target = target.replace(prefix, "").strip()
            if target:
                return {"intent": "search_web", "target": target, "confidence": 0.95}
        power_map = {
            "shutdown": ["shutdown computer", "shut down computer", "turn off computer", "turn off my pc", "shutdown my pc"],
            "restart": ["restart computer", "reboot computer", "restart my pc", "reboot my pc"],
            "sleep": ["put computer to sleep", "sleep computer", "sleep my pc"],
            "hibernate": ["hibernate computer", "hibernate my pc"],
            "lock": ["lock computer", "lock my pc", "lock my computer"],
        }
        for action, phrases in power_map.items():
            if any(phrase in lower for phrase in phrases):
                return {"intent": "power_action", "target": action, "confidence": 1.0}
        if any(k in lower for k in ["send email", "send an email", "compose email", "write email", "new email"]):
            return {"intent": "email_action", "target": "send", "confidence": 0.9}
        if any(k in lower for k in ["check my email", "read my email", "show my email", "recent emails", "my inbox"]):
            return {"intent": "gmail_action", "target": "read", "confidence": 0.9}
        if any(k in lower for k in ["search email", "find email", "email from"]):
            return {"intent": "gmail_action", "target": "search", "confidence": 0.9}
        if any(k in lower for k in [
            "teach me", "teach ", "explain ", "explain to me", "help me understand",
            "help me study", "i am studying", "iam studying", "studying ", "study ",
            "help me learn", "how does", "what is", "what are",
            "class 10", "class 9", "class 11", "class 12", "grade 10", "chapter", "lesson",
        ]):
            return {"intent": "teach", "target": text, "confidence": 0.9}
        if any(k in lower for k in ["weather", "temperature", "forecast", "rain", "sunny", "cold", "hot outside"]):
            return {"intent": "weather", "target": text, "confidence": 0.8}
        if any(k in lower for k in ["timer", "remind me", "reminder", "set a timer", "set timer"]):
            return {"intent": "timer", "target": text, "confidence": 0.8}
        if any(k in lower for k in ["remember this", "save this", "add to memory", "store this", "note that"]):
            return {"intent": "memory", "target": text, "confidence": 0.85}
        if any(k in lower for k in ["generate image", "create image", "draw ", "make image", "image of"]):
            return {"intent": "image_gen", "target": text, "confidence": 0.9}
        if any(k in lower for k in ["system info", "system status", "cpu usage", "ram usage", "battery status", "take screenshot"]):
            return {"intent": "system_info", "target": text, "confidence": 0.9}
        return None


def execute_routed_action(route: dict, original_message: str):
    intent = route.get("intent")
    target = route.get("target", "")
    try:
        if intent == "open_app":
            result = open_application(target)
            return f"🚀 Opening {target.title()}, brooo." if result else f"😕 I couldn't find '{target}' on your computer."
        elif intent == "open_website":
            result = open_website(target)
            return f"🌐 Opening {target}, brooo." if result else f"😕 I couldn't open '{target}'."
        elif intent == "open_file":
            if open_file:
                result = open_file(target)
                return result or "😕 I had trouble opening that file."
            return "📄 File operations aren't available right now."
        elif intent == "open_folder":
            if list_folder:
                folder_path = target
                if not os.path.isabs(folder_path):
                    folder_path = os.path.join(str(Path.home() / "Documents"), folder_path)
                if os.path.isdir(folder_path):
                    _open_file_explorer(folder_path)
                    return f"📁 Opening folder: {folder_path}"
                result = list_folder(folder_path)
                return result or "😕 I couldn't find that folder."
            return "📁 Folder operations aren't available right now."
        elif intent == "search_web":
            result = search_google(target)
            return f"🔍 Searched for '{target}'." if result else f"😕 Search failed for '{target}'."
        elif intent == "power_action":
            if handle_power:
                result = handle_power(original_message)
                if result:
                    return result
            return f"⚡ Power action '{target}' isn't available right now."
        elif intent == "email_action":
            if not is_gmail_available:
                return "Gmail isn't connected yet. You can connect it anytime from Settings."
            if handle_email:
                result = handle_email(original_message)
                if result:
                    return result
            return "📧 Email isn't available right now."
        elif intent == "gmail_action":
            if not is_gmail_available:
                return "Gmail isn't connected yet. You can connect it anytime from Settings."
            if target == "read":
                try:
                    emails = get_recent_emails()
                    if not emails:
                        return "📭 No recent emails found."
                    lines = ["Recent emails:"]
                    for e in emails[:5]:
                        lines.append(f"• {e.get('subject', 'No Subject')} from {e.get('from', 'Unknown')}")
                    return "\n".join(lines)
                except Exception as e:
                    return f"😕 Couldn't read emails: {e}"
            return "📧 Gmail action isn't available right now."
        elif intent == "teach":
            return None
        elif intent == "weather":
            if handle_weather:
                result = handle_weather(original_message)
                if result:
                    return result
            return None
        elif intent == "timer":
            if handle_timers:
                result = handle_timers(original_message)
                if result:
                    return result
            return None
        elif intent == "memory":
            if handle_memory:
                result = handle_memory(original_message)
                if result:
                    return result
            return None
        elif intent == "image_gen":
            if handle_image_generation:
                result = handle_image_generation(original_message)
                if result:
                    return result
            return None
        elif intent == "system_info":
            if handle_system:
                result = handle_system(original_message)
                if result:
                    return result
            return None
    except Exception as e:
        return f"😕 Something went wrong while executing that command: {e}"
    return None


# ============================================================
# APPLICATION DISCOVERY
# ============================================================

APP_ALIASES = {
    "chrome": "chrome", "google chrome": "chrome",
    "edge": "msedge", "microsoft edge": "msedge",
    "firefox": "firefox", "opera": "opera", "opera gx": "opera",
    "brave": "brave", "vivaldi": "vivaldi",
    "vs code": "code", "vscode": "code", "visual studio code": "code",
    "visual studio": "devenv", "pycharm": "pycharm", "intellij": "idea",
    "android studio": "studio64", "sublime text": "sublime_text", "notepad++": "notepad++",
    "steam": "steam", "epic games": "epicgameslauncher", "epic games launcher": "epicgameslauncher",
    "tlauncher": "tlauncher", "tl launcher": "tlauncher", "tl": "tlauncher",
    "minecraft": "minecraft", "roblox": "roblox", "valorant": "riotclient",
    "riot client": "riotclient", "battle.net": "battle.net", "battle net": "battle.net",
    "ubisoft connect": "upc",
    "discord": "discord", "telegram": "telegram", "whatsapp": "whatsapp",
    "zoom": "zoom", "skype": "skype", "teams": "teams", "microsoft teams": "teams",
    "spotify": "spotify", "vlc": "vlc", "obs": "obs64", "obs studio": "obs64",
    "photoshop": "photoshop", "adobe photoshop": "photoshop",
    "premiere pro": "premiere", "after effects": "afterfx",
    "blender": "blender", "figma": "figma", "canva": "canva",
    "calculator": "calc.exe", "calc": "calc.exe",
    "notepad": "notepad.exe", "paint": "mspaint.exe",
    "file explorer": "explorer.exe", "explorer": "explorer.exe", "files": "explorer.exe",
    "command prompt": "cmd.exe", "cmd": "cmd.exe",
    "powershell": "powershell.exe", "terminal": "wt.exe", "windows terminal": "wt.exe",
    "task manager": "taskmgr.exe", "control panel": "control.exe", "snipping tool": "snippingtool.exe",
}

START_MENU_LOCATIONS = [
    Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
]

PROGRAM_LOCATIONS = [
    Path(os.environ.get("PROGRAMFILES", "")),
    Path(os.environ.get("PROGRAMFILES(X86)", "")),
    Path(os.environ.get("LOCALAPPDATA", "")),
]

APP_CACHE: dict[str, str] = {}

def clear_app_cache():
    APP_CACHE.clear()

def get_app_cache():
    return dict(APP_CACHE)

def find_start_menu_app(app_name: str):
    app_name = normalize_name(app_name)
    best_match = None
    best_score = 0
    for location in START_MENU_LOCATIONS:
        if not location.exists():
            continue
        try:
            for item in location.rglob("*"):
                if not item.is_file():
                    continue
                item_name = normalize_name(item.stem)
                if not item_name:
                    continue
                if item_name == app_name:
                    return item
                score = 0
                if app_name in item_name:
                    score += 80
                if item_name in app_name:
                    score += 60
                for word in app_name.split():
                    if word in item_name:
                        score += 10
                if score > best_score:
                    best_score = score
                    best_match = item
        except Exception as error:
            print("[Start Menu Search Error]", error)
    return best_match

def find_installed_application(app_name: str):
    normalized = normalize_name(app_name)
    if normalized in APP_CACHE:
        return APP_CACHE[normalized]
    alias = APP_ALIASES.get(normalized)
    if alias:
        direct = shutil.which(alias)
        if direct:
            APP_CACHE[normalized] = direct
            return direct
    shortcut = find_start_menu_app(normalized)
    if shortcut:
        path = str(shortcut)
        APP_CACHE[normalized] = path
        return path
    best_match = None
    best_score = 0
    for location in PROGRAM_LOCATIONS:
        if not location.exists():
            continue
        try:
            for folder in location.iterdir():
                folder_name = normalize_name(folder.name)
                score = 0
                if normalized == folder_name:
                    score += 100
                if normalized in folder_name:
                    score += 70
                if folder_name in normalized:
                    score += 40
                if score > best_score:
                    best_score = score
                    best_match = folder
        except Exception:
            continue
    if best_match:
        path = str(best_match)
        APP_CACHE[normalized] = path
        return path
    return None

def open_application(app_name: str):
    normalized = normalize_name(app_name)
    if normalized in {"settings", "windows settings"}:
        try:
            if IS_WINDOWS:
                subprocess.Popen(["cmd", "/c", "start", "", "ms-settings:"], shell=False)
            else:
                return False
            return True
        except Exception as error:
            print("[Settings Launch Error]", error)
            return False
    application = find_installed_application(normalized)
    if not application:
        return False
    try:
        if os.path.exists(application):
            _open_file_default(application)
        else:
            subprocess.Popen(application, shell=False)
        return True
    except Exception as error:
        print("[Application Launch Error]", error)
        return False


# ============================================================
# APPLICATION COMMAND HANDLER
# ============================================================

def launch_app(text: str):
    lower = text.lower().strip()
    match = re.search(r"^(?:open|launch|start|run|execute)\s+(?:my\s+|the\s+)?(.+?)(?:\s+for\s+me)?$", lower)
    if not match:
        return None
    app_name = match.group(1).strip()
    app_name = re.sub(r"\b(application|app|program|software)\b", "", app_name).strip()
    if not app_name:
        return None
    if app_name in WEBSITE_ALIASES:
        return None
    if app_name in {"youtube", "google", "gmail", "github", "chatgpt", "instagram", "facebook", "reddit", "netflix", "tiktok", "wikipedia", "amazon", "daraz"}:
        return None
    if open_application(app_name):
        return f"🚀 Opening {app_name.title()}, brooo."
    return f"😕 I couldn't find '{app_name}' on your computer."


# ============================================================
# POWER COMMANDS
# ============================================================

_POWER_FUNCTIONS = {
    "shutdown": shutdown,
    "restart": restart,
    "sleep": sleep,
    "hibernate": hibernate,
    "lock": lock,
}

def handle_power(text: str):
    lower = text.lower()
    actions = {
        "shutdown": ["shutdown computer", "shut down computer", "turn off computer", "turn off my pc", "shutdown my pc"],
        "restart": ["restart computer", "reboot computer", "restart my pc", "reboot my pc"],
        "sleep": ["put computer to sleep", "sleep computer", "sleep my pc"],
        "hibernate": ["hibernate computer", "hibernate my pc"],
        "lock": ["lock computer", "lock my pc", "lock my computer"],
    }
    for action, phrases in actions.items():
        if not any(phrase in lower for phrase in phrases):
            continue
        if not get_setting(f"power.allow_{action}", True):
            return f"⚠️ {action.title()} is disabled in Settings."
        if get_setting(f"power.confirm_{action}", True):
            return f"⚠️ I can {action} your computer.\n\nPlease confirm this action."
        power_func = _POWER_FUNCTIONS.get(action)
        if not power_func:
            return f"The {action} function is unavailable."
        try:
            success, message = power_func()
            if success:
                return f"Done brooo. {action.title()} completed."
            return f"I couldn't perform {action}.\n\n{message}"
        except Exception as error:
            return f"I couldn't perform {action}.\n\n{error}"
    return None


# ============================================================
# GMAIL
# ============================================================

def handle_email(text: str):
    lower = text.lower()
    if not is_gmail_available:
        return "Gmail isn't connected yet. You can connect it anytime from Settings."
    if any(phrase in lower for phrase in ["check my emails", "read my emails", "show my emails", "check my gmail", "read my gmail"]):
        if not get_recent_emails:
            return "Gmail skill is not available."
        try:
            count = get_setting("gmail.recent_email_count", 5)
            emails = get_recent_emails(count)
            if not emails:
                return "Brooo, you don't have any recent emails 📧"
            return "\n\n".join(f"📧 {email}" for email in emails)
        except Exception as error:
            print("[Gmail Error]", error)
            return "I couldn't access Gmail right now 😭"
    if any(phrase in lower for phrase in ["search my emails", "search emails", "search my gmail"]):
        if not search_emails:
            return "Gmail search is unavailable."
        query = re.sub(r"search (my )?(emails|gmail)", "", text, flags=re.IGNORECASE).strip()
        if not query:
            return "Brooo, what should I search for in your emails? 📧"
        try:
            results = search_emails(query)
            if not results:
                return "No matching emails found."
            return "\n\n".join(map(str, results))
        except Exception as error:
            print("[Email Search Error]", error)
            return "I couldn't search your emails."
    return None


# ============================================================
# FILE AND FOLDER COMMANDS
# ============================================================

def open_folder(folder: str):
    try:
        if os.path.exists(folder):
            _open_file_explorer(folder)
            return True
    except Exception as error:
        print("[Folder Error]", error)
    return False

def handle_files(text: str):
    lower = text.lower()
    if any(phrase in lower for phrase in ["open documents folder", "open my documents", "open documents"]):
        folder = os.path.expanduser("~/Documents")
        folder = get_setting("files.default_folder", folder)
        if open_folder(folder):
            return "📁 Opening your Documents folder, brooo."
        return "I couldn't open your Documents folder."
    if any(phrase in lower for phrase in ["open downloads folder", "open my downloads", "open downloads"]):
        folder = os.path.expanduser("~/Downloads")
        if open_folder(folder):
            return "📁 Opening your Downloads folder, brooo."
        return "I couldn't open your Downloads folder."
    if any(phrase in lower for phrase in ["open desktop", "open my desktop"]):
        folder = os.path.expanduser("~/Desktop")
        if open_folder(folder):
            return "🖥️ Opening your Desktop, brooo."
        return "I couldn't open your Desktop."
    if any(phrase in lower for phrase in ["open home folder", "open home directory"]):
        folder = os.path.expanduser("~")
        if open_folder(folder):
            return "🏠 Opening your home folder, brooo."
    return None


# ============================================================
# MISSION COMMANDS
# ============================================================

def handle_missions(text: str):
    """Handle mission-related commands."""
    try:
        from mission_tracker import get_mission_tracker
        from mission_planner import get_mission_planner
        tracker = get_mission_tracker()
        planner = get_mission_planner()
    except ImportError:
        return None

    lower = text.lower().strip()

    # Create mission
    if any(phrase in lower for phrase in [
        "i want to", "i wanna", "i need to", "i'm trying to", "create mission",
        "new mission", "start mission", "begin mission", "plan to", "planning to"
    ]):
        # Use AI planner to create mission
        mission = planner.plan_mission(text)
        if mission:
            # Format response
            response = f"🚀 Mission Created!\n\n"
            response += f"**{mission.title}**\n"
            response += f"Category: {mission.category.title()}\n"
            response += f"Progress: 0%\n\n"
            response += f"Milestones:\n"
            for i, ms in enumerate(mission.milestones[:5], 1):
                response += f"{i}. {ms.title}\n"
            if len(mission.milestones) > 5:
                response += f"... and {len(mission.milestones) - 5} more\n"
            response += f"\nType 'show mission {mission.id}' for details."
            return response
        return None

    # Show missions
    if any(phrase in lower for phrase in [
        "show my missions", "list missions", "my missions", "active missions",
        "what missions", "show missions"
    ]):
        missions = tracker.get_active_missions()
        if not missions:
            return "You don't have any active missions. Say 'I want to...' to create one!"
        
        response = "📋 Your Active Missions:\n\n"
        for mission in missions[:5]:
            progress = int(mission.calculate_progress() * 100)
            response += f"• **{mission.title}** ({progress}%)\n"
        if len(missions) > 5:
            response += f"\n... and {len(missions) - 5} more"
        return response

    # Show specific mission
    match = re.search(r"(?:show|get|view)\s+mission\s+(?:called\s+)?(.+)", lower)
    if match:
        title = match.group(1).strip()
        mission = tracker.get_mission_by_title(title)
        if not mission:
            return f"I couldn't find a mission called '{title}'."
        
        summary = tracker.get_mission_summary(mission.id)
        if not summary:
            return "Mission not found."
        
        response = f"🚀 **{summary['title']}**\n\n"
        response += f"Status: {summary['status'].title()}\n"
        response += f"Progress: {int(summary['progress'] * 100)}%\n"
        response += f"Tasks: {summary['completed_tasks']}/{summary['total_tasks']}\n"
        response += f"Milestones: {summary['completed_milestones']}/{summary['total_milestones']}\n"
        
        if summary['current_task']:
            response += f"\nCurrent task: {summary['current_task']}\n"
            response += f"Next: {summary['next_action']['task_title'] if summary['next_action'] else 'None'}"
        
        return response

    # Complete task
    if "complete" in lower and "task" in lower:
        # Extract task info - simplified
        return "To complete a task, use the mission UI or say 'mark task [mission] [task] as done'"

    # Get next action
    if any(phrase in lower for phrase in [
        "what should i do", "next step", "next action", "what now",
        "continue mission", "work on mission"
    ]):
        missions = tracker.get_active_missions()
        if not missions:
            return "No active missions. Create one by saying 'I want to...'"
        
        # Get highest priority mission
        mission = max(missions, key=lambda m: m.priority)
        action = tracker.get_next_action(mission.id)
        if action:
            return f"🎯 **Next Step: {action['mission_title']}**\n\n{action['task_title']}\n\nEstimated: {action['estimated_minutes']} minutes\n\nType 'start' to begin."
        else:
            return f"Mission '{mission.title}' is complete! 🎉"

    # Export / final product
    if any(phrase in lower for phrase in [
        "give me the final product", "export this project", "package my website",
        "download my completed project", "finish the project", "get my files",
        "export mission", "final product", "download project", "get the files"
    ]):
        try:
            from mission_exporter import get_mission_exporter
            exporter = get_mission_exporter()
            
            # Get active missions
            missions = tracker.get_active_missions()
            if not missions:
                return "No active missions to export. Complete a mission first!"
            
            # Use highest priority mission
            mission = max(missions, key=lambda m: m.priority)
            
            # Check readiness
            readiness = exporter.is_project_ready_for_export(mission.id)
            if not readiness.get("ready"):
                return f"Can't export yet: {readiness.get('reason', 'Project not ready')}"
            
            # Get files
            project_files = exporter.get_project_files(mission.id)
            if not project_files:
                return "This mission doesn't have any files to export yet."
            
            # Export
            result = exporter.export_mission_project(
                mission_id=mission.id,
                project_files=project_files,
            )
            
            if result.get("success"):
                size_kb = result.get("size_bytes", 0) / 1024
                return (
                    f"📦 **Project Exported!**\n\n"
                    f"Mission: {mission.title}\n"
                    f"Files: {result.get('file_count', 0)}\n"
                    f"Size: {size_kb:.1f} KB\n"
                    f"Location: {result.get('path', 'Unknown')}\n\n"
                    f"Your project is ready!"
                )
            else:
                return f"Export failed: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Export error: {e}"

    return None


# ============================================================
# SYSTEM HARDWARE HANDLER
# ============================================================
# ============================================================
# SYSTEM HARDWARE HANDLER
# ============================================================

def handle_system(message: str) -> Optional[str]:
    if not message:
        return None
    lower = str(message).strip().lower()
    if any(k in lower for k in ["how much ram", "ram usage", "ram info", "memory info", "available ram"]):
        try:
            from skills.system import get_ram_info
            return get_ram_info()
        except Exception as e:
            return f"Brooo, couldn't fetch RAM info 😭\n{e}"
    if any(k in lower for k in ["cpu usage", "cpu info", "processor info", "cpu status"]):
        try:
            from skills.system import get_cpu_info, get_cpu_usage
            return f"{get_cpu_info()}\n{get_cpu_usage()}"
        except Exception as e:
            return f"Brooo, couldn't fetch CPU info 😭\n{e}"
    if any(k in lower for k in ["gpu info", "graphics card", "gpu status", "graphics info"]):
        try:
            from skills.system import get_gpu_info
            return get_gpu_info()
        except Exception as e:
            return f"Brooo, couldn't fetch GPU info 😭\n{e}"
    if any(k in lower for k in ["storage info", "disk space", "hard drive", "storage status", "disk info", "how much storage"]):
        try:
            from skills.system import get_storage_info
            return get_storage_info()
        except Exception as e:
            return f"Brooo, couldn't fetch Storage info 😭\n{e}"
    if any(k in lower for k in ["battery status", "battery level", "battery info", "how much battery"]):
        try:
            from skills.system import get_battery_status
            return get_battery_status()
        except Exception as e:
            return f"Brooo, couldn't fetch Battery info 😭\n{e}"
    if any(k in lower for k in ["full system status", "system status", "full system info", "system specs"]):
        try:
            from skills.system import get_full_system_status
            return get_full_system_status()
        except Exception as e:
            return f"Brooo, couldn't fetch System status 😭\n{e}"
    if any(k in lower for k in ["current time", "what time is it", "what's the time", "today's date", "what is the date"]):
        try:
            from skills.system import get_current_time
            return get_current_time()
        except Exception as e:
            return f"Brooo, couldn't fetch time 😭\n{e}"
    if any(k in lower for k in ["take screenshot", "take a screenshot", "capture screen"]):
        try:
            from skills.system import take_screenshot
            return take_screenshot()
        except Exception as e:
            return f"Brooo, couldn't take screenshot 😭\n{e}"
    if any(k in lower for k in ["lock computer", "lock my pc", "lock screen", "lock laptop"]):
        try:
            from skills.system import lock_computer
            return lock_computer()
        except Exception as e:
            return f"Brooo, couldn't lock PC 😭\n{e}"
    return None


# ============================================================
# MAIN COMMAND PROCESSOR
# ============================================================

def process_message(user_message: str, attachments: Optional[list[dict]] = None):
    user_message = clean_text(user_message)
    if not user_message and not attachments:
        return "Brooo, say something 😄"

    if attachments:
        image_attachments = [a for a in attachments if a.get('type') == 'image']
        if image_attachments:
            try:
                return _handle_image_understanding(user_message, image_attachments)
            except Exception as e:
                print("[IMAGE UNDERSTANDING ERROR]", e)
                return "Brooo 😭 I had trouble understanding that image. Can you try again?"

    # ============================================================
    # INTERNAL ANALYSIS PIPELINE
    # ============================================================
    analysis = _analyze_user_input(user_message)
    
    # ============================================================
    # GREETING SHORT-CIRCUIT (only for obvious greetings)
    # ============================================================
    lower_msg = user_message.lower().strip()
    simple_greetings = ["hi", "hello", "hey", "yo", "sup", "what's up", "whats up"]
    if lower_msg in simple_greetings and analysis["intent"] == "conversation":
        from datetime import datetime
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            greeting = "Good morning"
        elif 12 <= current_hour < 17:
            greeting = "Good afternoon"
        elif 17 <= current_hour < 21:
            greeting = "Good evening"
        else:
            greeting = "Hey"
        
        responses = [
            f"{greeting}! What's on your mind?",
            f"{greeting}! How can I help you today?",
            f"Hey there! {greeting}! What's up?",
            f"{greeting}! Ready to help with whatever you need.",
        ]
        import random
        response = random.choice(responses)
        add_to_history("user", user_message)
        add_to_history("assistant", response)
        return response

    add_to_history("user", user_message)

    # ============================================================
    # COMMAND ROUTING (high confidence only)
    # ============================================================
    if analysis["confidence"] >= 0.9:
        try:
            route = CommandRouter.classify(user_message)
            if route and route.get("intent") != "teach":
                routed = execute_routed_action(route, user_message)
                if routed:
                    add_to_history("assistant", routed)
                    return routed
        except Exception as error:
            print("[CommandRouter Error]", error)

    # ============================================================
    # SPECIALIZED HANDLERS
    # ============================================================
    if analysis["intent"] in ["weather", "timer", "memory", "image", "system_info", "email", "power", "files"]:
        handlers = [
            handle_weather, handle_timers, handle_memory, handle_image_generation,
            handle_system, handle_email, handle_power, handle_files,
        ]
        # Map intent to handler
        intent_to_handler = {
            "weather": handle_weather,
            "timer": handle_timers,
            "memory": handle_memory,
            "image": handle_image_generation,
            "system_info": handle_system,
            "email": handle_email,
            "power": handle_power,
            "files": handle_files,
        }
        handler = intent_to_handler.get(analysis["intent"])
        if handler:
            try:
                result = handler(user_message)
                if result:
                    add_to_history("assistant", result)
                    return result
            except Exception as error:
                print(f"[{handler.__name__} Error]", error)

    # ============================================================
    # MULTI-STEP REQUEST HANDLING
    # ============================================================
    if analysis["multi_step"]:
        # For multi-step requests, acknowledge and break down
        if analysis["urgency"] == "high":
            return "Got it, this has multiple steps. Let me handle this efficiently for you. One moment..."

    # ============================================================
    # MEMORY RELEVANCE CHECK
    # ============================================================
    memory_context = ""
    if analysis["memory_relevant"]:
        try:
            from memory import get_memories
            memories = get_memories()
            if memories:
                # Check if any memory is relevant to current topic
                relevant_memories = []
                for mem in memories:
                    mem_text = str(mem) if not isinstance(mem, str) else mem
                    if any(word in mem_text.lower() for word in lower_msg.split()):
                        relevant_memories.append(mem_text)
                if relevant_memories:
                    memory_context = f"Relevant memories found: {'; '.join(relevant_memories[:3])}\n"
        except Exception:
            pass

    # ============================================================
    # CONTEXT DETERMINATION
    # ============================================================
    mode_ctx = ""
    try:
        from skills.modes import detect_mode, get_mode_instruction
        mode = detect_mode(user_message)
        mode_ctx = get_mode_instruction(mode)
    except Exception as err:
        print("[MODE DETECTION ERROR]", err)

    teaching_ctx = ""
    try:
        from skills.study import detect_study_mode, get_study_mode_prompt_instructions
        study_mode = detect_study_mode(user_message)
        if study_mode:
            teaching_ctx = get_study_mode_prompt_instructions(study_mode, user_message)
    except Exception as err:
        print("[STUDY SKILL ERROR]", err)

    if not teaching_ctx and is_teaching_request(user_message):
        if is_full_notes_request(user_message):
            teaching_ctx = (
                "\n[TEACHING MODE: FULL REVISION NOTES]\n"
                "The student explicitly requested complete notes or all topics at once.\n"
                "You must provide a comprehensive, well-structured revision document:\n"
                "1. Start with a brief overview of the topic.\n"
                "2. Break content into clear sections with bold headings.\n"
                "3. Explain every formula by defining each symbol and showing a simple worked example.\n"
                "4. Include key definitions, diagram descriptions, and important facts.\n"
                "5. Add top exam tips and common mistakes to avoid at the end.\n"
                "Make it easy to read and study from, like a textbook summary.\n"
            )
        else:
            teaching_ctx = (
                "\n[TEACHING MODE: ENHANCED TUTOR]\n"
                "You are now acting as an intelligent, patient tutor. Follow this exact flow:\n"
                "1. FIRST: Restate the student's question in your own words to confirm understanding.\n"
                "2. CONCEPT BREAKDOWN: Split the topic into 2-4 digestible parts. Explain each part clearly.\n"
                "3. STEP-BY-STEP: If applicable, walk through the solution or process in numbered steps with reasoning.\n"
                "4. EXAMPLES: Provide ONE simple example and ONE practical real-world example.\n"
                "5. COMMON PITFALLS: Warn about 1-2 typical mistakes students make with this topic.\n"
                "6. NATURAL FOLLOW-UP: End with ONE supportive follow-up question to check understanding.\n"
                "Use simple, clear language. Be encouraging but precise. Never skip steps.\n"
                "Keep a natural, warm tone - like a smart friend helping out, not a textbook.\n"
            )

    try:
        from skills.learning_profile import track_topic, track_interaction
        if is_teaching_request(user_message) or teaching_ctx:
            topic = user_message[:100]
            track_topic(topic)
        track_interaction(user_message, "")
    except Exception:
        pass

    # ============================================================
    # SMART CONTEXT BUILDING
    # ============================================================
    history_text = get_history_text()
    context_text = get_context()
    
    # Summarize history if too long
    if len(history_text) > 2000:
        lines = history_text.split('\n')
        lines = lines[-10:]  # Keep last 10 messages
        history_text = '\n'.join(lines)
        history_text = "[Earlier conversation summarized]\n" + history_text

    # Build emotion-aware prompt additions
    emotion_guidance = ""
    if analysis["emotion"] == "frustrated":
        emotion_guidance = "\n[EMOTION: User seems frustrated. Be extra patient, empathetic, and reassuring. Acknowledge their frustration before diving into solutions.]"
    elif analysis["emotion"] == "excited":
        emotion_guidance = "\n[EMOTION: User is excited. Match their energy and enthusiasm!]"
    elif analysis["emotion"] == "upset":
        emotion_guidance = "\n[EMOTION: User seems upset. Be supportive, empathetic, and gentle. Offer encouragement.]"
    elif analysis["emotion"] == "polite":
        emotion_guidance = "\n[EMOTION: User is polite. Be warm and appreciative in your response.]"
    elif analysis["emotion"] == "urgent":
        emotion_guidance = "\n[URGENCY: High. Be direct, concise, and action-oriented. Skip small talk.]"

    # Urgency guidance
    urgency_guidance = ""
    if analysis["urgency"] == "high":
        urgency_guidance = "\n[URGENT REQUEST: Respond quickly and efficiently. Prioritize action over explanation.]"
    elif analysis["urgency"] == "low":
        urgency_guidance = "\n[NO RUSH: Take your time. Provide a thorough, thoughtful response.]"

    # Multi-step guidance
    multi_step_guidance = ""
    if analysis["multi_step"]:
        multi_step_guidance = "\n[MULTI-STEP REQUEST: Break this into clear steps. Confirm understanding before proceeding.]"

    # Clarification guidance
    clarification_guidance = ""
    if analysis["needs_clarification"]:
        clarification_guidance = "\n[NEEDS CLARIFICATION: Ask ONE concise clarifying question. Do not guess.]"

    prompt = f"""
{get_system_prompt()}
{mode_ctx}
{teaching_ctx}
{memory_context}

CONVERSATION CONTEXT (use this to give personalized, context-aware responses):
{history_text}

LONG-TERM MEMORY (important facts about the user):
{context_text}

CURRENT USER MESSAGE:
{user_message}

INTERNAL ANALYSIS (use this to guide your response style):
- Detected emotion: {analysis['emotion']}
- Urgency level: {analysis['urgency']}
- Intent confidence: {analysis['confidence']}
- Multi-step request: {analysis['multi_step']}
- Needs clarification: {analysis['needs_clarification']}

RESPONSE GUIDELINES:
{emotion_guidance}
{urgency_guidance}
{multi_step_guidance}
{clarification_guidance}
- Respond naturally as a best friend would.
- Reference earlier conversation points when relevant (e.g. "like you said before...").
- Don't repeat information already discussed unless asked.
- Be concise for simple questions, detailed for complex topics.
- Show personality and empathy.
- Match the user's energy and tone.
- Before responding, mentally verify: Does this answer their question? Is it accurate? Does it sound natural?
"""

    answer = ask_ai(prompt)
    if answer:
        answer = clean_ai_reply(answer)
        add_to_history("assistant", answer)
        return answer

    return "Brooo, I couldn't generate a response right now 😭"


# ============================================================
# COMPATIBILITY FUNCTIONS
# ============================================================

def get_ai_response(message: str):
    return process_message(message)

def chat(message: str):
    return process_message(message)

def reset_ai():
    clear_conversation()

# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "process_message",
    "get_ai_response",
    "chat",
    "reset_ai",
    "clear_conversation",
    "get_conversation_history",
    "clear_app_cache",
    "get_app_cache",
]