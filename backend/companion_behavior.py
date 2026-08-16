"""
============================================================
        COMPANION BEHAVIOR CONTROLLER
============================================================

Manages the companion's interactive behavior:
  - Character click detection
  - Floating mini chat bubble (fully independent)
  - Click greetings (context-aware)
  - Welcome-back detection
  - Anti-annoyance for interactions
  - Repeated click playful reactions
  - Animated speech bubbles near character

Architecture:
  - CompanionBehaviorController: Main controller
  - MiniChatBubble: Floating chat widget
  - MiniChatWorker: Background AI worker
  - CompanionSpeechBubble: Small animated contextual bubble
============================================================
"""

import math
import random
import time
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QThread, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QApplication,
    QScrollArea
)
from PySide6.QtGui import QColor, QFont, QPainter


# =============================================================
# MINI CHAT WORKER
# =============================================================

class MiniChatWorker(QThread):
    """Background worker for mini chat AI responses."""
    response_ready = Signal(str)
    response_error = Signal(str)

    def __init__(self, message: str, parent=None, attachments: Optional[list] = None):
        super().__init__(parent)
        self.message = str(message)
        self.attachments = attachments or []

    def run(self):
        try:
            import sys
            import os
            project_root = os.path.dirname(os.path.abspath(__file__))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from ai_logic import process_message
            reply = process_message(self.message, self.attachments)
            if reply:
                self.response_ready.emit(str(reply))
            else:
                self.response_error.emit("No response generated.")
        except Exception as e:
            self.response_error.emit(f"Error: {str(e)}")


# =============================================================
# MINI CHAT BUBBLE
# =============================================================

