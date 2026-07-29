"""
================================================================
AVORA GLOBAL HOTKEY SYSTEM
================================================================
Registers a global hotkey (Ctrl+Alt+F12) that triggers the
panic kill switch to instantly stop all automation.

Uses pynput for cross-platform keyboard listening.
Falls back gracefully if pynput is not installed.
================================================================
"""

from __future__ import annotations

import threading
import time
from typing import Optional

from avora_safety import trigger_panic, log_activity

# ============================================================
# OPTIONAL IMPORTS
# ============================================================

try:
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
    keyboard = None


# ============================================================
# CONFIGURATION
# ============================================================

# Default panic hotkey: Ctrl+Alt+F12
PANIC_HOTKEY = {
    "ctrl": True,
    "alt": True,
    "key": "f12",
}

_listener: Optional[threading.Thread] = None
_keyboard_listener = None
_running = False


# ============================================================
# HOTKEY LISTENER THREAD
# ============================================================

def _hotkey_listener_thread() -> None:
    """Background thread that listens for the panic hotkey."""
    global _keyboard_listener

    if not HAS_PYNPUT:
        return

    try:
        # Use pynput's GlobalHotKeys for reliable hotkey detection
        hotkey = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+<f12>': trigger_panic,
        })
        _keyboard_listener = hotkey
        hotkey.start()
        hotkey.join()
    except Exception as e:
        print(f"[AVORA HOTKEY] Listener error: {e}")


# ============================================================
# PUBLIC API
# ============================================================

def start_hotkey_listener() -> bool:
    """Start the global hotkey listener in a background thread."""
    global _listener, _running

    if _running:
        return True

    if not HAS_PYNPUT:
        print("[AVORA HOTKEY] pynput not installed. Install with: pip install pynput")
        print("[AVORA HOTKEY] Panic hotkey disabled. Use trigger_panic() programmatically.")
        return False

    _running = True
    _listener = threading.Thread(
        target=_hotkey_listener_thread,
        daemon=True,
        name="AvoraHotkeyListener",
    )
    _listener.start()
    log_activity("HOTKEY", "Global panic hotkey listener started (Ctrl+Alt+F12)")
    print("[AVORA HOTKEY] Panic hotkey active: Ctrl+Alt+F12")
    return True


def stop_hotkey_listener() -> None:
    """Stop the global hotkey listener."""
    global _keyboard_listener, _listener, _running

    _running = False

    if _keyboard_listener is not None:
        try:
            _keyboard_listener.stop()
        except Exception:
            pass
        _keyboard_listener = None

    _listener = None
    log_activity("HOTKEY", "Global panic hotkey listener stopped")


def is_listener_running() -> bool:
    """Check if the hotkey listener is active."""
    return _running


# ============================================================
# INITIALIZATION
# ============================================================

def initialize() -> None:
    """Initialize the hotkey system."""
    from settings import get_setting
    if get_setting("safety.enable_panic_hotkey", True):
        start_hotkey_listener()
    else:
        print("[AVORA HOTKEY] Panic hotkey disabled in settings.")


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "start_hotkey_listener",
    "stop_hotkey_listener",
    "is_listener_running",
    "initialize",
]
