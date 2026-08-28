#!/usr/bin/env python3
"""
AVORA Desktop - Production Entrypoint (RESTORED)

Restored to the original cinematic AVORA UI (avora backend/main.py).
The previous minimal placeholder UI (787 lines, idle/0% progress-only) has
been replaced. This wrapper delegates to the last known-good rich UI
without duplicating code, preserving all backend fixes.

Original UI features restored:
 - 1200x800 dark cinematic window, neural background, cursor glow
 - Sidebar with Logo, New Chat, Voice, Settings, ChatSidebar
 - Header with AVORA + status label (Ready/Thinking/Error)
 - Chat area with message bubbles, markdown renderer, image display
 - ChatComposer (Enter sends, Shift+Enter newline, auto-resize 46-160px)
 - Animated Character (Character QWidget) with mood/emotion, speech bubble
 - Companion Intelligence + BehaviorController + ActivityMonitor
 - Screen Awareness, mission tracker, hotkey/clipboard/automation
 - Voice toggle, attach file, mic button
 - Settings persistence, theme listener, apply_styles/generate_qss
 - Safe shutdown, QThread workers, panic timer

Backend preservation: ai_logic Gemini/Groq routing, vision_engine,
screen_awareness, companion_intelligence, memory — unchanged.
"""

import os
import sys
import importlib.util
import pathlib

# --- Prevent duplicate instances (same lock as before) ---
import socket as _sock
_lock_socket = _sock.socket(_sock.AF_UNIX if hasattr(_sock, 'AF_UNIX') else _sock.AF_INET, _sock.SOCK_STREAM)
try:
    if hasattr(_sock, 'AF_UNIX'):
        _lock_socket.bind('\0avora_desktop_lock')
    else:
        _lock_socket.bind(('127.0.0.1', 47231))
except OSError:
    print("AVORA Desktop is already running.")
    sys.exit(0)

# --- Resolve backend location ---
ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKEND = ROOT / "avora backend"

# Ensure both ROOT and BACKEND are on sys.path for `from character import ...` etc.
for p in (str(ROOT), str(BACKEND)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Also ensure BACKEND is inserted first for intra-backend imports
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Change working directory to backend so relative resource paths (ICON_PATH, etc.) resolve
try:
    os.chdir(str(BACKEND))
except Exception:
    pass

# --- Load and execute the rich UI main ---
backend_main_path = BACKEND / "main.py"
if not backend_main_path.is_file():
    print(f"[AVORA] Backend main not found at {backend_main_path}")
    sys.exit(1)

spec = importlib.util.spec_from_file_location("avora_backend_main", str(backend_main_path))
if spec is None or spec.loader is None:
    print("[AVORA] Failed to create spec for backend main")
    sys.exit(1)

avora_backend_main = importlib.util.module_from_spec(spec)
# Keep lock reference alive on the app module after load
sys.modules["avora_backend_main"] = avora_backend_main
spec.loader.exec_module(avora_backend_main)

# Expose backend MainWindow/Character for external imports/tests if needed
try:
    MainWindow = avora_backend_main.MainWindow
    Character = avora_backend_main.Character
    ChatComposer = avora_backend_main.ChatComposer
except Exception:
    pass

def main():
    """Delegate to the restored rich UI main()."""
    # Keep lock alive for the lifetime of the app
    # (avora_backend_main.main() will create QApplication and hold lock via this process)
    # Store on sys.modules so GC doesn't collect
    import sys as _sys
    _sys._avora_lock_socket = _lock_socket
    return avora_backend_main.main()

if __name__ == "__main__":
    sys.exit(main())