class MiniChatBubble(QWidget):
    """
    Beautiful floating mini chat bubble that appears near the character.
    Completely independent mini-chat with its own AI calls.
    """
    closed = Signal()
    message_sent = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 420)
        self.messages = []
        self.worker = None
        self._thinking_widget = None
        self._setup_ui()

    def _setup_ui(self):
        self.container = QFrame(self)
        self.container.setObjectName("MiniChatContainer")
        self.container.setStyleSheet("""
            QFrame#MiniChatContainer {
                background: rgba(18, 18, 32, 245);
                border: 1px solid rgba(139, 122, 255, 0.35);
                border-radius: 20px;
            }
            QLineEdit {
                background: rgba(38, 38, 58, 210);
                border: 1px solid rgba(139, 122, 255, 0.45);
                border-radius: 12px;
                padding: 9px 14px;
                color: #F5F5F5;
                font-size: 12px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B7AFF, stop:1 #6C63FF);
                border: none;
                border-radius: 12px;
                padding: 9px 16px;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9E91FF, stop:1 #817AFF);
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        self.char_status = QLabel("✧ Avora")
        self.char_status.setStyleSheet("font-weight: 700; font-size: 13px; color: #8B7AFF;")
        header.addWidget(self.char_status)
        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                border: none; border-radius: 12px;
                padding: 0px; font-size: 11px; color: #A0A0B5;
            }
            QPushButton:hover { background: rgba(255,255,255,0.18); color: #FFFFFF; }
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Scrollable messages area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area, 1)

        input_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type something...")
        self.input_box.returnPressed.connect(self._send_message)
        self.input_box.setFixedHeight(38)

        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedHeight(38)
        self.send_btn.clicked.connect(self._send_message)

        input_row.addWidget(self.input_box, 1)
        input_row.addWidget(self.send_btn)
        layout.addLayout(input_row)

        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.container.setGraphicsEffect(shadow)

    def show_near(self, parent_widget, global_pos):
        screen = parent_widget.screen() or QApplication.primaryScreen()
        geo = screen.availableGeometry()

        x = global_pos.x() - self.width() // 2
        y = global_pos.y() - self.height() - 24

        x = max(geo.left() + 10, min(geo.right() - self.width() - 10, x))
        y = max(geo.top() + 10, min(geo.bottom() - self.height() - 10, y))

        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(100, lambda: self.input_box.setFocus())

    def add_message(self, text, is_user=False):
        if not text:
            return

        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setMaximumWidth(220)
        msg.setStyleSheet(
            f"background: {'rgba(139, 122, 255, 0.22)' if is_user else 'rgba(38, 38, 58, 190)'};"
            f"border-radius: 12px; padding: 7px 11px; color: #F5F5F5;"
        )
        msg.setAlignment(Qt.AlignmentFlag.AlignLeft)

        container = QWidget()
        cl = QHBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(msg)
        if is_user:
            cl.setAlignment(msg, Qt.AlignmentFlag.AlignRight)
            msg.setStyleSheet(
                "background: rgba(139, 122, 255, 0.28);"
                "border-radius: 12px; padding: 7px 11px; color: #FFFFFF;"
            )

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        self.messages.append((text, is_user))

        # Scroll to bottom
        QTimer.singleShot(50, lambda: self._scroll_to_bottom())

    def _scroll_to_bottom(self):
        try:
            scrollbar = self.scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception:
            pass

    def add_thinking(self):
        if self._thinking_widget is not None:
            return

        thinking = QLabel("Thinking...")
        thinking.setStyleSheet(
            "background: rgba(38, 38, 58, 190);"
            "border-radius: 12px; padding: 7px 11px; color: #A0A0B5;"
            "font-style: italic;"
        )
        thinking.setMaximumWidth(120)

        container = QWidget()
        cl = QHBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(thinking)
        cl.setAlignment(thinking, Qt.AlignmentFlag.AlignLeft)

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        self._thinking_widget = container
        QTimer.singleShot(50, lambda: self._scroll_to_bottom())

    def remove_thinking(self):
        if self._thinking_widget is not None:
            try:
                self._thinking_widget.deleteLater()
            except Exception:
                pass
            self._thinking_widget = None

    def add_error(self, error_text):
        self.remove_thinking()
        error = QLabel(f"Error: {error_text}")
        error.setWordWrap(True)
        error.setMaximumWidth(220)
        error.setStyleSheet(
            "background: rgba(255, 80, 80, 0.2);"
            "border-radius: 12px; padding: 7px 11px; color: #FF6B6B;"
        )
        error.setAlignment(Qt.AlignmentFlag.AlignLeft)

        container = QWidget()
        cl = QHBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(error)

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        self.messages.append((f"Error: {error_text}", False))
        QTimer.singleShot(50, lambda: self._scroll_to_bottom())

    def _send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return

        # Clear input and add user message locally
        self.input_box.clear()
        self.add_message(text, is_user=True)

        # Show thinking state
        self.add_thinking()
        self.send_btn.setEnabled(False)
        self.input_box.setEnabled(False)

        # Emit for controller to handle AI call
        self.message_sent.emit(text)

    def receive_reply(self, text):
        self.remove_thinking()
        self.add_message(text, is_user=False)
        self.send_btn.setEnabled(True)
        self.input_box.setEnabled(True)
        self.input_box.setFocus()

    def receive_error(self, error_text):
        self.remove_thinking()
        self.add_error(error_text)
        self.send_btn.setEnabled(True)
        self.input_box.setEnabled(True)
        self.input_box.setFocus()

    def set_processing(self, processing: bool):
        self.send_btn.setEnabled(not processing)
        self.input_box.setEnabled(not processing)

    def closeEvent(self, event):
        self.remove_thinking()
        if self.worker is not None:
            try:
                self.worker.quit()
                self.worker.wait(500)
            except Exception:
                pass
            self.worker = None
        self.closed.emit()
        super().closeEvent(event)


# =============================================================
# COMPANION SPEECH BUBBLE
# =============================================================

class CompanionSpeechBubble(QWidget):
    """
    Small animated speech bubble that appears near the character.
    Shows proactive contextual messages.
    Clicking opens the mini companion chat.
    """
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._text = ""
        self._opacity = 0.0
        self._target_opacity = 0.0
        self._hide_timer = None
        self._fade_anim = None
        self._setup_ui()

    def _setup_ui(self):
        self.container = QFrame(self)
        self.container.setObjectName("SpeechBubbleContainer")
        self.container.setStyleSheet("""
            QFrame#SpeechBubbleContainer {
                background: rgba(18, 18, 32, 235);
                border: 1px solid rgba(139, 122, 255, 0.45);
                border-radius: 16px;
            }
            QLabel {
                color: #F5F5F5;
                font-size: 12px;
                font-weight: 500;
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumWidth(220)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.message_label)

        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.container.setGraphicsEffect(shadow)

    def show_message(self, text: str, parent_widget, char_global_pos: QPoint, duration_ms: int = 5000):
        if not text:
            return

        self._text = text
        self.message_label.setText(text)
        self.message_label.adjustSize()

        width = max(120, min(240, self.message_label.width() + 24))
        height = self.message_label.height() + 28
        height = min(height, 160)

        self.setFixedSize(width, height)
        self.container.setFixedSize(width, height)

        screen = parent_widget.screen() or QApplication.primaryScreen()
        geo = screen.availableGeometry()

        x = char_global_pos.x() - width // 2
        y = char_global_pos.y() - height - 28

        x = max(geo.left() + 10, min(geo.right() - width - 10, x))
        y = max(geo.top() + 10, min(geo.bottom() - height - 10, y))

        self.move(x, y)
        self.show()
        self.raise_()

        if self._fade_anim is None:
            self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
            self._fade_anim.setDuration(280)
            self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._fade_anim.stop()
        self.setWindowOpacity(0.0)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

        if self._hide_timer is not None:
            self._hide_timer.stop()
        self._hide_timer = QTimer()
        self._hide_timer.timeout.connect(self.hide_bubble)
        self._hide_timer.start(duration_ms)

    def hide_bubble(self):
        if self._fade_anim is not None:
            try:
                self._fade_anim.finished.disconnect(self._do_hide)
            except Exception:
                pass
            self._fade_anim.stop()
            self._fade_anim.setStartValue(self.windowOpacity())
            self._fade_anim.setEndValue(0.0)
            self._fade_anim.finished.connect(self._do_hide)
            self._fade_anim.start()
        else:
            self._do_hide()

    def _do_hide(self):
        try:
            self.hide()
        except Exception:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def hideEvent(self, event):
        if self._hide_timer is not None:
            self._hide_timer.stop()
            self._hide_timer = None
        super().hideEvent(event)


