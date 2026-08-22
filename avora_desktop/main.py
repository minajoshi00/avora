#!/usr/bin/env python3
"""
AVORA Desktop Agent - Main Application

A polished PySide6 desktop assistant that connects to the existing Python backend.
Implements Stop/Cancel, Retry, Progress, Activity, and Permissions features.
"""

import sys
import os

# Add project root to Python path for backend imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QLineEdit, QFrame, QScrollArea,
    QDialog, QVBoxLayout as QDialogVBoxLayout, QHBoxLayout as QDialogHBoxLayout,
    QProgressBar, QTextEdit, QListWidget, QListWidgetItem, QStackedWidget,
    QSpacerItem, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, qApp, QPropertyAnimation
from PySide6.QtGui import QFont, QPainter, QColor, QIcon, QTextOption
from PySide6.QtCore import QEasingCurve

from agent_bridge import AgentBridge


# Task states
class TaskState:
    IDLE = "idle"
    LISTENING = "listening"
    UNDERSTANDING = "understanding"
    THINKING = "thinking"
    PROCESSING = "processing"
    WORKING = "working"
    WAITING_PERMISSION = "waiting_permission"
    VERIFYING = "verifying"
    SPEAKING = "speaking"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class ActivityItem:
    """Represents a tool activity item."""
    def __init__(self, tool: str, status: str, details: str = ""):
        self.tool = tool
        self.status = status  # "running", "completed", "failed", "pending"
        self.details = details


class AvoraCharacter(QLabel):
    """Visual character/avatar indicator."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("🤖")
        self.setFixedSize(64, 64)
        self.setFont(QFont("Arial", 28))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            border-radius: 32px;
            background: qlineargradient(135deg, #6366f1, #8b5cf6);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        """)
        self._state = TaskState.IDLE
        
    def setState(self, state: str):
        """Update character state with visual feedback."""
        self._state = state
        state_styles = {
            TaskState.IDLE: "background: qlineargradient(135deg, #6366f1, #8b5cf6);",
            TaskState.LISTENING: "background: qlineargradient(135deg, #10b981, #059669);",
            TaskState.THINKING: "background: qlineargradient(135deg, #f59e0b, #d97706);",
            TaskState.WORKING: "background: qlineargradient(135deg, #8b5cf6, #6366f1);",
            TaskState.WAITING_PERMISSION: "background: qlineargradient(135deg, #f97316, #ea580c);",
            TaskState.SUCCESS: "background: qlineargradient(135deg, #22c55e, #16a34a);",
            TaskState.ERROR: "background: qlineargradient(135deg, #ef4444, #dc2626);",
            TaskState.CANCELLED: "background: qlineargradient(135deg, #6b7280, #4b5563);",
        }
        self.setStyleSheet(f"""
            border-radius: 32px;
            {state_styles.get(state, state_styles[TaskState.IDLE])}
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        """)
        # Change emoji based on state
        emojis = {
            TaskState.IDLE: "🤖",
            TaskState.LISTENING: "🎧",
            TaskState.THINKING: "🧠",
            TaskState.WORKING: "🚀",
            TaskState.WAITING_PERMISSION: "🔐",
            TaskState.SUCCESS: "✅",
            TaskState.ERROR: "❌",
            TaskState.CANCELLED: "⏹️",
        }
        self.setText(emojis.get(state, "🤖"))


