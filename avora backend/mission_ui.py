"""
========================================================================
AVORA MISSIONS - Mission UI Components
========================================================================

Provides UI components for displaying and managing missions.
Integrates with the existing AVORA design system.

Components:
  - MissionDashboard: Main mission overview
  - MissionCard: Individual mission display
  - MilestoneList: Milestone progress view
  - TaskList: Current tasks view
  - ProgressBar: Visual progress indicator

Integration:
  - Uses existing AVORA theme system
  - Integrates with main window sidebar
  - Character notification support
  - Voice feedback support
"""

from __future__ import annotations

import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QScrollArea, QSizePolicy,
    QMessageBox, QInputDialog, QDialog, QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPalette

from settings import get_setting, set_setting
from mission_tracker import get_mission_tracker, Mission, Milestone, Task
from character import react_naturally

# =========================================================================
# EXPORT FUNCTIONALITY
# =========================================================================

def _handle_export_mission(mission: Mission, parent=None):
    """
    Export mission project files.
    
    Args:
        mission: Mission to export
        parent: Parent widget for dialogs
    """
    try:
        from mission_exporter import get_mission_exporter
        exporter = get_mission_exporter()
        
        # Get project files
        project_files = exporter.get_project_files(mission.id)
        
        if not project_files:
            QMessageBox.warning(
                parent,
                "No Files to Export",
                "This mission doesn't have any tracked files yet.\n\n"
                "Files are tracked automatically when created during task execution.",
            )
            return None
        
        # Check readiness
        readiness = exporter.is_project_ready_for_export(mission.id)
        
        if not readiness.get("ready"):
            QMessageBox.warning(
                parent,
                "Project Not Ready",
                f"Cannot export: {readiness.get('reason', 'Unknown reason')}",
            )
            return None
        
        # Export
        result = exporter.export_mission_project(
            mission_id=mission.id,
            project_files=project_files,
        )
        
        if result.get("success"):
            # Show success
            msg = (
                f"✅ Project exported successfully!\n\n"
                f"Files: {result.get('file_count', 0)}\n"
                f"Size: {result.get('size_bytes', 0) / 1024:.1f} KB\n"
                f"Location: {result.get('path', 'Unknown')}\n\n"
                f"Would you like to open the folder?"
            )
            
            reply = QMessageBox.question(
                parent,
                "Export Complete",
                msg,
                QMessageBox.Yes | QMessageBox.No,
            )
            
            if reply == QMessageBox.Yes:
                # Open folder
                try:
                    from skills.files import open_file
                    export_path = Path(result.get("path", ""))
                    if export_path.exists():
                        if export_path.is_file():
                            open_file(export_path.parent)
                        else:
                            open_file(export_path)
                except Exception:
                    pass
            
            return result
        else:
            QMessageBox.critical(
                parent,
                "Export Failed",
                f"Failed to export project:\n{result.get('error', 'Unknown error')}",
            )
            return None
            
    except Exception as e:
        QMessageBox.critical(
            parent,
            "Export Error",
            f"Error during export: {e}",
        )
        return None


# =========================================================================
# MISSION CARD
# =========================================================================