# =============================================================
# COMPANION BEHAVIOR CONTROLLER
# =============================================================

class CompanionBehaviorController:
    """
    Central controller for companion interactive behavior.
    Manages click handling, mini chat bubble, and proactive messages.
    """

    def __init__(self, main_window):
        self.main = main_window
        self.character = getattr(main_window, 'character', None)
        self.companion = getattr(main_window, 'companion', None)
        self.mini_chat: Optional[MiniChatBubble] = None
        self.speech_bubble: Optional[CompanionSpeechBubble] = None
        self.click_count = 0
        self.last_click_time = 0.0
        self.click_reset_time = 0.0
        self._last_click_greeting_time = 0.0
        self._click_greeting_cooldown = 8.0

    # =========================================================
    # LIFECYCLE
    # =========================================================

    def start(self):
        pass

    def stop(self):
        if self.mini_chat is not None:
            try:
                self.mini_chat.close()
            except Exception:
                pass
            self.mini_chat = None
        if self.speech_bubble is not None:
            try:
                self.speech_bubble.close()
            except Exception:
                pass
            self.speech_bubble = None

    def show_speech_bubble(self, message: str, duration_ms: int = 5000):
        """Show a small animated speech bubble near the character."""
        if self.character is None or not message:
            return
        try:
            if self.speech_bubble is None:
                self.speech_bubble = CompanionSpeechBubble()
                self.speech_bubble.clicked.connect(self._on_speech_bubble_clicked)

            char_pos = self.character.pos()
            global_pos = self.character.mapToGlobal(QPoint(char_pos.x(), char_pos.y()))
            self.speech_bubble.show_message(message, self.main, global_pos, duration_ms)
        except Exception:
            pass

    def hide_speech_bubble(self):
        """Hide the speech bubble immediately."""
        if self.speech_bubble is not None:
            try:
                self.speech_bubble.hide_bubble()
            except Exception:
                pass

    def _on_speech_bubble_clicked(self):
        """Open mini companion chat when speech bubble is clicked."""
        self._open_mini_chat(clicked_now=True)

    # =========================================================
    # CHARACTER CLICK
    # =========================================================

    def on_character_clicked(self):
        """Called when user clicks the character widget."""
        if self.character is None or not self.character.isEnabled():
            return

        now = time.time()

        if now - self.click_reset_time > 6.0:
            self.click_count = 0
            self.click_reset_time = now

        if now - self.last_click_time > 2.0:
            self.click_count = 1
        else:
            self.click_count += 1
        self.last_click_time = now

        if self.click_count >= 4:
            self._handle_rapid_clicks()
            self.click_count = 0
            return

        # Update companion mood
        if self.companion is not None:
            idle_minutes = 0.0
            if self.main.activity_monitor is not None:
                idle_minutes = self.main.activity_monitor.idle_minutes
            if idle_minutes > 2:
                self.companion.on_user_returned(idle_minutes)
            else:
                self.companion.on_user_clicked()

        # Toggle mini chat only - never touch main chat
        if self.mini_chat is not None and self.mini_chat.isVisible():
            self.mini_chat.close()
        else:
            self._open_mini_chat(clicked_now=True)

        self._playful_click_reaction()

    def _playful_click_reaction(self):
        if self.character is None:
            return
        try:
            self.character.react("happy", {"message": ""})
            QTimer.singleShot(350, lambda: self.character.react("idle", {}))
        except Exception:
            pass

    def _handle_rapid_clicks(self):
        """Playful response when user rapidly clicks the character."""
        responses = [
            "Hey hey! I'm here! 😂",
            "Okay okay, I get it! 👋",
            "You're persistent! I like it 😄",
            "Stop poking me! ...just kidding, click again! 👀",
            "BRO chill 😭 I'm listening!",
            "Ok ok ok, what do you need? 😂",
        ]
        msg = random.choice(responses)
        self._show_character_notification(msg, 2500)
        if self.mini_chat and self.mini_chat.isVisible():
            self.mini_chat.receive_reply(msg)

    # =========================================================
    # MINI CHAT BUBBLE
    # =========================================================

    def _open_mini_chat(self, clicked_now=False):
        if self.character is None:
            return

        if self.mini_chat is None:
            self.mini_chat = MiniChatBubble()
            self.mini_chat.message_sent.connect(self._on_mini_chat_message)
            self.mini_chat.closed.connect(self._on_mini_chat_closed)

            # Greeting
            greeting = self._generate_click_greeting()
            if greeting:
                self.mini_chat.add_message(greeting, is_user=False)

        char_pos = self.character.pos()
        global_pos = self.character.mapToGlobal(QPoint(char_pos.x(), char_pos.y() + 20))
        self.mini_chat.show_near(self.main, global_pos)

        if clicked_now:
            self._playful_click_reaction()

    def _on_mini_chat_message(self, text):
        """Handle message from mini chat - call AI directly, never touch main chat."""
        if not text:
            return

        if self.companion is not None:
            self.companion.on_user_message(text)

        # Create worker for AI call
        if self.mini_chat is None:
            return

        self.mini_chat.worker = MiniChatWorker(text)
        self.mini_chat.worker.response_ready.connect(
            lambda reply: self._on_mini_chat_reply(reply)
        )
        self.mini_chat.worker.response_error.connect(
            lambda err: self._on_mini_chat_error(err)
        )
        self.mini_chat.worker.finished.connect(
            lambda: self._on_mini_chat_worker_done()
        )
        self.mini_chat.worker.start()

    def _on_mini_chat_reply(self, reply):
        if self.mini_chat is not None and self.mini_chat.isVisible():
            self.mini_chat.receive_reply(reply)
            if self.companion is not None:
                self.companion.on_ai_response(str(reply))

    def _on_mini_chat_error(self, error_text):
        if self.mini_chat is not None and self.mini_chat.isVisible():
            self.mini_chat.receive_error(error_text)

    def _on_mini_chat_worker_done(self):
        if self.mini_chat is not None:
            try:
                self.mini_chat.worker = None
            except Exception:
                pass

    def _on_mini_chat_closed(self):
        self.mini_chat = None

    # =========================================================
    # CONTEXT-AWARE DIALOGUE
    # =========================================================

    def _generate_click_greeting(self):
        now = datetime.now()
        hour = now.hour
        time_greeting = "Hey"
        if 5 <= hour < 12:
            time_greeting = "Morning"
        elif 12 <= hour < 17:
            time_greeting = "Afternoon"
        elif 17 <= hour < 22:
            time_greeting = "Evening"

        observation = None
        if self.companion:
            observation = self.companion.get_last_observation()

        if observation:
            idle_mins = observation.get("idle_minutes", 0)

            # Only react to being away
            if idle_mins > 15:
                return "You disappeared 👀 everything okay?"

            if idle_mins > 3:
                return "Welcome back 😄"

            # Check current activity from screen awareness
            current_activity = observation.get("activity_type", "")
            if hasattr(current_activity, "value"):
                current_activity = current_activity.value
            
            activity_str = str(current_activity).lower()
            
            # Context-aware greetings based on what they're doing
            if activity_str == "coding":
                return f"{time_greeting} bro! 👋 Hope the coding's going well."
            elif activity_str == "studying":
                return f"Hey! 😊 How's the studying going?"
            elif activity_str == "gaming":
                return "Hey! 😄 Have fun! I'll stay out of the way."
            elif activity_str == "working":
                return f"{time_greeting}! How's work going?"
            elif activity_str == "reading":
                return f"{time_greeting}! Enjoying what you're reading?"
            elif activity_str == "designing":
                return f"{time_greeting}! How's the design work going?"

        # Default greeting - simple and friendly
        return f"{time_greeting} bro! 👋 Good to see you."

    # =========================================================
    # NOTIFICATIONS
    # =========================================================

    def _show_character_notification(self, message: str, duration: int = 2200):
        """Show a notification on the character."""
        if self.character is None:
            return
        try:
            self.character.show_notification(message, duration=duration)
        except Exception:
            pass