class PermissionDialog(QDialog):
    """Dialog for permission requests."""
    
    allowOnce = Signal()
    allowForTask = Signal()
    deny = Signal()
    
    def __init__(self, action: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AVORA Permission")
        self.setModal(True)
        self.setFixedSize(360, 180)
        
        layout = QDialogVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Message
        self.title_label = QLabel("AVORA wants permission to:")
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.title_label)
        
        self.action_label = QLabel(action)
        self.action_label.setStyleSheet("color: #a3a3a3; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 8px;")
        layout.addWidget(self.action_label)
        
        # Buttons
        btn_layout = QDialogHBoxLayout()
        btn_layout.addStretch()
        
        self.deny_btn = QPushButton("Deny")
        self.deny_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid rgba(239, 68, 68, 0.4);
                color: #ef4444;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
            }
        """)
        self.deny_btn.clicked.connect(lambda: (self.deny.emit(), self.accept()))
        
        self.allow_task_btn = QPushButton("Allow for Task")
        self.allow_task_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59, 130, 246, 0.2);
                border: 1px solid rgba(59, 130, 246, 0.4);
                color: #3b82f6;
                padding: 8px 16px;
                border-radius: 6px;
                margin-right: 8px;
            }
            QPushButton:hover {
                background: rgba(59, 130, 246, 0.3);
            }
        """)
        self.allow_task_btn.clicked.connect(lambda: (self.allowForTask.emit(), self.accept()))
        
        self.allow_once_btn = QPushButton("Allow Once")
        self.allow_once_btn.setStyleSheet("""
            QPushButton {
                background: rgba(16, 185, 129, 0.2);
                border: 1px solid rgba(16, 185, 129, 0.4);
                color: #10b981;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(16, 185, 129, 0.3);
            }
        """)
        self.allow_once_btn.clicked.connect(lambda: (self.allowOnce.emit(), self.accept()))
        
        btn_layout.addWidget(self.allow_once_btn)
        btn_layout.addWidget(self.allow_task_btn)
        btn_layout.addWidget(self.deny_btn)
        
        layout.addLayout(btn_layout)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))


