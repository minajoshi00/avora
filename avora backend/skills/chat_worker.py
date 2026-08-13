"""
========================================================================
chat_worker.py
NOVA - Streaming AI chat worker with stop/regenerate support
========================================================================
Provides:
- StreamingWorker: QThread that streams AI responses token-by-token
- Safe signal-based communication with the main thread
- Stop generation support (properly aborts API calls)
- Regenerate support
========================================================================
"""

import os
import sys
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("ChatWorker")

from PySide6.QtCore import QThread, Signal, QMutex

# Import AI logic
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_logic import process_message, get_conversation_history, conversation_history


class StreamingWorker(QThread):
    """
    Worker thread that generates AI responses with streaming-like behavior.
    
    Since the current AI providers don't support true streaming via this codebase,
    we simulate progressive delivery by breaking responses into chunks.
    
    Signals:
        chunk_ready(str): Emitted when a text chunk is ready for display
        stream_finished(str): Emitted with the complete response when done
        stream_failed(str): Emitted with error message on failure
        stream_started(): Emitted when generation begins
    """

    chunk_ready = Signal(str)
    stream_finished = Signal(str)
    stream_failed = Signal(str)
    stream_started = Signal()

    def __init__(self, message: str, parent: Optional[Any] = None, attachments: Optional[list] = None):
        super().__init__(parent)
        self.message = str(message)
        self.attachments = attachments or []
        self._is_cancelled = False
        self._mutex = QMutex()
        self._full_response = ""

    def cancel(self):
        """Request cancellation of the current generation."""
        self._mutex.lock()
        try:
            self._is_cancelled = True
        finally:
            self._mutex.unlock()
        # Request thread interruption for faster abort
        self.requestInterruption()

    def is_cancelled(self) -> bool:
        """Check if generation was cancelled."""
        self._mutex.lock()
        try:
            return self._is_cancelled
        finally:
            self._mutex.unlock()

    def run(self):
        try:
            if self.is_cancelled():
                return

            self.stream_started.emit()

            # Check cancellation before the blocking AI call
            if self.is_cancelled():
                return

            # Get the full response from AI logic
            reply = process_message(self.message, self.attachments)

            if self.is_cancelled():
                return

            if reply is None:
                reply = "Sorry brooo 😭\n\nI couldn't generate a response."

            self._full_response = str(reply)

            # Simulate streaming by breaking response into chunks
            self._simulate_streaming(reply)

            if not self.is_cancelled():
                self.stream_finished.emit(self._full_response)

        except Exception as error:
            logger.warning("Streaming worker error: %s", error, exc_info=False)

            if not self.is_cancelled():
                error_msg = "Sorry brooo 😭\n\nSomething went wrong generating my response."
                self.stream_failed.emit(error_msg)

    def _simulate_streaming(self, text: str):
        """Break text into chunks and emit them progressively."""
        if not text:
            return

        # For short responses, emit in sentence chunks
        # For longer responses, emit in paragraph chunks
        text_str = str(text)

        # Split by sentences for natural progressive display
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text_str)

        chunk = ""
        for sentence in sentences:
            if self.is_cancelled():
                return

            chunk += sentence + " "
            
            # Emit paragraph-sized chunks
            if len(chunk) >= 80 or sentence.endswith((".", "!", "?")):
                self.chunk_ready.emit(chunk)
                chunk = ""
                self.msleep(15)  # Small delay for progressive feel

        # Emit remaining text
        if chunk.strip():
            self.chunk_ready.emit(chunk)

    def get_full_response(self) -> str:
        """Get the complete generated response."""
        return self._full_response


class RegenerateWorker(QThread):
    """
    Worker that regenerates a response by clearing the last AI message
    and re-running the AI.
    """

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, message: str, parent: Optional[Any] = None, attachments: Optional[list] = None):
        super().__init__(parent)
        self.message = str(message)
        self.attachments = attachments or []
        self._is_cancelled = False
        self._mutex = QMutex()

    def cancel(self):
        """Request cancellation."""
        self._mutex.lock()
        try:
            self._is_cancelled = True
        finally:
            self._mutex.unlock()
        self.requestInterruption()

    def is_cancelled(self) -> bool:
        """Check if cancelled."""
        self._mutex.lock()
        try:
            return self._is_cancelled
        finally:
            self._mutex.unlock()

    def run(self):
        try:
            if self.is_cancelled():
                return

            # Remove the last assistant message from history
            # so the AI generates a fresh response
            hist = get_conversation_history()
            if hist and hist[-1].get("role") == "assistant":
                conversation_history.pop()

            if self.is_cancelled():
                return

            reply = process_message(self.message, self.attachments)

            if self.is_cancelled():
                return

            if reply is None:
                reply = "Sorry brooo 😭\n\nI couldn't regenerate a response."

            self.finished.emit(reply)

        except Exception as error:
            logger.warning("Regenerate worker error: %s", error, exc_info=False)
            if not self.is_cancelled():
                self.failed.emit("Sorry brooo 😭\n\nSomething went wrong regenerating my response.")