class MissionCard(QFrame):
    """A card displaying mission summary information."""
    
    clicked = Signal(str)  # mission_id
    action_requested = Signal(str, str)  # mission_id, action
    
    def __init__(self, mission: Mission, parent=None):
        super().__init__(parent)
        self.mission = mission
        self.setup_ui()
    
    def setup_ui(self):
        """Create the card UI."""
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: rgba(20, 20, 35, 0.8);
                border: 1px solid rgba(139, 122, 255, 0.3);
                border-radius: 12px;
                padding: 16px;
                margin: 8px;
            }
            QFrame:hover {
                background: rgba(30, 30, 50, 0.9);
                border: 1px solid rgba(139, 122, 255, 0.5);
            }
            QLabel {
                color: #F5F5F5;
                background: transparent;
            }
            QPushButton {
                background: rgba(139, 122, 255, 0.2);
                color: #F5F5F5;
                border: 1px solid rgba(139, 122, 255, 0.5);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(139, 122, 255, 0.4);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title and category
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.mission.title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        
        category_label = QLabel(self.mission.category.title())
        category_label.setStyleSheet("""
            color: #8B7AFF;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 8px;
            background: rgba(139, 122, 255, 0.1);
            border-radius: 4px;
        """)
        
        header_layout.addWidget(title_label, stretch=1)
        header_layout.addWidget(category_label)
        
        # Progress bar
        progress = self.mission.calculate_progress()
        progress_bar = QProgressBar()
        progress_bar.setValue(int(progress * 100))
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: #F5F5F5;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B7AFF, stop:1 #6366F1);
                border-radius: 4px;
            }
        """)
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{int(progress * 100)}%")
        
        # Stats
        stats_layout = QHBoxLayout()
        
        total_tasks = sum(len(m.tasks) for m in self.mission.milestones)
        completed_tasks = sum(
            1 for m in self.mission.milestones 
            for t in m.tasks if t.status == "completed"
        )
        
        tasks_label = QLabel(f"Tasks: {completed_tasks}/{total_tasks}")
        tasks_label.setStyleSheet("color: #858599; font-size: 12px;")
        
        milestones_label = QLabel(f"Milestones: {len(self.mission.milestones)}")
        milestones_label.setStyleSheet("color: #858599; font-size: 12px;")
        
        stats_layout.addWidget(tasks_label)
        stats_layout.addStretch()
        stats_layout.addWidget(milestones_label)
        
        # Current task
        current_task = self.mission.get_next_task()
        if current_task:
            task_label = QLabel(f"Next: {current_task.title}")
            task_label.setStyleSheet("color: #8B7AFF; font-size: 12px; font-weight: 500;")
            task_label.setWordWrap(True)
        else:
            task_label = QLabel("All tasks complete! 🎉")
            task_label.setStyleSheet("color: #10B981; font-size: 12px; font-weight: 500;")
        
        # Action button
        action_btn = QPushButton("Continue Mission")
        action_btn.clicked.connect(lambda: self.action_requested.emit(self.mission.id, "continue"))
        
        # Assemble
        layout.addLayout(header_layout)
        layout.addWidget(progress_bar)
        layout.addLayout(stats_layout)
        layout.addWidget(task_label)
        layout.addWidget(action_btn)
        
        # Click handler
        self.mousePressEvent = lambda event: self.clicked.emit(self.mission.id)
    
    def update_mission(self, mission: Mission):
        """Update card with new mission data."""
        self.mission = mission
        # Refresh UI
        self.setup_ui()


# =========================================================================
# MISSION DETAIL DIALOG
# =========================================================================

class MissionDetailDialog(QDialog):
    """Detailed view of a mission with milestones and tasks."""
    
    def __init__(self, mission: Mission, parent=None):
        super().__init__(parent)
        self.mission = mission
        self.tracker = get_mission_tracker()
        self.setup_ui()
    
    def setup_ui(self):
        """Create the detail dialog UI."""
        self.setWindowTitle(f"Mission: {self.mission.title}")
        self.setMinimumWidth(600)
        self.setStyleSheet("""
            QDialog {
                background: #0B0B12;
            }
            QLabel {
                color: #F5F5F5;
                background: transparent;
            }
            QPushButton {
                background: rgba(139, 122, 255, 0.2);
                color: #F5F5F5;
                border: 1px solid rgba(139, 122, 255, 0.5);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(139, 122, 255, 0.4);
            }
            QFrame {
                background: rgba(20, 20, 35, 0.8);
                border: 1px solid rgba(139, 122, 255, 0.3);
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header
        header = QLabel(self.mission.title)
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(header)
        
        desc_label = QLabel(self.mission.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #858599;")
        layout.addWidget(desc_label)
        
        # Progress
        progress = self.mission.calculate_progress()
        progress_bar = QProgressBar()
        progress_bar.setValue(int(progress * 100))
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                height: 10px;
                text-align: center;
                color: #F5F5F5;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B7AFF, stop:1 #6366F1);
                border-radius: 4px;
            }
        """)
        layout.addWidget(QLabel(f"Progress: {int(progress * 100)}%"))
        layout.addWidget(progress_bar)
        
        # Milestones and tasks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)
        
        for milestone in self.mission.milestones:
            milestone_frame = QFrame()
            milestone_layout = QVBoxLayout(milestone_frame)
            
            milestone_title = QLabel(milestone.title)
            milestone_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            milestone_title.setStyleSheet("color: #8B7AFF;")
            
            milestone_progress = milestone.get_progress()
            milestone_bar = QProgressBar()
            milestone_bar.setValue(int(milestone_progress * 100))
            milestone_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 3px;
                    height: 6px;
                }
                QProgressBar::chunk {
                    background: rgba(139, 122, 255, 0.6);
                    border-radius: 3px;
                }
            """)
            
            milestone_layout.addWidget(milestone_title)
            milestone_layout.addWidget(milestone_bar)
            
            # Tasks
            for task in milestone.tasks:
                task_widget = QWidget()
                task_layout = QHBoxLayout(task_widget)
                task_layout.setContentsMargins(8, 4, 8, 4)
                
                task_label = QLabel(f"☐ {task.title}")
                task_label.setStyleSheet("color: #F5F5F5; font-size: 12px;")
                
                complete_btn = QPushButton("Complete")
                complete_btn.setMaximumWidth(80)
                complete_btn.clicked.connect(
                    lambda checked, t=task: self.complete_task(t)
                )
                
                task_layout.addWidget(task_label, stretch=1)
                task_layout.addWidget(complete_btn)
                
                milestone_layout.addWidget(task_widget)
            
            content_layout.addWidget(milestone_frame)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Export button
        export_btn = QPushButton("📦 Export Project")
        export_btn.clicked.connect(self.export_project)
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.accept)
        
        # Add buttons to layout
        layout.addWidget(export_btn)
        layout.addWidget(buttons)
    
    def complete_task(self, task: Task):
        """Mark a task as complete."""
        self.tracker.complete_task(self.mission.id, task.id)
        QMessageBox.information(self, "Task Complete", f"Completed: {task.title}")
        self.setup_ui()  # Refresh UI
    
    def export_project(self):
        """Export the mission project."""
        result = _handle_export_mission(self.mission, self)
        if result and result.get("success"):
            self.accept()  # Close dialog after successful export


