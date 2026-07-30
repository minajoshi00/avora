"""
AVORA Feedback UI

Provides feedback, bug report, and feature request dialogs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import (
    Qt,
    Signal,
)

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app_paths import APP_DATA_DIR
from changelog import get_changelog_manager


class FeedbackDialog(QDialog):
    """Dialog for submitting general feedback."""
    
    submitted = Signal(dict)
    
    def __init__(
        self,
        app_version: str,
        parent=None,
    ):
        super().__init__(parent)
        
        self.app_version = app_version
        self.rating = 0
        
        self.setWindowTitle("Send Feedback")
        self.setMinimumSize(500, 400)
        
        self.build_ui()
        self.apply_styles()
    
    def build_ui(self):
        """Build the feedback UI."""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("FeedbackHeader")
        header.setStyleSheet("""
            QWidget#FeedbackHeader {
                background: #1a1a2e;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        title = QLabel("💬 How is AVORA working for you?")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        
        header_layout.addWidget(title)
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
        
        # Star rating
        rating_label = QLabel("Overall Rating")
        rating_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #F5F7FF;")
        content_layout.addWidget(rating_label)
        
        self.rating_container = QWidget()
        rating_layout = QHBoxLayout(self.rating_container)
        rating_layout.setSpacing(8)
        rating_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stars = []
        for i in range(1, 6):
            star = QPushButton("☆")
            star.setFixedSize(36, 36)
            star.setCursor(Qt.CursorShape.PointingHandCursor)
            star.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    font-size: 24px;
                    color: #4B5563;
                }
                QPushButton:hover {
                    color: #FBBF24;
                }
            """)
            star.clicked.connect(lambda checked, rating=i: self.set_rating(rating))
            rating_layout.addWidget(star)
            self.stars.append(star)
        
        rating_layout.addStretch()
        content_layout.addWidget(self.rating_container)
        
        # Comments
        comments_label = QLabel("Comments (optional)")
        comments_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #F5F7FF; margin-top: 16px;")
        content_layout.addWidget(comments_label)
        
        self.comments = QTextEdit()
        self.comments.setPlaceholderText("Tell us what you think...")
        self.comments.setStyleSheet("""
            QTextEdit {
                background: #111827;
                border: 1px solid #24324D;
                border-radius: 12px;
                padding: 12px;
                color: #F5F7FF;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 1px solid #9B5CFF;
            }
        """)
        self.comments.setFixedHeight(120)
        content_layout.addWidget(self.comments)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)
        
        # Footer
        footer = QWidget()
        footer.setObjectName("FeedbackFooter")
        footer.setStyleSheet("""
            QWidget#FeedbackFooter {
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
            QPushButton[secondary="true"] {
                background: transparent;
                border: 1px solid #24324D;
                color: #8995AE;
            }
            QPushButton[secondary="true"]:hover {
                background: #111827;
                color: #F5F7FF;
            }
        """)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(30, 15, 30, 15)
        footer_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setProperty("secondary", "true")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        submit_button = QPushButton("Submit Feedback")
        submit_button.clicked.connect(self.submit)
        submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        footer_layout.addWidget(cancel_button)
        footer_layout.addWidget(submit_button)
        root_layout.addWidget(footer)
    
    def set_rating(self, rating: int):
        """Set the star rating."""
        self.rating = rating
        for i, star in enumerate(self.stars):
            if i < rating:
                star.setText("★")
                star.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        font-size: 24px;
                        color: #FBBF24;
                    }
                """)
            else:
                star.setText("☆")
                star.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        font-size: 24px;
                        color: #4B5563;
                    }
                """)
    
    def submit(self):
        """Submit the feedback."""
        if self.rating == 0:
            return
        
        feedback_data = {
            'rating': self.rating,
            'comments': self.comments.toPlainText(),
            'type': 'general',
            'app_version': self.app_version,
            'timestamp': datetime.now().isoformat(),
        }
        
        self.submitted.emit(feedback_data)
        self.accept()
    
    def apply_styles(self):
        """Apply global styles."""
        self.setStyleSheet("""
            QDialog {
                background: #0a0a0f;
            }
        """)


class BugReportDialog(QDialog):
    """Dialog for submitting bug reports."""
    
    submitted = Signal(dict)
    
    def __init__(
        self,
        app_version: str,
        os: str,
        parent=None,
    ):
        super().__init__(parent)
        
        self.app_version = app_version
        self.os = os
        
        self.setWindowTitle("Report a Bug")
        self.setMinimumSize(550, 450)
        
        self.build_ui()
        self.apply_styles()
    
    def build_ui(self):
        """Build the bug report UI."""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("BugReportHeader")
        header.setStyleSheet("""
            QWidget#BugReportHeader {
                background: #1a1a2e;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        title = QLabel("🐛 Report a Bug")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        
        header_layout.addWidget(title)
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
        
        # Error message
        error_label = QLabel("Error Message (if any)")
        error_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #F5F7FF;")
        content_layout.addWidget(error_label)
        
        self.error_input = QLineEdit()
        self.error_input.setPlaceholderText("Paste any error message here...")
        self.error_input.setStyleSheet("""
            QLineEdit {
                background: #111827;
                border: 1px solid #24324D;
                border-radius: 10px;
                padding: 10px 14px;
                color: #F5F7FF;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #9B5CFF;
            }
        """)
        content_layout.addWidget(self.error_input)
        
        # Description
        desc_label = QLabel("What happened?")
        desc_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #F5F7FF; margin-top: 16px;")
        content_layout.addWidget(desc_label)
        
        self.description = QTextEdit()
        self.description.setPlaceholderText("Describe the bug and steps to reproduce it...")
        self.description.setStyleSheet("""
            QTextEdit {
                background: #111827;
                border: 1px solid #24324D;
                border-radius: 12px;
                padding: 12px;
                color: #F5F7FF;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 1px solid #9B5CFF;
            }
        """)
        self.description.setFixedHeight(150)
        content_layout.addWidget(self.description)
        
        # Screenshot placeholder
        screenshot_label = QLabel("Screenshot (coming soon)")
        screenshot_label.setStyleSheet("font-size: 12px; color: #6B7280; font-style: italic; margin-top: 8px;")
        content_layout.addWidget(screenshot_label)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)
        
        # Footer
        footer = QWidget()
        footer.setObjectName("BugReportFooter")
        footer.setStyleSheet("""
            QWidget#BugReportFooter {
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
            QPushButton[secondary="true"] {
                background: transparent;
                border: 1px solid #24324D;
                color: #8995AE;
            }
            QPushButton[secondary="true"]:hover {
                background: #111827;
                color: #F5F7FF;
            }
        """)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(30, 15, 30, 15)
        footer_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setProperty("secondary", "true")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        submit_button = QPushButton("Submit Report")
        submit_button.clicked.connect(self.submit)
        submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        footer_layout.addWidget(cancel_button)
        footer_layout.addWidget(submit_button)
        root_layout.addWidget(footer)
    
    def submit(self):
        """Submit the bug report."""
        report = {
            'app_version': self.app_version,
            'os': self.os,
            'error_message': self.error_input.text().strip(),
            'comments': self.description.toPlainText().strip(),
            'timestamp': datetime.now().isoformat(),
        }
        
        self.submitted.emit(report)
        self.accept()
    
    def apply_styles(self):
        """Apply global styles."""
        self.setStyleSheet("""
            QDialog {
                background: #0a0a0f;
            }
        """)


