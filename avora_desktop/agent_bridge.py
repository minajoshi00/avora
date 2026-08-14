#!/usr/bin/env python3
"""
AVORA Desktop Agent Bridge - Phase 1
Adapts the existing AgentOrchestrator for Qt signal emission.
Reuses existing backend without modification.
"""

import sys
import os

# Add the avora project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PySide6.QtCore import QObject, Signal, Slot
from avora.backend.agent.orchestrator import AgentOrchestrator


class AgentBridge(QObject):
    """
    Wraps AgentOrchestrator to provide Qt signals for desktop UI integration.
    
    Exposes these signals:
    - task_started: emitted when a new task begins
    - task_finished: emitted when task completes
    - task_failed: emitted when task fails
    - task_cancelled: emitted when task is cancelled
    - activity_update: emitted with task status updates
    - permission_request: emitted when action requires user approval
    """
    
    task_started = Signal(str)  # task description
    task_finished = Signal(str)  # result summary
    task_failed = Signal(str)  # error message
    task_cancelled = Signal(str)  # reason
    activity_update = Signal(dict)  # status/task data
    permission_request = Signal(dict)  # permission request details
    
    def __init__(self, orchestrator: AgentOrchestrator | None = None):
        super().__init__()
        self.orchestrator = orchestrator or AgentOrchestrator()
        self._cancelled = False
        self._current_task_id = None
        
    def handle_request(self, request: str) -> None:
        """
        Process a natural-language request through AgentOrchestrator.
        Emits signals as execution progresses.
        """
        self._cancelled = False
        self._current_task_id = str(id(request))
        
        self.task_started.emit(request)
        
        try:
            result = self.orchestrator.handle_request(request)
            
            # Emit outcome based on result
            if result.get("success", False):
                self.task_finished.emit(result.get("message", "Task completed"))
            else:
                self.task_failed.emit(result.get("message", "Task failed"))
                
        except Exception as e:
            self.task_failed.emit(f"Error during task execution: {str(e)}")
    
    def cancel_current(self) -> None:
        """Request cancellation of the current task."""
        self._cancelled = True
        self.task_cancelled.emit("Cancellation requested by user")
    
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancelled
    
    # ------------------------------------------------------------------
    #  Activity / status helpers
    # ------------------------------------------------------------------
    
    def _update_activity(self, activity: dict) -> None:
        """Emit an activity status update."""
        self.activity_update.emit(activity)
    
    def _request_permission(self, payload: dict) -> None:
        """Emit a permission request to the UI layer."""
        self.permission_request.emit(payload)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    bridge = AgentBridge()
    print("AgentBridge loaded. Available signals:")
    for sig in dir(bridge):
        if isinstance(getattr(bridge, sig), Signal):
            print(f"  - {sig}")
    sys.exit(app.exec_())
