"""
============================================================
VOICE SESSION
============================================================
Continuous live voice conversation mode for Avora.

States:
- IDLE
- LISTENING
- USER_SPEAKING
- THINKING
- AVORA_SPEAKING
- INTERRUPTED
- STOPPING

Integrates with existing voice.py for TTS/STT and with
main.py for the chat pipeline.
"""

from __future__ import annotations

import threading
import time
from typing import Optional, Callable

try:
    import numpy as np
except ImportError:
    np = None

try:
    from voice import (
        speak,
        stop_speaking,
        is_speaking,
        listen_start,
        listen_stop,
        is_recording,
    )
except Exception:
    speak = None
    stop_speaking = None
    is_speaking = lambda: False
    listen_start = lambda: False
    listen_stop = lambda: None
    is_recording = lambda: False


class VoiceSessionState:
    IDLE = "idle"
    LISTENING = "listening"
    USER_SPEAKING = "user_speaking"
    THINKING = "thinking"
    AVORA_SPEAKING = "avora_speaking"
    INTERRUPTED = "interrupted"
    STOPPING = "stopping"


class VoiceSession:
    """Manages a continuous voice conversation session."""

    def __init__(
        self,
        on_state_changed: Optional[Callable[[str], None]] = None,
        on_user_text: Optional[Callable[[str], None]] = None,
        on_ai_text: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self._state = VoiceSessionState.IDLE
        self._on_state_changed = on_state_changed
        self._on_user_text = on_user_text
        self._on_ai_text = on_ai_text
        self._on_error = on_error

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._session_thread: Optional[threading.Thread] = None

        # VAD settings
        self._silence_timeout = 1.5
        self._speech_threshold = 500
        self._min_speech_duration = 0.5

        # Barge-in monitoring
        self._barge_in_thread: Optional[threading.Thread] = None
        self._barge_in_stop = threading.Event()

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    def start(self) -> bool:
        """Start continuous voice conversation mode."""
        with self._lock:
            if self._state != VoiceSessionState.IDLE:
                return False
            self._stop_event.clear()
            self._state = VoiceSessionState.LISTENING

        self._notify_state()
        self._session_thread = threading.Thread(target=self._session_loop, daemon=True)
        self._session_thread.start()
        return True

    def stop(self) -> None:
        """Stop voice conversation mode."""
        self._stop_event.set()
        self._barge_in_stop.set()

        try:
            stop_speaking()
        except Exception:
            pass

        try:
            listen_stop()
        except Exception:
            pass

        with self._lock:
            self._state = VoiceSessionState.IDLE

        self._notify_state()

    def interrupt(self) -> None:
        """Interrupt Avora's speech and return to listening."""
        with self._lock:
            if self._state == VoiceSessionState.AVORA_SPEAKING:
                self._state = VoiceSessionState.INTERRUPTED

        try:
            stop_speaking()
        except Exception:
            pass

        self._notify_state()

    def _session_loop(self) -> None:
        """Main voice session loop."""
        while not self._stop_event.is_set():
            try:
                if self._state == VoiceSessionState.LISTENING:
                    self._listen_phase()
                elif self._state == VoiceSessionState.THINKING:
                    self._think_phase()
                elif self._state == VoiceSessionState.AVORA_SPEAKING:
                    self._speak_phase()
                elif self._state == VoiceSessionState.INTERRUPTED:
                    self._interrupted_phase()
                else:
                    time.sleep(0.1)
            except Exception as error:
                if self._on_error:
                    try:
                        self._on_error(str(error))
                    except Exception:
                        pass
                time.sleep(0.5)

    def _listen_phase(self) -> None:
        """Listen for user speech."""
        with self._lock:
            if self._state != VoiceSessionState.LISTENING:
                return

        success = listen_start()
        if not success:
            self._notify_error("Could not start microphone. Check permissions.")
            return

        try:
            while not self._stop_event.is_set():
                with self._lock:
                    if self._state != VoiceSessionState.LISTENING:
                        listen_stop()
                        return

                if is_recording():
                    time.sleep(0.1)
                    continue

                text = listen_stop()
                if text and text.strip():
                    with self._lock:
                        self._state = VoiceSessionState.USER_SPEAKING
                    self._notify_state()
                    if self._on_user_text:
                        try:
                            self._on_user_text(text.strip())
                        except Exception as error:
                            self._notify_error(str(error))
                    with self._lock:
                        self._state = VoiceSessionState.THINKING
                    self._notify_state()
                    return

                time.sleep(0.1)
        except Exception as error:
            self._notify_error(str(error))
            listen_stop()

    def _think_phase(self) -> None:
        """Wait for AI response via external callback."""
        time.sleep(0.1)

    def _speak_phase(self) -> None:
        """Speak AI response and start barge-in monitor."""
        if speak is None:
            with self._lock:
                self._state = VoiceSessionState.LISTENING
            self._notify_state()
            return

        self._barge_in_stop.clear()
        self._barge_in_thread = threading.Thread(target=self._barge_in_loop, daemon=True)
        self._barge_in_thread.start()

        try:
            speak(
                "",
                on_start=lambda: None,
                on_finish=self._on_speak_finish,
            )
        except Exception:
            pass

        self._barge_in_stop.set()
        if self._barge_in_thread is not None:
            self._barge_in_thread.join(timeout=1.0)

        with self._lock:
            if self._state == VoiceSessionState.AVORA_SPEAKING:
                self._state = VoiceSessionState.LISTENING
            self._notify_state()

    def _on_speak_finish(self) -> None:
        with self._lock:
            if self._state == VoiceSessionState.AVORA_SPEAKING:
                self._state = VoiceSessionState.LISTENING
                self._notify_state()

    def _interrupted_phase(self) -> None:
        with self._lock:
            self._state = VoiceSessionState.LISTENING
            self._notify_state()

    def _barge_in_loop(self) -> None:
        """Monitor microphone during speech for user interruption."""
        while not self._barge_in_stop.is_set():
            try:
                if is_recording():
                    time.sleep(0.05)
                    continue

                success = listen_start()
                if not success:
                    time.sleep(0.1)
                    continue

                samples = 0
                while not self._barge_in_stop.is_set() and samples < 50:
                    if is_recording():
                        time.sleep(0.1)
                        samples += 1
                        continue
                    break

                if not is_recording():
                    listen_stop()
                    time.sleep(0.1)
                    continue

                time.sleep(0.3)

                if not is_recording():
                    listen_stop()
                    time.sleep(0.1)
                    continue

                with self._lock:
                    if self._state == VoiceSessionState.AVORA_SPEAKING:
                        self._state = VoiceSessionState.INTERRUPTED
                        self._notify_state()
                return

            except Exception:
                time.sleep(0.1)

    def set_thinking(self) -> None:
        with self._lock:
            if self._state in (
                VoiceSessionState.USER_SPEAKING,
                VoiceSessionState.THINKING,
            ):
                self._state = VoiceSessionState.THINKING
                self._notify_state()

    def set_speaking(self) -> None:
        with self._lock:
            if self._state == VoiceSessionState.THINKING:
                self._state = VoiceSessionState.AVORA_SPEAKING
                self._notify_state()

    def _notify_state(self) -> None:
        if self._on_state_changed:
            try:
                self._on_state_changed(self.state)
            except Exception:
                pass

    def _notify_error(self, message: str) -> None:
        if self._on_error:
            try:
                self._on_error(message)
            except Exception:
                pass
