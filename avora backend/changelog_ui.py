"""
AVORA Changelog UI

Displays what's new information inside the application.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
)

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from changelog import get_changelog_manager, ChangelogEntry


class ChangelogDialog(QDialog):
    """Dialog showing changelog information."""
    
    def __init__(
        self,
        current_version: str,
        parent=None,
    ):
        super().__init__(parent)
        
        self.current_version = current_version
        self.changelog_manager = get_changelog_manager()
        
        self.setWindowTitle("What's New")
        self.setMinimumSize(600, 500)
        
        self.build_ui()
        self.apply_styles()
    
    def build_ui(self):
        """Build the changelog UI."""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("ChangelogHeader")
        header.setStyleSheet("""
            QWidget#ChangelogHeader {
                background: #1a1a2e;
                padding: 20px;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        title = QLabel("✨ What's New")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        
        subtitle = QLabel(f"Version {self.current_version}")
        subtitle.setStyleSheet("font-size: 13px; color: #8995AE;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle, 1)
        
        root_layout.addWidget(header)
        
        # Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)
        
        # Add changelog entries
        entries = self.changelog_manager.get_entries(limit=5) if self.changelog_manager else []
        
        if not entries:
            no_changes = QLabel("No changelog entries available.")
            no_changes.setStyleSheet("color: #8995AE; font-size: 14px;")
            content_layout.addWidget(no_changes)
        else:
            for entry in entries:
                entry_widget = self.create_entry_widget(entry)
                content_layout.addWidget(entry_widget)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)
        
        # Footer
        footer = QWidget()
        footer.setObjectName("ChangelogFooter")
        footer.setStyleSheet("""
            QWidget#ChangelogFooter {
                background: #0a0a0f;
                padding: 15px 30px;
            }
            QPushButton {
                background: #9B5CFF;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #AC73FF;
            }
        """)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(30, 15, 30, 15)
        footer_layout.addStretch()
        
        close_button = QPushButton("Got it!")
        close_button.clicked.connect(self.accept)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        footer_layout.addWidget(close_button)
        root_layout.addWidget(footer)
    
    def create_entry_widget(self, entry: ChangelogEntry) -> QWidget:
        """Create a widget for a single changelog entry."""
        widget = QWidget()
        widget.setObjectName("ChangelogEntry")
        widget.setStyleSheet("""
            QWidget#ChangelogEntry {
                background: #111827;
                border: 1px solid #24324D;
                border-radius: 16px;
                padding: 20px;
            }
            QLabel {
                color: #F5F7FF;
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        
        # Version header
        version_header = QHBoxLayout()
        
        version_label = QLabel(f"v{entry.version}")
        version_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #9B5CFF;")
        
        date_label = QLabel(entry.release_date)
        date_label.setStyleSheet("font-size: 12px; color: #8995AE;")
        
        version_header.addWidget(version_label)
        version_header.addWidget(date_label, 1)
        layout.addLayout(version_header)
        
        # Title
        if entry.title:
            title = QLabel(entry.title)
            title.setStyleSheet("font-size: 14px; font-weight: 600; color: #F5F7FF; margin-top: 4px;")
            layout.addWidget(title)
        
        # Features
        if entry.features:
            features_label = QLabel("🚀 New Features")
            features_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #36D399; margin-top: 8px;")
            layout.addWidget(features_label)
            
            for feature in entry.features:
                feature_label = QLabel(f"• {feature}")
                feature_label.setStyleSheet("font-size: 13px; color: #E5E7EB; margin-left: 8px;")
                feature_label.setWordWrap(True)
                layout.addWidget(feature_label)
        
        # Improvements
        if entry.improvements:
            improvements_label = QLabel("⚡ Improvements")
            improvements_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #60A5FA; margin-top: 8px;")
            layout.addWidget(improvements_label)
            
            for improvement in entry.improvements:
                imp_label = QLabel(f"• {improvement}")
                imp_label.setStyleSheet("font-size: 13px; color: #E5E7EB; margin-left: 8px;")
                imp_label.setWordWrap(True)
                layout.addWidget(imp_label)
        
        # Bug fixes
        if entry.bug_fixes:
            fixes_label = QLabel("🔧 Bug Fixes")
            fixes_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #A78BFA; margin-top: 8px;")
            layout.addWidget(fixes_label)
            
            for fix in entry.bug_fixes:
                fix_label = QLabel(f"• {fix}")
                fix_label.setStyleSheet("font-size: 13px; color: #E5E7EB; margin-left: 8px;")
                fix_label.setWordWrap(True)
                layout.addWidget(fix_label)
        
        return widget
    
    def apply_styles(self):
        """Apply global styles."""
        self.setStyleSheet("""
            QDialog {
                background: #0a0a0f;
            }
        """)
    
    @staticmethod
    def show_changelog(current_version: str, parent=None):
        """Static method to show the changelog dialog."""
        dialog = ChangelogDialog(current_version, parent)
        dialog.exec()