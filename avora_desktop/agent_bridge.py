#!/usr/bin/env python3
"""
AVORA Desktop Agent Bridge - Non-blocking QThread worker.
Fixes P1: handle_request no longer blocks UI thread; cancel actually
interrupts the active worker via QThread requestInterruption.
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

backend_dir = os.path.join(project_root, "avora backend")
if os.path.isdir(backend_dir):
    sys.path.insert(0, backend_dir)

from PySide6.QtCore import QObject, Signal, QThread
from agent.orchestrator import AgentOrchestrator


class _Worker(QThread):
    """Runs orchestrator.handle_request off the UI thread."""
    finished_ok = Signal(dict)
    finished_err = Signal(str)

    def __init__(self, orchestrator: AgentOrchestrator, request: str):
        super().__init__()
        self._orchestrator = orchestrator
        self._request = request

    def run(self):
        # Check interruption before starting
        if self.isInterruptionRequested():
            self.finished_err.emit("Cancelled before start")
            return
        try:
            result = self._orchestrator.handle_request(self._request)
            if self.isInterruptionRequested():
                self.finished_err.emit("Cancelled")
                return
            self.finished_ok.emit(result if isinstance(result, dict) else {"success": True, "message": str(result)})
        except Exception as e:
            if self.isInterruptionRequested():
                self.finished_err.emit("Cancelled")
            else:
                self.finished_err.emit(f"Error during task execution: {e}")


class AgentBridge(QObject):
    """
    Wraps AgentOrchestrator to provide Qt signals for desktop UI integration.
    Non-blocking: handle_request spawns a QThread worker.
    """

    task_started = Signal(str)
    task_finished = Signal(str)
    task_failed = Signal(str)
    task_cancelled = Signal(str)
    activity_update = Signal(dict)
    permission_request = Signal(dict)

    def __init__(self, orchestrator: AgentOrchestrator | None = None):
        super().__init__()
        self.orchestrator = orchestrator or AgentOrchestrator()
        self._cancelled = False
        self._current_task_id = None
        self._worker: _Worker | None = None

    def handle_request(self, request: str) -> None:
        """Non-blocking: spawn worker thread for orchestrator execution."""
        # If a previous worker is still running, cancel it first
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()
            try:
                self.orchestrator.cancel()
            except Exception:
                pass

        self._cancelled = False
        self._current_task_id = str(id(request))
        self.task_started.emit(request)

        self._worker = _Worker(self.orchestrator, request)
        # Ensure orchestrator cancel flag is reset
        try:
            self.orchestrator.reset()
        except Exception:
            pass
        self._worker.finished_ok.connect(self._on_worker_ok)
        self._worker.finished_err.connect(self._on_worker_err)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_ok(self, result: dict):
        if self._cancelled:
            return
        if result.get("cancelled"):
            self.task_cancelled.emit(result.get("message", "Cancelled"))
        elif result.get("success", False):
            self.task_finished.emit(result.get("message", "Task completed"))
        else:
            self.task_failed.emit(result.get("message", "Task failed"))

    def _on_worker_err(self, msg: str):
        if self._cancelled or "Cancelled" in msg:
            self.task_cancelled.emit(msg)
        else:
            self.task_failed.emit(msg)

    def _on_worker_finished(self):
        # Clean up worker reference
        if self._worker is not None:
            try:
                self._worker.deleteLater()
            except Exception:
                pass
            self._worker = None

    def cancel_current(self) -> None:
        """Request cancellation: interrupt worker + set flags."""
        self._cancelled = True
        try:
            if hasattr(self.orchestrator, 'cancel'):
                self.orchestrator.cancel()
        except Exception:
            pass
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()
            # Give worker a brief window to exit, else we still emit cancelled
            if not self._worker.wait(1500):
                try:
                    self._worker.terminate()
                    self._worker.wait(500)
                except Exception:
                    pass
        self.task_cancelled.emit("Cancellation requested by user")

    # Compatibility shims expected by avora_desktop/main.py permission flow
    def setPaused(self, paused: bool) -> None:
        try:
            if hasattr(self.orchestrator, 'set_paused'):
                self.orchestrator.set_paused(paused)
        except Exception:
            pass

    def allowOnce(self) -> None:
        try:
            if hasattr(self.orchestrator, 'allow_once'):
                self.orchestrator.allow_once()
            elif hasattr(self.orchestrator, 'approve_permission'):
                self.orchestrator.approve_permission(once=True)
        except Exception:
            pass
        try:
            if hasattr(self.orchestrator, 'set_paused'):
                self.orchestrator.set_paused(False)
        except Exception:
            pass

    def allowForTask(self) -> None:
        try:
            if hasattr(self.orchestrator, 'allow_for_task'):
                self.orchestrator.allow_for_task()
            elif hasattr(self.orchestrator, 'approve_permission'):
                self.orchestrator.approve_permission(once=False)
        except Exception:
            pass
        try:
            if hasattr(self.orchestrator, 'set_paused'):
                self.orchestrator.set_paused(False)
        except Exception:
            pass

    def deny(self) -> None:
        try:
            if hasattr(self.orchestrator, 'deny_permission'):
                self.orchestrator.deny_permission()
            elif hasattr(self.orchestrator, 'deny'):
                self.orchestrator.deny()
        except Exception:
            pass
        try:
            if hasattr(self.orchestrator, 'set_paused'):
                self.orchestrator.set_paused(False)
        except Exception:
            pass

    def is_cancelled(self) -> bool:
        return self._cancelled

    def cleanup(self) -> None:
        """Clean up worker and orchestrator resources."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()
            try:
                self._worker.wait(1500)
            except Exception:
                pass
        try:
            if hasattr(self.orchestrator, 'cancel'):
                self.orchestrator.cancel()
        except Exception:
            pass

    def _update_activity(self, activity: dict) -> None:
        self.activity_update.emit(activity)

    def _request_permission(self, payload: dict) -> None:
        self.permission_request.emit(payload)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    bridge = AgentBridge()
    print("AgentBridge loaded. Available signals:")
    for sig in dir(bridge):
        if isinstance(getattr(bridge, sig), Signal):
            print(f"  - {sig}")
    sys.exit(app.exec())