class ToolActivityWidget(QFrame):
    """Shows real tool activity with expand/collapse."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        self.header = QLabel("AVORA is working")
        self.header.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        self.toggle_btn = QPushButton("▼")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8b5cf6;
                font-size: 12px;
                padding: 0;
            }
        """)
        self.toggle_btn.toggled.connect(self._onToggle)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.header, 1)
        header_layout.addWidget(self.toggle_btn)
        self.setLayout(layout)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                padding: 0;
            }
            QListWidget::item {
                padding: 4px 0;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.list_widget)
        
        self._activities: list[ActivityItem] = []
    
    def _onToggle(self, checked: bool):
        self.toggle_btn.setText("▲" if not checked else "▼")
        self.list_widget.setVisible(checked)
    
    def addActivity(self, tool: str, status: str, details: str = ""):
        """Add a new activity item."""
        item = ActivityItem(tool, status, details)
        self._activities.append(item)
        
        # Add to list widget
        widget = QWidget()
        h_layout = QHBoxLayout(widget)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        status_style = {
            "running": "color: #8b5cf6;",
            "completed": "color: #10b981;",
            "failed": "color: #ef4444;",
            "pending": "color: #f59e0b;",
        }
        
        status_icon = {"running": "→", "completed": "✓", "failed": "✗", "pending": "○"}
        
        status_label = QLabel(f"{status_icon.get(status, '')} {tool}")
        status_label.setStyleSheet(f"background: rgba(255,255,255,0.05); padding: 4px 8px; border-radius: 4px; {status_style.get(status, '')}")
        if details:
            detail_label = QLabel(f"<small>{details}</small>")
            detail_label.setStyleSheet("color: #666;")
            h_layout.addWidget(detail_label)
        h_layout.addWidget(status_label)
        h_layout.addStretch()
        
        list_item = QListWidgetItem()
        list_item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, widget)
    
    def updateActivity(self, tool: str, status: str):
        """Update an existing activity."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                for child in widget.findChildren(QLabel):
                    if tool in child.text():
                        child.setText(f"{status_icon.get(status, '')} {tool}")
                        child.setStyleSheet(f"background: rgba(255,255,255,0.05); padding: 4px 8px; border-radius: 4px; {status_style.get(status, '')}")
                        break
    
    def clear(self):
        """Clear all activities."""
        self._activities.clear()
        self.list_widget.clear()


class AvoraDesktopWindow(QMainWindow):
    """Main AVORA desktop assistant window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AVORA")
        self.setWindowIcon(QIcon())
        self.resize(500, 650)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(180deg, #0a0a0f, #1a1a2e);
            }
            * {
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }
        """)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("background: rgba(255,255,255,0.03); padding: 16px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 16, 16, 16)
        
        self.character = AvoraCharacter()
        h_layout.addWidget(self.character)
        
        title = QLabel("AVORA")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("margin-left: 8px;")
        h_layout.addWidget(title)
        h_layout.addStretch()
        
        self.state_label = QLabel(TaskState.IDLE)
        self.state_label.setStyleSheet("color: #888;")
        h_layout.addWidget(self.state_label)
        
        main_layout.addWidget(header)
        
        # Status bar for progress
        self.status_bar = QProgressBar(self)
        self.status_bar.setValue(0)
        self.status_bar.setTextVisible(True)
        self.status_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255,255,255,0.05);
                border: none;
                border-radius: 4px;
                height: 4px;
                text-align: center;
            }
        """)
        main_layout.addWidget(self.status_bar)
        
        # Chat area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_area.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.chat_area.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                padding: 12px 16px;
                color: #e5e5e5;
            }
        """)
        main_layout.addWidget(self.chat_area, 1)
        
        # Tool activity widget
        self.activity_widget = ToolActivityWidget()
        main_layout.addWidget(self.activity_widget)
        
        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet("background: rgba(255,255,255,0.03);")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 16)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 12px;
                padding: 10px 14px;
                color: #e5e5e5;
            }
            QLineEdit:focus {
                border-color: rgba(99, 102, 241, 0.5);
            }
        """)
        self.input_field.returnPressed.connect(self._onSend)
        
        # Control buttons
        self.stop_btn = QPushButton("Stop / Cancel")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid rgba(239, 68, 68, 0.4);
                color: #ef4444;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                color: #666;
            }
        """)
        self.stop_btn.clicked.connect(self._onStop)
        
        self.retry_btn = QPushButton("Retry")
        self.retry_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59, 130, 246, 0.2);
                border: 1px solid rgba(59, 130, 246, 0.4);
                color: #3b82f6;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                color: #666;
            }
        """)
        self.retry_btn.clicked.connect(self._onRetry)
        self.retry_btn.setEnabled(False)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(135deg, #6366f1, #8b5cf6);
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 12px;
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.1);
                color: #666;
            }
        """)
        self.send_btn.clicked.connect(self._onSend)
        self.send_btn.setEnabled(False)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.stop_btn)
        input_layout.addWidget(self.retry_btn)
        input_layout.addWidget(self.send_btn)
        
        main_layout.addWidget(input_frame)
        
        # Initialize bridge
        self.bridge = AgentBridge()
        self._connectSignals()
        
        # State tracking
        self._is_running = False
        self._has_error = False
        self._current_request = None
        self._permission_dialog = None
        self._permission_callback = None
        
    def _connectSignals(self):
        """Connect AgentBridge signals to UI slots."""
        self.bridge.task_started.connect(self._onTaskStarted)
        self.bridge.task_finished.connect(self._onTaskFinished)
        self.bridge.task_failed.connect(self._onTaskFailed)
        self.bridge.task_cancelled.connect(self._onTaskCancelled)
        self.bridge.activity_update.connect(self._onActivityUpdate)
        self.bridge.permission_request.connect(self._onPermissionRequest)
        
    def _onTaskStarted(self, request: str):
        """Handle task started."""
        self._is_running = True
        self._has_error = False
        self._current_request = request
        
        self.character.setState(TaskState.WORKING)
        self.state_label.setText("Working")
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.input_field.setEnabled(False)
        
        self.status_bar.setRange(0, 0)  # Indeterminate progress
        
        # Add user message to chat
        self.chat_area.append(f"<b style='color:#6366f1'>You:</b> {request}")
        
    def _onTaskFinished(self, result: str):
        """Handle task finished."""
        self._is_running = False
        self._current_request = None
        
        self.character.setState(TaskState.SUCCESS)
        self.state_label.setText("Done")
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.input_field.setEnabled(True)
        self.status_bar.setValue(100)
        
        # Add response to chat
        self.chat_area.append(f"<b style='color:#22c55e'>AVORA:</b> {result}")
        
        # Auto-scroll
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        
        # Reset after animation
        QTimer.singleShot(1500, self._resetSuccessState)
        
    def _resetSuccessState(self):
        if not self._is_running:
            self.character.setState(TaskState.IDLE)
            self.state_label.setText(TaskState.IDLE)
            
    def _onTaskFailed(self, error: str):
        """Handle task failed."""
        self._is_running = False
        self._has_error = True
        self._current_request = None
        
        self.character.setState(TaskState.ERROR)
        self.state_label.setText("Error")
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.input_field.setEnabled(True)
        self.status_bar.setValue(0)
        
        # Add error to chat
        self.chat_area.append(f"<b style='color:#ef4444'>AVORA:</b> {error}")
        
        # Auto-scroll
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        
        # Show retry button
        self.retry_btn.setEnabled(True)
        
        QTimer.singleShot(2000, self._resetErrorState)
        
    def _resetErrorState(self):
        if not self._is_running:
            self.character.setState(TaskState.IDLE)
            self.state_label.setText(TaskState.IDLE)
            
    def _onTaskCancelled(self, reason: str):
        """Handle task cancelled."""
        self._is_running = False
        self._current_request = None
        
        self.character.setState(TaskState.CANCELLED)
        self.state_label.setText("Cancelled")
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.input_field.setEnabled(True)
        self.status_bar.setValue(0)
        
        # Add cancellation to chat
        self.chat_area.append(f"<b style='color:#6b7280'>AVORA:</b> Task stopped.")
        
        # Auto-scroll
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        
        # Reset after animation
        QTimer.singleShot(1500, self._resetCancelledState)
        
    def _resetCancelledState(self):
        if not self._is_running:
            self.character.setState(TaskState.IDLE)
            self.state_label.setText(TaskState.IDLE)
            
    def _onActivityUpdate(self, data: dict):
        """Handle activity updates."""
        tool = data.get("tool", "")
        status = data.get("status", "")
        details = data.get("details", "")
        self.activity_widget.addActivity(tool, status, details)
        
    def _onPermissionRequest(self, payload: dict):
        """Handle permission requests from the bridge."""
        action = payload.get("action", "an action")
        self._showPermissionDialog(action)
    
    def _showPermissionDialog(self, action: str):
        """Show permission dialog and wait for response."""
        if self._permission_dialog:
            return  # Already showing
            
        self._permission_dialog = PermissionDialog(action, self)
        self._permission_dialog.allowOnce.connect(self._onAllowOnce)
        self._permission_dialog.allowForTask.connect(self._onAllowForTask)
        self._permission_dialog.deny.connect(self._onDeny)
        self._permission_dialog.show()
        self.bridge.setPaused(True)
        
    def _onAllowOnce(self):
        """Handle allow once permission."""
        if self._permission_dialog:
            self._permission_dialog.close()
            self._permission_dialog = None
            self.bridge.setPaused(False)
            self.bridge.allowOnce()
            
    def _onAllowForTask(self):
        """Handle allow for task permission."""
        if self._permission_dialog:
            self._permission_dialog.close()
            self._permission_dialog = None
            self.bridge.setPaused(False)
            self.bridge.allowForTask()
            
    def _onDeny(self):
        """Handle denied permission."""
        if self._permission_dialog:
            self._permission_dialog.close()
            self._permission_dialog = None
            self.bridge.setPaused(False)
            self.bridge.deny()
        
    def _onSend(self):
        """Send user message or execute request."""
        if self._is_running:
            return  # Already running
            
        text = self.input_field.text().strip()
        if not text:
            return
            
        # Clear previous retry
        self.retry_btn.setEnabled(False)
        
        # Send to bridge
        self.bridge.handle_request(text)
        
        # Clear input
        self.input_field.clear()
        
    def _onStop(self):
        """Stop current task."""
        if self._is_running:
            self.character.setState(TaskState.CANCELLED)
            self.state_label.setText("Cancelling...")
            self.bridge.cancel_current()
            
    def _onRetry(self):
        """Retry the last failed task."""
        if self._current_request:
            self.retry_btn.setEnabled(False)
            self.bridge.handle_request(self._current_request)
            self.input_field.clear()


def main():
    """Entry point for AVORA Desktop."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Dark theme
    app.setStyleSheet("""
        QTextEdit, QLineEdit {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 8px;
            color: white;
        }
    """)
    
    window = AvoraDesktopWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()