class FeatureRequestDialog(QDialog):
    """Dialog for submitting feature requests."""
    
    submitted = Signal(dict)
    
    def __init__(
        self,
        app_version: str,
        parent=None,
    ):
        super().__init__(parent)
        
        self.app_version = app_version
        
        self.setWindowTitle("Feature Request")
        self.setMinimumSize(500, 400)
        
        self.build_ui()
        self.apply_styles()
    
    def build_ui(self):
        """Build the feature request UI."""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("FeatureRequestHeader")
        header.setStyleSheet("""
            QWidget#FeatureRequestHeader {
                background: #1a1a2e;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        title = QLabel("💡 Suggest a Feature")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        
        header_layout.addWidget(title)
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
        
        # Title
        title_label = QLabel("Feature Title")
        title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #F5F7FF;")
        content_layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("What feature would you like to see?")
        self.title_input.setStyleSheet("""
            QLineEdit {
                background: #111827;
                border: 1px solid #24324D;
                border-radius: 10px;
                padding: 10px 14px;
                color: #F5F7FF;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #9B5CFF;
            }
        """)
        content_layout.addWidget(self.title_input)
        
        # Description
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #F5F7FF; margin-top: 16px;")
        content_layout.addWidget(desc_label)
        
        self.description = QTextEdit()
        self.description.setPlaceholderText("Describe your feature idea in detail...")
        self.description.setStyleSheet("""
            QTextEdit {
                background: #111827;
                border: 1px solid #24324D;
                border-radius: 12px;
                padding: 12px;
                color: #F5F7FF;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 1px solid #9B5CFF;
            }
        """)
        self.description.setFixedHeight(150)
        content_layout.addWidget(self.description)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)
        
        # Footer
        footer = QWidget()
        footer.setObjectName("FeatureRequestFooter")
        footer.setStyleSheet("""
            QWidget#FeatureRequestFooter {
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
            QPushButton[secondary="true"] {
                background: transparent;
                border: 1px solid #24324D;
                color: #8995AE;
            }
            QPushButton[secondary="true"]:hover {
                background: #111827;
                color: #F5F7FF;
            }
        """)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(30, 15, 30, 15)
        footer_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setProperty("secondary", "true")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        submit_button = QPushButton("Submit Request")
        submit_button.clicked.connect(self.submit)
        submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        footer_layout.addWidget(cancel_button)
        footer_layout.addWidget(submit_button)
        root_layout.addWidget(footer)
    
    def submit(self):
        """Submit the feature request."""
        title = self.title_input.text().strip()
        if not title:
            return
        
        request = {
            'title': title,
            'description': self.description.toPlainText().strip(),
            'date': datetime.now().isoformat(),
            'app_version': self.app_version,
        }
        
        self.submitted.emit(request)
        self.accept()
    
    def apply_styles(self):
        """Apply global styles."""
        self.setStyleSheet("""
            QDialog {
                background: #0a0a0f;
            }
        """)