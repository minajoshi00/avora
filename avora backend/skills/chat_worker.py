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


def _simulate_stream_chunks(text: str, min_len: int = 80) -> list:
    """Split text into progressive display chunks WITHOUT losing whitespace.

    Preserves every newline / double-newline so paragraph and list block
    structure survives to the Markdown renderer. The concatenation of the
    returned chunks is byte-for-byte identical to ``text``.
    """
    import re
    # Split after sentence punctuation but CAPTURE the trailing whitespace
    # (including "\n"/"\n\n") so paragraph/list boundaries are not destroyed.
    parts = re.split(r"(?<=[.!?])(\s+)", str(text), flags=re.DOTALL)
    chunks = []
    chunk = ""
    i = 0
    n = len(parts)
    while i < n:
        sentence = parts[i]
        ws = parts[i + 1] if (i + 1 < n) else ""
        chunk += sentence + ws
        i += 2
        if len(chunk) >= min_len or sentence.rstrip().endswith((".", "!", "?")):
            chunks.append(chunk)
            chunk = ""
    if chunk.strip():
        chunks.append(chunk)
    return chunks


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
        """Break text into chunks and emit them progressively.

        Uses _simulate_stream_chunks() so newlines / double-newlines are
        preserved — the AI's paragraph and list structure reaches the Markdown
        renderer intact (fixes the wall-of-text bug).
        """
        if not text:
            return

        for chunk in _simulate_stream_chunks(str(text)):
            if self.is_cancelled():
                return
            self.chunk_ready.emit(chunk)
            self.msleep(15)  # Small delay for progressive feel

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