# =========================================================================
# MISSION DASHBOARD
# =========================================================================

class MissionDashboard(QWidget):
    """
    Main mission dashboard widget.
    Shows active missions and provides management interface.
    """
    
    mission_selected = Signal(str)  # mission_id
    mission_action = Signal(str, str)  # mission_id, action
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tracker = get_mission_tracker()
        self.setup_ui()
        self.refresh_missions()
    
    def setup_ui(self):
        """Create the dashboard UI."""
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
            QLabel {
                color: #F5F5F5;
                background: transparent;
            }
            QPushButton {
                background: rgba(139, 122, 255, 0.2);
                color: #F5F5F5;
                border: 1px solid rgba(139, 122, 255, 0.5);
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(139, 122, 255, 0.4);
            }
            QPushButton#secondary {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton#secondary:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🚀 Missions")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        
        self.create_btn = QPushButton("+ New Mission")
        self.create_btn.clicked.connect(self.create_mission)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.create_btn)
        
        layout.addLayout(header_layout)
        
        # Mission list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.missions_container = QWidget()
        self.missions_layout = QVBoxLayout(self.missions_container)
        self.missions_layout.setSpacing(8)
        self.missions_layout.addStretch()
        
        scroll.setWidget(self.missions_container)
        layout.addWidget(scroll, stretch=1)
        
        # Status label
        self.status_label = QLabel("No active missions")
        self.status_label.setStyleSheet("color: #858599; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
    
    def refresh_missions(self):
        """Refresh the mission list."""
        # Clear existing cards
        while self.missions_layout.count() > 1:
            item = self.missions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get active missions
        missions = self.tracker.get_active_missions()
        
        if not missions:
            self.status_label.setText("No active missions. Create one to get started!")
            return
        
        self.status_label.setText(f"{len(missions)} active mission(s)")
        
        # Create cards
        for mission in missions:
            card = MissionCard(mission)
            card.clicked.connect(self.mission_selected)
            card.action_requested.connect(self.mission_action)
            self.missions_layout.insertWidget(self.missions_layout.count() - 1, card)
    
    def create_mission(self):
        """Create a new mission."""
        text, ok = QInputDialog.getText(
            self,
            "New Mission",
            "What do you want to accomplish?",
        )
        
        if ok and text.strip():
            # Use mission planner
            try:
                from mission_planner import get_mission_planner
                planner = get_mission_planner()
                mission = planner.plan_mission(text.strip())
                
                if mission:
                    self.refresh_missions()
                    self.mission_selected.emit(mission.id)
                    
                    # Show success notification
                    QMessageBox.information(
                        self,
                        "Mission Created",
                        f"Mission created: {mission.title}\n\n"
                        f"Category: {mission.category}\n"
                        f"Milestones: {len(mission.milestones)}\n"
                        f"Estimated deadline: {datetime.fromtimestamp(mission.deadline).strftime('%B %d, %Y') if mission.deadline else 'Not set'}",
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Could not create mission. Please try again.",
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create mission: {e}",
                )
    
    def show_mission_detail(self, mission_id: str):
        """Show detailed view of a mission."""
        mission = self.tracker.get_mission(mission_id)
        if not mission:
            return
        
        dialog = MissionDetailDialog(mission, self)
        dialog.exec()
        self.refresh_missions()


# =========================================================================
# WELCOME BACK WIDGET
# =========================================================================

class WelcomeBackWidget(QFrame):
    """
    Shows active mission and next recommended action on startup.
    """
    
    continue_mission = Signal(str)  # mission_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tracker = get_mission_tracker()
        self.setup_ui()
    
    def setup_ui(self):
        """Create the welcome back UI."""
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(139, 122, 255, 0.1),
                    stop:1 rgba(99, 102, 241, 0.05));
                border: 1px solid rgba(139, 122, 255, 0.3);
                border-radius: 16px;
                padding: 24px;
                margin: 16px;
            }
            QLabel {
                color: #F5F5F5;
                background: transparent;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B7AFF, stop:1 #6366F1);
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9B8AFF, stop:1 #7376F1);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Greeting
        self.greeting_label = QLabel("Welcome back! 👋")
        self.greeting_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(self.greeting_label)
        
        # Mission info
        self.mission_label = QLabel("You have no active missions.")
        self.mission_label.setWordWrap(True)
        self.mission_label.setStyleSheet("color: #F5F5F5; font-size: 14px;")
        layout.addWidget(self.mission_label)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: #F5F5F5;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B7AFF, stop:1 #6366F1);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Next action
        self.next_action_label = QLabel("")
        self.next_action_label.setWordWrap(True)
        self.next_action_label.setStyleSheet("color: #8B7AFF; font-size: 13px;")
        layout.addWidget(self.next_action_label)
        
        # Continue button
        self.continue_btn = QPushButton("Continue Mission")
        self.continue_btn.clicked.connect(self.on_continue)
        self.continue_btn.setVisible(False)
        layout.addWidget(self.continue_btn)
    
    def update_mission(self):
        """Update with current active mission."""
        missions = self.tracker.get_active_missions()
        
        if not missions:
            self.mission_label.setText("You have no active missions.")
            self.progress_bar.setVisible(False)
            self.next_action_label.setText("Create a mission to get started!")
            self.continue_btn.setVisible(False)
            return
        
        # Get highest priority mission
        mission = max(missions, key=lambda m: m.priority)
        progress = mission.calculate_progress()
        
        self.mission_label.setText(
            f"You were working on:\n{mission.title}"
        )
        self.progress_bar.setValue(int(progress * 100))
        self.progress_bar.setFormat(f"{int(progress * 100)}% complete")
        self.progress_bar.setVisible(True)
        
        # Get next action
        action = self.tracker.get_next_action(mission.id)
        if action:
            self.next_action_label.setText(
                f"Next: {action['task_title']}\n"
                f"Estimated: {action['estimated_minutes']} minutes"
            )
            self.continue_btn.setVisible(True)
            self._current_mission_id = mission.id
        else:
            self.next_action_label.setText("Mission complete! 🎉")
            self.continue_btn.setVisible(False)
            self._current_mission_id = None
    
    def on_continue(self):
        """Handle continue button click."""
        if hasattr(self, '_current_mission_id'):
            self.continue_mission.emit(self._current_mission_id)


# =========================================================================
# PUBLIC API
# =========================================================================

__all__ = [
    "MissionCard",
    "MissionDetailDialog",
    "MissionDashboard",
    "WelcomeBackWidget",
]