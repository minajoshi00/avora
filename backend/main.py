# ============================================================
#                     AI FRIEND MAIN APPLICATION
# ============================================================
#
# Main desktop application window for AI Friend.
#
# Features:
#   • PySide6 desktop interface
#   • Gemini/Groq AI logic through ai_logic.py
#   • Voice control
#   • Animated Character
#   • Settings window
#   • Live settings updates
#   • Safe AI worker thread
#   • Conversation reset
#   • Character positioning
#   • Error handling
#   • Safe shutdown
#   • ChatGPT-style microphone (continuous recording)
#   • Image display in chat
#
# ============================================================


from __future__ import annotations


# ============================================================
# STANDARD LIBRARY
# ============================================================

import os
import sys
import traceback
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


# ============================================================
# PY SIDE 6
# ============================================================

from PySide6.QtCore import (
    QEvent,
    QThread,
    QTimer,
    Signal,
    Qt,
)

from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QPixmap,
    QPainter,
)

from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QTextBrowser,
    QFileDialog,
)


# ============================================================
# PROJECT IMPORTS
# ============================================================

from .voice import (
    speak,
    stop_speaking,
    listen,
    listen_start,
    listen_stop,
    is_recording,
)

from .ai_logic import (
    get_ai_response,
)

from .character import (
    Character,
)

from .settings import (
    get_setting,
    set_setting,
    is_voice_enabled,
    is_character_enabled,
    add_settings_listener,
)

from .theme import (
    get_current_theme,
    generate_qss,
    apply_theme_to_app,
    refresh_theme,
    get_current_theme_id,
    add_theme_listener,
    is_dark_mode,
)

from .app_paths import (
    APP_DATA_DIR,
    ICON_PATH,
)

from .app_utils import (
    clean_ai_reply,
    format_status,
    sanitize_user_text,
)

from .skills.markdown_renderer import (
    markdown_to_html,
)

from .skills.chat_worker import (
    StreamingWorker,
    RegenerateWorker,
)

from .activity_monitor import (
    ActivityMonitor,
    ActivityType,
)

from .companion_behavior import (
    CompanionBehaviorController,
)

from .companion_intelligence import (
    CompanionIntelligence,
    CompanionMood,
    UserState,
    InterventionType,
)

from .screen_awareness import (
    ScreenAwareness,
)

from .chat_sidebar import (
    ChatSidebar,
    save_conversations,
    load_conversations,
    generate_title_from_messages,
)


# ============================================================
# AVORA SYSTEMS
# ============================================================

from .avora_safety import (
    initialize as init_safety,
    is_panic,
    trigger_panic,
    clear_panic,
    log_activity,
)

from .avora_hotkey import (
    initialize as init_hotkey,
    stop_hotkey_listener,
)

from .avora_clipboard import (
    initialize as init_clipboard,
    stop_clipboard_monitor,
    get_history as get_clipboard_history,
    search_history as search_clipboard,
    clear_history as clear_clipboard,
)

from .avora_automation import (
    initialize as init_automation,
    create_automation_task,
    execute_automation_task,
    cancel_automation_task,
    get_all_tasks,
)

from .core.bootstrap import (
    get_bootstrap,
)


# ============================================================
# VOICE RECOGNITION WORKER (Proper QThread)
# ============================================================


class VoiceRecognitionWorker(QThread):
    """Proper QThread subclass for speech recognition."""

    result_ready = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        """Run speech recognition in a background thread."""
        try:
            text = listen_stop()
            self.result_ready.emit(text)
        except Exception as error:
            print("[VOICE RECOGNITION ERROR]", error)
            self.result_ready.emit(None)


# ============================================================
# MAIN WINDOW
# ============================================================


class MainWindow(QWidget):

    # Used to control character talking animation.
    character_talking_signal = Signal(bool)

    # Used to marshal companion observations to the main thread safely.
    _activity_changed_signal = Signal(dict)

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        # ====================================================
        # APPLICATION STATE
        # ====================================================

        self.worker = None

        self.settings_window = None

        self.thinking_label = None

        self.is_processing = False

        self.is_closing = False

        self.voice_enabled = bool(
            is_voice_enabled()
        )

        self.character_enabled = bool(
            is_character_enabled()
        )

        self.character = None

        self.status_label = None

        self.compact_character_mode = False

        self.activity_monitor = None
        self.last_proactive_time = 0
        self.proactive_cooldown = 15 * 60

        # Companion Intelligence System
        self.companion = None
        self.companion_timer = None
        self.behavior_controller = None

        # Screen Awareness System
        self.screen_awareness = None

        # Neural background animation
        self.neural_canvas = None
        self.neural_nodes = []
        self.neural_timer = None
        self.mouse_pos = None

        # Chat Sidebar System
        self.chats = []
        self.active_chat_id = None
        self.chat_sidebar = None
        self._updating_chat = False

        self._current_message = None

        # ====================================================
        # SIGNALS
        # ====================================================

        self.character_talking_signal.connect(
            self.character_talking
        )

        # ====================================================
        # WINDOW
        # ====================================================

        self.setWindowTitle(
            "AVORA AI"
        )

        self.setWindowIcon(
            QIcon(
                str(ICON_PATH)
            )
        )

        self.setObjectName(
            "MainWindow"
        )

        self.resize(
            1200,
            800
        )

        self.setMinimumSize(
            950,
            700
        )

        # ====================================================
        # UI
        # ====================================================

        self.apply_styles()

        self.create_neural_background()

        self.create_ui()

        self.load_chats()

        self.create_character()

        # ====================================================
        # SETTINGS LISTENER
        # ====================================================

        try:

            add_settings_listener(
                self.on_setting_changed
            )

        except Exception as error:

            print(
                "SETTINGS LISTENER ERROR:",
                error
            )

        # ====================================================
        # THEME LISTENER
        # ====================================================

        try:

            add_theme_listener(
                self.on_theme_changed
            )

        except Exception as error:

            print(
                "THEME LISTENER ERROR:",
                error
            )

    # ========================================================
    # THEME CHANGE
    # ========================================================

    def on_theme_changed(
        self,
        theme,
    ):

        self.setStyleSheet(
            generate_qss()
        )

        # Refresh character theme colors
        if self.character is not None:

            try:

                self.character.update_theme()

            except Exception as error:

                print(
                    "CHARACTER THEME ERROR:",
                    error
                )

    # ========================================================
    # STYLES
    # ========================================================

    def apply_styles(
        self,
    ):

        self.setStyleSheet(
            generate_qss()
        )

    # ========================================================
    # NEURAL BACKGROUND
    # ========================================================

    def create_neural_background(self):
        """Create an animated neural network background."""
        self.neural_canvas = QWidget(self)
        self.neural_canvas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.neural_canvas.lower()

        # Create neural nodes
        import random
        self.neural_nodes = []
        for i in range(20):
            self.neural_nodes.append({
                "x": random.randint(0, self.width()),
                "y": random.randint(0, self.height()),
                "vx": random.uniform(-0.3, 0.3),
                "vy": random.uniform(-0.3, 0.3),
                "size": random.uniform(2.0, 5.0),
                "opacity": random.uniform(0.3, 0.8),
            })

        self.neural_timer = QTimer()
        self.neural_timer.timeout.connect(self.animate_neural_background)
        self.neural_timer.start(100)  # 10 FPS - smoother, less CPU

    def animate_neural_background(self):
        """Animate neural nodes and repaint."""
        if self.is_closing:
            return

        if not self.neural_canvas or not self.neural_nodes:
            return

        if self.neural_canvas.isHidden() or not self.neural_canvas.isVisible():
            return

        if self.neural_canvas.paintEngine() is None:
            return

        w, h = self.neural_canvas.width(), self.neural_canvas.height()
        if w <= 0 or h <= 0:
            return

        # Update positions
        for node in self.neural_nodes:
            node["x"] += node["vx"]
            node["y"] += node["vy"]

            # Bounce off edges
            if node["x"] < 0 or node["x"] > w:
                node["vx"] *= -1
                node["x"] = max(0, min(w, node["x"]))
            if node["y"] < 0 or node["y"] > h:
                node["vy"] *= -1
                node["y"] = max(0, min(h, node["y"]))

            # Mouse interaction - gentle push
            if self.mouse_pos:
                dx = node["x"] - self.mouse_pos.x()
                dy = node["y"] - self.mouse_pos.y()
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < 150:
                    force = (150 - dist) / 150
                    node["vx"] += dx * force * 0.02
                    node["vy"] += dy * force * 0.02
                    # Clamp velocity
                    max_v = 1.0
                    node["vx"] = max(-max_v, min(max_v, node["vx"]))
                    node["vy"] = max(-max_v, min(max_v, node["vy"]))

        self.neural_canvas.update()

    def paintEvent(self, event):
        """Override paintEvent to draw neural network."""
        super().paintEvent(event)

        if self.is_closing:
            return

        if not self.neural_canvas or not self.neural_nodes:
            return

        if self.neural_canvas.isHidden() or not self.neural_canvas.isVisible():
            return

        if self.neural_canvas.paintEngine() is None:
            return

        try:
            painter = QPainter(self.neural_canvas)
        except Exception:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get theme colors
        theme = get_current_theme()
        is_dark = is_dark_mode()

        node_color = QColor(139, 122, 255)  # Accent color
        connection_color = QColor(139, 122, 255)

        # Draw connections
        max_dist = 180
        painter.setPen(QColor(connection_color.red(), connection_color.green(), connection_color.blue(), 25))
        for i, node1 in enumerate(self.neural_nodes):
            for j, node2 in enumerate(self.neural_nodes):
                if i >= j:
                    continue
                dx = node1["x"] - node2["x"]
                dy = node1["y"] - node2["y"]
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < max_dist:
                    alpha = int(255 * (1 - dist / max_dist) * 0.15)
                    painter.setPen(QColor(connection_color.red(), connection_color.green(), connection_color.blue(), alpha))
                    painter.drawLine(int(node1["x"]), int(node1["y"]), int(node2["x"]), int(node2["y"]))

        # Draw nodes
        painter.setBrush(node_color)
        for node in self.neural_nodes:
            alpha = int(255 * node.get("opacity", 0.5) * 0.6)
            painter.setPen(QColor(node_color.red(), node_color.green(), node_color.blue(), alpha))
            painter.drawEllipse(int(node["x"]), int(node["y"]), int(node["size"]), int(node["size"]))

        painter.end()

    def mouseMoveEvent(self, event):
        """Track mouse position for neural interaction."""
        self.mouse_pos = event.pos()
        super().mouseMoveEvent(event)

    def resizeEvent(self, event):
        """Handle resize."""
        super().resizeEvent(event)
        if self.neural_canvas:
            self.neural_canvas.setGeometry(self.rect())
            # Reinitialize nodes for new size
            import random
            w, h = self.width(), self.height()
            if w > 0 and h > 0:
                for node in self.neural_nodes:
                    node["x"] = random.randint(0, w)
                    node["y"] = random.randint(0, h)

    # ========================================================
    # CREATE UI
    # ========================================================

    def create_ui(
        self,
    ):

        main_layout = QHBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(
            0
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        self.sidebar = QFrame()

        self.sidebar.setObjectName(
            "Sidebar"
        )

        self.sidebar.setFixedWidth(
            290
        )

        self.apply_shadow(
            self.sidebar,
            blur=24,
            offset=0,
            alpha=90,
        )

        sidebar_layout = QVBoxLayout(
            self.sidebar
        )

        sidebar_layout.setContentsMargins(
            18,
            18,
            18,
            16
        )

        sidebar_layout.setSpacing(
            8
        )

        # ====================================================
        # LOGO
        # ====================================================

        logo = QLabel(
            "✦  AVORA"
        )

        logo.setObjectName(
            "Logo"
        )

        logo.setStyleSheet("""
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.5px;
            padding: 5px 0;
        """)

        subtitle = QLabel(
            "Intelligence, redefined."
        )

        subtitle.setObjectName(
            "SubText"
        )

        subtitle.setStyleSheet("""
            font-size: 11px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            font-weight: 500;
        """)

        sidebar_layout.addWidget(
            logo
        )

        sidebar_layout.addWidget(
            subtitle
        )

        sidebar_layout.addSpacing(
            30
        )

        # ====================================================
        # NEW CHAT
        # ====================================================

        self.new_chat_button = QPushButton(
            "＋   New Conversation"
        )

        self.new_chat_button.setObjectName(
            "NewChatButton"
        )

        self.new_chat_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.new_chat_button.clicked.connect(
            self.create_new_chat
        )

        self.new_chat_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B7AFF, stop:1 #6C63FF);
                border: none;
                border-radius: 12px;
                padding: 14px;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9E91FF, stop:1 #817AFF);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6C63FF, stop:1 #5149D8);
            }
        """)

        sidebar_layout.addWidget(
            self.new_chat_button
        )

        # ====================================================
        # VOICE
        # ====================================================

        self.voice_button = QPushButton()

        self.voice_button.setObjectName(
            "VoiceButton"
        )

        self.voice_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.voice_button.clicked.connect(
            self.toggle_voice
        )

        self.update_voice_button()

        sidebar_layout.addWidget(
            self.voice_button
        )

        # ====================================================
        # SETTINGS
        # ====================================================

        self.settings_button = QPushButton(
            "⚙️   Settings"
        )

        self.settings_button.setObjectName(
            "SettingsButton"
        )

        self.settings_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.settings_button.clicked.connect(
            self.open_settings
        )

        sidebar_layout.addWidget(
            self.settings_button
        )

        sidebar_layout.addSpacing(
            10
        )

        # ====================================================
        # CHAT SIDEBAR (RECENT CHATS)
        # ====================================================

        self.chat_sidebar = ChatSidebar(
            self.sidebar
        )

        self.chat_sidebar.chat_selected.connect(
            self.switch_chat
        )

        self.chat_sidebar.new_chat_requested.connect(
            self.create_new_chat
        )

        self.chat_sidebar.chat_deleted.connect(
            self._on_chat_deleted
        )

        sidebar_layout.addWidget(
            self.chat_sidebar,
            1,
        )

        sidebar_layout.addSpacing(
            15
        )

        sidebar_layout.addStretch()

        # ====================================================
        # RIGHT SIDE
        # ====================================================

        right_side = QFrame()

        right_side.setObjectName(
            "RightSide"
        )

        right_layout = QVBoxLayout(
            right_side
        )

        right_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        right_layout.setSpacing(
            0
        )

        # ====================================================
        # HEADER
        # ====================================================

        header = QFrame()

        header.setObjectName(
            "Header"
        )

        header.setFixedHeight(
            70
        )

        header_layout = QHBoxLayout(
            header
        )

        header_layout.setContentsMargins(
            25,
            0,
            25,
            0
        )

        header_title = QLabel(
            "AVORA"
        )

        header_title.setObjectName(
            "HeaderTitle"
        )

        header_status = QLabel(
            "● Ready"
        )

        header_status.setObjectName(
            "HeaderStatus"
        )

        self.status_label = header_status

        header_layout.addWidget(
            header_title
        )

        header_layout.addSpacing(
            10
        )

        header_layout.addWidget(
            header_status
        )

        header_layout.addStretch()

        right_layout.addWidget(
            header
        )

        # ====================================================
        # CHAT AREA
        # ====================================================

        self.chat_area = QScrollArea()

        self.chat_area.setObjectName(
            "ChatArea"
        )

        self.chat_area.setWidgetResizable(
            True
        )

        self.chat_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.chat_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.message_widget = QWidget()

        self.message_widget.setObjectName(
            "MessageArea"
        )

        self.message_layout = QVBoxLayout(
            self.message_widget
        )

        self.message_layout.setContentsMargins(
            36,
            24,
            36,
            24
        )

        self.message_layout.setSpacing(
            18
        )

        self.message_layout.addStretch()

        self.chat_area.setWidget(
            self.message_widget
        )

        right_layout.addWidget(
            self.chat_area,
            1
        )

        # ====================================================
        # INPUT
        # ====================================================

        input_outer = QFrame()

        input_outer.setFixedHeight(
            96
        )

        input_layout = QHBoxLayout(
            input_outer
        )

        input_layout.setContentsMargins(
            18,
            12,
            18,
            18
        )

        self.input_container = QFrame()

        self.input_container.setObjectName(
            "InputContainer"
        )

        self.apply_shadow(
            self.input_container,
            blur=18,
            offset=0,
            alpha=100,
        )

        input_container_layout = QHBoxLayout(
            self.input_container
        )

        input_container_layout.setContentsMargins(
            10,
            6,
            10,
            6
        )

        self.user_input = QLineEdit()

        self.user_input.setObjectName(
            "InputBox"
        )

        self.user_input.setPlaceholderText(
            "Message your AI Friend..."
        )

        self.user_input.returnPressed.connect(
            self.send_message
        )

        self.send_button = QPushButton(
            "➤"
        )

        self.send_button.setObjectName(
            "SendButton"
        )

        self.send_button.setFixedSize(
            48,
            42
        )

        self.send_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.send_button.clicked.connect(
            self.send_message
        )

        input_container_layout.addWidget(
            self.user_input,
            1
        )

        input_container_layout.addWidget(
            self.send_button
        )

        self.attach_button = QPushButton(
            "📎"
        )

        self.attach_button.setObjectName(
            "AttachButton"
        )

        self.attach_button.setFixedSize(
            42,
            42
        )

        self.attach_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.attach_button.clicked.connect(
            self._attach_file
        )

        self.attached_files = []

        input_container_layout.addWidget(
            self.attach_button
        )

        self.mic_button = QPushButton(
            "🎤"
        )

        self.mic_button.setObjectName(
            "MicButton"
        )

        self.mic_button.setFixedSize(
            48,
            42
        )

        self.mic_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.mic_button.clicked.connect(
            self.toggle_voice_input
        )

        self.is_listening = False

        input_container_layout.addWidget(
            self.mic_button
        )


        input_layout.addWidget(
            self.input_container
        )

        right_layout.addWidget(
            input_outer
        )

        # ====================================================
        # ADD TO WINDOW
        # ====================================================

        main_layout.addWidget(
            self.sidebar
        )

        main_layout.addWidget(
            right_side,
            1
        )

        # ====================================================
        # WELCOME MESSAGE
        # ====================================================

        self.update_status(
            "ready",
            "Ready",
        )

        self.add_ai_message_rich(
            "Hey bro! 👋 Good to see you."
        )

    # ========================================================
    # STYLES
    # ========================================================

    def apply_shadow(
        self,
        widget,
        blur=24,
        offset=0,
        alpha=120,
    ):

        effect = QGraphicsDropShadowEffect(
            widget
        )

        effect.setBlurRadius(
            blur
        )

        effect.setOffset(
            0,
            offset,
        )

        effect.setColor(
            QColor(
                0,
                0,
                0,
                alpha,
            )
        )

        widget.setGraphicsEffect(
            effect
        )

        return effect

    # ========================================================
    # CHARACTER
    # ========================================================

    def create_character(
        self,
    ):

        if not self.character_enabled:

            self.character = None

            return

        try:

            self.character = Character(
                parent=self
            )

        except TypeError:

            try:

                self.character = Character()

                self.character.setParent(
                    self
                )

            except Exception as error:

                print(
                    "CHARACTER CREATION ERROR:",
                    error
                )

                self.character = None

                return

        except Exception as error:

            print(
                "CHARACTER CREATION ERROR:",
                error
            )

            self.character = None

            return

        self.character.setParent(
            self.sidebar
        )

        self.character.show()

        self.character.raise_()

        self.character.clicked.connect(
            self._on_character_clicked
        )

        self.character_talking_signal.connect(
            self.character_talking
        )

        self._activity_changed_signal.connect(
            self._apply_companion_observation
        )

        self.position_character()

    # ========================================================
    # ACTIVITY MONITOR
    # ========================================================

    def start_activity_monitor(self):
        """Start the activity monitor for proactive behavior."""
        try:
            self.activity_monitor = ActivityMonitor(
                check_interval=5.0,
                idle_threshold_minutes=3.0,
            )
            self.activity_monitor.add_listener(
                self.on_activity_changed
            )
            self.activity_monitor.start()
            print("[ACTIVITY] Monitor started")
        except Exception as e:
            print("[ACTIVITY] Monitor failed to start:", e)

    def stop_activity_monitor(self):
        """Stop the activity monitor."""
        if self.activity_monitor:
            try:
                self.activity_monitor.stop()
                print("[ACTIVITY] Monitor stopped")
            except Exception as e:
                print("[ACTIVITY] Monitor stop error:", e)

    def on_activity_changed(self, activity, title):
        """Handle activity change from monitor."""
        try:
            # Don't process while busy
            if self.is_processing or self.is_listening:
                return

            # Feed activity into Companion Intelligence
            if self.companion is not None:
                personality = get_setting("personality.current_personality", "friendly")
                self.companion.set_personality(personality)

                # Run the companion cycle
                activity_name = activity.value if hasattr(activity, 'value') else str(activity)
                idle_minutes = self.activity_monitor.idle_minutes if self.activity_monitor else 0.0
                process_name = self.activity_monitor.process_name if self.activity_monitor else ""

                observation = self.companion.cycle(
                    activity_type=activity_name,
                    window_title=title,
                    process_name=process_name,
                    idle_minutes=idle_minutes,
                    is_processing=self.is_processing,
                    is_voice_active=self.is_listening,
                )

                # Marshal observation to main thread for UI updates
                self._activity_changed_signal.emit(observation if isinstance(observation, dict) else {})
        except Exception as e:
            print("[COMPANION] Cycle error:", e)

    def _apply_companion_observation(self, observation: dict):
        """Apply companion observation to character and UI."""
        if not observation:
            return

        # 1. Update character emotion
        if self.character is not None:
            mood_value = observation.get("mood", CompanionMood.NEUTRAL).value if hasattr(
                observation.get("mood"), "value") else str(observation.get("mood", "neutral"))
            intensity = observation.get("mood_intensity", 0.5)

            # Check for intervention
            intervention = observation.get("intervention")
            if intervention:
                char_emotion = intervention.get("character_emotion", "idle")
                message = intervention.get("message")

                if message and observation.get("silent_mode") is False:
                    self.character_call("react_naturally", mood_value, intensity,
                                       False, message)
                    if self.behavior_controller is not None:
                        self.behavior_controller.show_speech_bubble(message)
                else:
                    # Silent awareness - just change expression
                    self.character_call("react_naturally", mood_value, intensity,
                                       True, None)
            else:
                # No intervention - just update expression silently
                self.character_call("react_naturally", mood_value, intensity,
                                   True, None)

            # Handle achievements
            achievement = observation.get("new_achievement")
            if achievement and self.character:
                title = achievement.get("title", "")
                desc = achievement.get("description", "")
                msg = f"🎉 {title} - {desc}"
                self.character_call("react_naturally", "happy", 0.8, False, msg)
                if self.behavior_controller is not None:
                    self.behavior_controller.show_speech_bubble(msg, duration_ms=6000)

        # 2. Update status label with user state
        user_state = observation.get("user_state")
        if user_state:
            state_label = user_state.value if hasattr(user_state, 'value') else str(user_state)
            self.update_status("ready", f"Companion - {state_label}")

    def start_companion(self):
        """Initialize and start the Companion Intelligence system."""
        try:
            personality = get_setting("personality.current_personality", "friendly")
            self.companion = CompanionIntelligence(
                activity_monitor=self.activity_monitor,
                personality=personality,
            )
            print("[COMPANION] Intelligence system initialized")

            self.behavior_controller = CompanionBehaviorController(self)
            self.behavior_controller.start()
            self._start_companion_timer()
        except Exception as e:
            print("[COMPANION] Failed to initialize:", e)

    def start_screen_awareness(self):
        """Initialize and start the Screen Awareness system."""
        try:
            if not hasattr(self, 'screen_awareness') or self.screen_awareness is None:
                from screen_awareness import ScreenAwareness
                self.screen_awareness = ScreenAwareness(main_window=self)
            self.screen_awareness.start()
            print("[SCREEN AWARENESS] Started")
        except Exception as e:
            print("[SCREEN AWARENESS] Failed to start:", e)

    def stop_screen_awareness(self):
        """Stop the screen awareness system."""
        if hasattr(self, 'screen_awareness') and self.screen_awareness is not None:
            try:
                self.screen_awareness.stop()
                print("[SCREEN AWARENESS] Stopped")
            except Exception:
                pass
            self.screen_awareness = None

    def stop_companion(self):
        """Stop the companion intelligence system."""
        if self.behavior_controller is not None:
            try:
                self.behavior_controller.stop()
            except Exception:
                pass
            self.behavior_controller = None
        if self.companion_timer is not None:
            try:
                self.companion_timer.stop()
            except Exception:
                pass
            self.companion_timer = None
        self.companion = None
        print("[COMPANION] Stopped")

    def _start_companion_timer(self):
        if self.companion_timer is not None:
            try:
                self.companion_timer.stop()
            except Exception:
                pass
        self.companion_timer = QTimer()
        self.companion_timer.timeout.connect(self._companion_tick)
        self.companion_timer.start(5000)

    def _companion_tick(self):
        if self.companion is None or self.activity_monitor is None:
            return
        try:
            activity = self.activity_monitor.current_activity
            activity_name = activity.value if hasattr(activity, 'value') else str(activity)
            observation = self.companion.cycle(
                activity_type=activity_name,
                window_title=self.activity_monitor.window_title,
                process_name=self.activity_monitor.process_name,
                idle_minutes=self.activity_monitor.idle_minutes,
                is_processing=self.is_processing,
                is_voice_active=getattr(self, 'is_listening', False),
            )
            self._apply_companion_observation(observation)
        except Exception as e:
            print("[COMPANION] Tick error:", e)

    def _on_character_clicked(self):
        if self.behavior_controller is not None:
            self.behavior_controller.on_character_clicked()

    # ========================================================
    # SETTINGS
    # ========================================================

    def open_settings(
        self,
    ):

        try:

            from settings_ui import SettingsWindow

            if self.settings_window is not None:

                try:

                    self.settings_window.show()

                    self.settings_window.raise_()

                    self.settings_window.activateWindow()

                    return

                except RuntimeError:

                    self.settings_window = None

            self.settings_window = SettingsWindow()

            self.settings_window.setWindowTitle(
                "AI Friend Settings"
            )

            self.settings_window.setMinimumSize(
                950,
                650,
            )

            self.settings_window.resize(
                1100,
                750,
            )

            self.settings_window.setAttribute(
                Qt.WidgetAttribute.WA_DeleteOnClose,
                False,
            )

            self.settings_window.settings_changed.connect(
                self.on_setting_changed
            )

            self.settings_window.navigate_back.connect(
                self.back_to_chat
            )

            screen = self.screen()
            if screen is None:
                screen = QApplication.primaryScreen()
            if screen is not None:
                screen_geo = screen.availableGeometry()
                x = screen_geo.center().x() - self.settings_window.width() // 2
                y = screen_geo.center().y() - self.settings_window.height() // 2
                self.settings_window.move(
                    max(screen_geo.left(), x),
                    max(screen_geo.top(), y),
                )

            self.settings_window.show()

            self.settings_window.raise_()

            self.settings_window.activateWindow()

        except ImportError as error:

            print(
                "SETTINGS IMPORT ERROR:",
                error
            )

            QMessageBox.warning(
                self,
                "Settings Error",
                "settings_ui.py could not be loaded."
            )

        except Exception as error:

            print(
                "SETTINGS WINDOW ERROR:",
                error
            )

            traceback.print_exc()

            QMessageBox.warning(
                self,
                "Settings Error",
                str(error)
            )

    # ========================================================
    # BACK TO CHAT
    # ========================================================

    def back_to_chat(
        self,
    ):

        if self.settings_window is not None:

            try:

                self.settings_window.hide()

            except Exception:

                pass

        if self.character is not None:

            self.character.show()

            self.character.raise_()

            self.position_character()

    # ========================================================
    # SETTINGS CHANGE
    # ========================================================

    def on_setting_changed(
        self,
        *args,
    ):

        """
        Supports both:

            callback(path, value)

        and:

            callback(path, old_value, new_value)

        This prevents listener signature crashes.
        """

        if len(args) == 2:

            path = args[0]

            new_value = args[1]

            old_value = None

        elif len(args) >= 3:

            path = args[0]

            old_value = args[1]

            new_value = args[2]

        else:

            return

        print(
            f"SETTING CHANGED: "
            f"{path} "
            f"{old_value} -> "
            f"{new_value}"
        )

        # ----------------------------------------------------
        # VOICE
        # ----------------------------------------------------

        if path == "voice.enabled":

            self.voice_enabled = bool(
                new_value
            )

            self.update_voice_button()

            if not self.voice_enabled:

                try:

                    stop_speaking()

                except Exception:

                    pass

                self.character_talking_signal.emit(
                    False
                )

        # ----------------------------------------------------
        # CHARACTER
        # ----------------------------------------------------

        elif path == "character.enabled":

            self.update_character_visibility(
                bool(new_value)
            )

        # ----------------------------------------------------
        # VOICE AUTO STOP
        # ----------------------------------------------------

        elif path == "voice.auto_stop_previous":

            pass

        # ----------------------------------------------------
        # CHARACTER SIZE
        # ----------------------------------------------------

        elif path == "character.size":

            self.apply_character_size(
                new_value
            )

        # ----------------------------------------------------
        # SCREEN AWARENESS
        # ----------------------------------------------------

        elif path == "screen_awareness.enabled":

            if new_value:

                self.start_screen_awareness()

            else:

                self.stop_screen_awareness()

    # ========================================================
    # CHARACTER SIZE
    # ========================================================

    def apply_character_size(
        self,
        value,
    ):

        if self.character is None:

            return

        try:

            size = float(value)

        except Exception:

            return

        method = getattr(
            self.character,
            "set_character_size",
            getattr(self.character, "set_scale_factor", None)
        )

        if callable(method):

            try:

                method(
                    size
                )

            except Exception as error:

                print(
                    "CHARACTER SIZE ERROR:",
                    error
                )

        self.position_character()

    # ========================================================
    # VOICE BUTTON
    # ========================================================

    def update_voice_button(
        self,
    ):

        if self.voice_enabled:

            self.voice_button.setText(
                "🔊  Voice: ON"
            )

        else:

            self.voice_button.setText(
                "🔇  Voice: OFF"
            )

    # ========================================================
    # STATUS
    # ========================================================

    def update_status(
        self,
        state,
        message=None,
    ):

        if self.status_label is None:

            return

        label = message or format_status(
            state,
            "Ready",
        )

        self.status_label.setText(
            f"● {label}"
        )

        if state == "error":

            self.status_label.setStyleSheet(
                "color: #FF6B6B;"
            )

        elif state in {"thinking", "speaking", "listening"}:

            self.status_label.setStyleSheet(
                "color: #FFD166;"
            )

        else:

            self.status_label.setStyleSheet(
                "color: #65E6A5;"
            )

    # ========================================================
    # TOGGLE VOICE
    # ========================================================

    def toggle_voice(
        self,
    ):

        self.voice_enabled = not self.voice_enabled

        try:

            set_setting(
                "voice.enabled",
                self.voice_enabled
            )

        except Exception as error:

            print(
                "VOICE SETTING ERROR:",
                error
            )

        if not self.voice_enabled:

            try:

                stop_speaking()

            except Exception:

                pass

            self.character_talking_signal.emit(
                False
            )

        self.update_voice_button()

    # ========================================================
    # VOICE INPUT (MICROPHONE) - ChatGPT-Style
    # ========================================================

    def toggle_voice_input(
        self,
    ):

        if self.is_listening:
            self.stop_voice_input()
            return

        if self.is_processing:
            return

        self.start_voice_input()

    def start_voice_input(
        self,
    ):

        # Start continuous recording via voice.py
        success = listen_start()

        if not success:
            QMessageBox.warning(
                self,
                "Microphone Error",
                "Could not start microphone recording.\n\n"
                "Please check your microphone device."
            )
            return

        self.is_listening = True

        self.mic_button.setText(
            "🔴"
        )

        self.mic_button.setProperty(
            "listening",
            True
        )

        self.mic_button.style().unpolish(
            self.mic_button
        )

        self.mic_button.style().polish(
            self.mic_button
        )

        self.update_status(
            "listening",
            "Listening...",
        )

        self.user_input.setPlaceholderText(
            "Listening... speak now"
        )

    def stop_voice_input(
        self,
    ):

        self.is_listening = False

        self.mic_button.setText(
            "🎤"
        )

        self.mic_button.setProperty(
            "listening",
            False
        )

        self.mic_button.style().unpolish(
            self.mic_button
        )

        self.mic_button.style().polish(
            self.mic_button
        )

        self.update_status(
            "ready",
            "Ready",
        )

        self.user_input.setPlaceholderText(
            "Message your AI Friend..."
        )

        # Stop recording and recognize in a background thread
        self.voice_input_worker = VoiceRecognitionWorker()
        self.voice_input_worker.result_ready.connect(
            self._on_voice_recognition_done
        )
        self.voice_input_worker.start()

    def _on_voice_recognition_done(
        self,
        text,
    ):

        if self.voice_input_worker is not None:
            self.voice_input_worker.deleteLater()
            self.voice_input_worker = None

        if text:

            self.user_input.setText(
                str(text)
            )

            self.user_input.setFocus()

        else:

            QMessageBox.warning(
                self,
                "Microphone",
                "Could not understand audio.\n\n"
                "Please try again."
            )

    # ========================================================
    # CHARACTER VISIBILITY
    # ========================================================

    def update_character_visibility(
        self,
        enabled,
    ):

        self.character_enabled = bool(
            enabled
        )

        if self.character_enabled:

            if self.character is None:

                self.create_character()

            else:

                self.character.show()

                self.character.raise_()

                self.position_character()

        else:

            if self.character is not None:

                self.character.hide()

                try:

                    stop_speaking()

                except Exception:

                    pass

                self.character_talking_signal.emit(
                    False
                )

    # ========================================================
    # SAFE CHARACTER METHOD
    # ========================================================

    def character_call(
        self,
        method_name,
        *args,
    ):

        if self.character is None:

            return

        method = getattr(
            self.character,
            method_name,
            None
        )

        if not callable(method):

            return

        try:

            method(
                *args
            )

        except Exception as error:

            print(
                f"CHARACTER ERROR "
                f"({method_name}):",
                error
            )

    # ========================================================
    # CHARACTER TALKING
    # ========================================================

    def character_talking(
        self,
        talking,
    ):

        if self.character is None:

            return

        self.character_call(
            "set_talking",
            bool(talking)
        )

        if not talking:

            QTimer.singleShot(
                700,
                self.return_to_idle
            )

    def _animate_widget_entrance(self, widget):
        """Animate widget fading/sliding in."""
        try:
            from PySide6.QtCore import QPropertyAnimation, QEasingCurve
            
            widget.setWindowOpacity(0.0)
            current_pos = widget.pos()
            widget.move(current_pos.x(), current_pos.y() + 10)
            
            opacity_anim = QPropertyAnimation(widget, b"windowOpacity")
            opacity_anim.setDuration(300)
            opacity_anim.setStartValue(0.0)
            opacity_anim.setEndValue(1.0)
            opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            
            pos_anim = QPropertyAnimation(widget, b"pos")
            pos_anim.setDuration(300)
            pos_anim.setStartValue(widget.pos())
            pos_anim.setEndValue(current_pos)
            pos_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            
            opacity_anim.start()
            pos_anim.start()
        except Exception:
            pass

    # ========================================================
    # ADD USER MESSAGE
    # ========================================================

    def add_user_message(
        self,
        text,
    ):

        bubble = QLabel(
            str(text)
        )

        bubble.setObjectName(
            "UserBubble"
        )

        bubble.setWordWrap(
            True
        )

        bubble.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        # Keep the user reply comfortably wide without dominating the chat area.
        chat_width = self.chat_area.width() if self.chat_area else 800
        max_width = max(260, int(chat_width * 0.72))
        bubble.setMaximumWidth(
            max_width
        )

        bubble.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )

        # Animate entrance
        self._animate_widget_entrance(bubble)

        row = QHBoxLayout()

        row.setContentsMargins(
            0,
            0,
            0,
            0
        )

        row.addStretch()

        row.addWidget(
            bubble
        )

        self.message_layout.insertLayout(
            self.message_layout.count() - 1,
            row
        )

        self.scroll_to_bottom()

    # ========================================================
    # ADD AI MESSAGE (RICH MARKDOWN) - PRIMARY METHOD
    # ========================================================

    def add_ai_message_rich(
        self,
        text,
        message_id=None,
    ):
        """Add a Markdown-rendered AI message using QTextBrowser."""

        browser = QTextBrowser()
        browser.setObjectName("AIBubble")
        
        # Let AI responses feel spacious but still readable within the conversation area.
        chat_width = self.chat_area.width() if self.chat_area else 800
        max_width = max(360, int(chat_width * 0.82))
        browser.setMaximumWidth(max_width)
        browser.setMinimumHeight(40)
        browser.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )
        browser.setOpenExternalLinks(True)
        browser.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        browser.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        browser.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)

        # Style the QTextBrowser to match AIBubble
        browser.setStyleSheet(
            "QTextBrowser {"
            "  background-color: #20202D;"
            "  border: 1px solid #303044;"
            "  border-radius: 16px;"
            "  padding: 12px 16px;"
            "  font-size: 14px;"
            "  color: white;"
            "}"
        )

        html = markdown_to_html(str(text))
        browser.setHtml(html)

        # Adjust height after layout settles to avoid nested scrollbars
        QTimer.singleShot(0, lambda: self._adjust_browser_height(browser, max_width))

        # Store message data
        if message_id:
            browser.setProperty("message_id", message_id)
        browser.setProperty("full_text", str(text))

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(browser)
        row.addStretch()

        self.message_layout.insertLayout(
            self.message_layout.count() - 1,
            row
        )

        self.scroll_to_bottom()
        return browser

    def _adjust_browser_height(self, browser, width=None):
        """Safely adjust QTextBrowser height to fit content without scrollbars."""
        try:
            doc = browser.document()
            actual_width = width or browser.maximumWidth() or 680
            doc.setTextWidth(actual_width)
            height = int(doc.size().height()) + 24
            browser.setMinimumHeight(max(40, height))
            browser.setMaximumHeight(height)
        except Exception:
            pass

    def _reflow_messages(self):
        """Reflow all messages to fit the current chat area width."""
        if not self.chat_area or not self.message_layout:
            return
        
        chat_width = self.chat_area.width()
        if chat_width <= 0:
            return
        
        # Update all user message bubbles
        for i in range(self.message_layout.count()):
            item = self.message_layout.itemAt(i)
            if item and item.layout():
                layout = item.layout()
                for j in range(layout.count()):
                    widget = layout.itemAt(j).widget()
                    if widget and widget.objectName() == "UserBubble":
                        max_width = max(260, int(chat_width * 0.72))
                        widget.setMaximumWidth(max_width)
                    elif widget and widget.objectName() == "AIBubble":
                        max_width = max(360, int(chat_width * 0.82))
                        widget.setMaximumWidth(max_width)
                        # Re-adjust height with new width
                        QTimer.singleShot(0, lambda b=widget, w=max_width: self._adjust_browser_height(b, w))

    # ========================================================
    # ADD AI MESSAGE (PLAIN TEXT FALLBACK - delegates to rich)
    # ========================================================

    def add_ai_message(self, text):
        """Add a plain text AI message (delegates to rich markdown version)."""
        return self.add_ai_message_rich(text)

    # ========================================================
    # ADD AI IMAGE MESSAGE
    # ========================================================

    def add_ai_image_message(
        self,
        image_path,
        caption=None,
    ):

        # Container frame for image message
        container = QFrame()

        container.setObjectName(
            "ImageBubble"
        )

        container.setMaximumWidth(
            680
        )

        container_layout = QVBoxLayout(
            container
        )

        container_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        container_layout.setSpacing(
            8
        )

        # Caption label
        if caption:

            caption_label = QLabel(
                str(caption)
            )

            caption_label.setWordWrap(
                True
            )

            caption_label.setStyleSheet(
                "color: #F5F5F5; font-size: 14px;"
            )

            container_layout.addWidget(
                caption_label
            )

        # Image label
        image_label = QLabel()

        image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # Load and scale image
        if os.path.exists(image_path):

            pixmap = QPixmap(
                image_path
            )

            if not pixmap.isNull():

                # Scale to fit chat area, preserve aspect ratio
                max_width = 500
                max_height = 400

                scaled = pixmap.scaled(
                    max_width,
                    max_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                image_label.setPixmap(
                    scaled
                )

            else:

                image_label.setText(
                    "[Image could not be loaded]"
                )

        else:

            image_label.setText(
                "[Image file not found]"
            )

        container_layout.addWidget(
            image_label
        )

        # Row layout
        row = QHBoxLayout()

        row.setContentsMargins(
            0,
            0,
            0,
            0
        )

        row.addWidget(
            container
        )

        row.addStretch()

        self.message_layout.insertLayout(
            self.message_layout.count() - 1,
            row
        )

        self.scroll_to_bottom()

    # ========================================================
    # THINKING
    # ========================================================

    def show_thinking(
        self,
    ):

        if self.thinking_label is not None:

            return

        self.thinking_label = QLabel(
            "AI Friend is thinking... 🤔"
        )

        self.thinking_label.setObjectName(
            "Typing"
        )

        row = QHBoxLayout()

        row.setContentsMargins(
            0,
            0,
            0,
            0
        )

        row.addWidget(
            self.thinking_label
        )

        row.addStretch()

        self.message_layout.insertLayout(
            self.message_layout.count() - 1,
            row
        )

        self.scroll_to_bottom()

    # ========================================================
    # REMOVE THINKING
    # ========================================================

    def remove_thinking(
        self,
    ):

        if self.thinking_label is None:

            return

        try:

            self.thinking_label.deleteLater()

        except RuntimeError:

            pass

        self.thinking_label = None

    # ========================================================
    # IMAGE MESSAGE
    # ========================================================

    def add_image_message(
        self,
        image_path,
    ):

        pixmap = QPixmap(
            image_path
        )

        if pixmap.isNull():

            return

        scaled = pixmap.scaled(
            280,
            280,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        label = QLabel()
        label.setPixmap(scaled)
        label.setMaximumWidth(300)
        label.setMinimumHeight(40)
        label.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        label.setStyleSheet(
            "QLabel {"
            "  border-radius: 14px;"
            "  border: 1px solid #303044;"
            "  background-color: #20202D;"
            "  padding: 4px;"
            "}"
        )
        label.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        layout.setAlignment(
            label,
            Qt.AlignmentFlag.AlignLeft
        )

        self.message_layout.insertWidget(
            self.message_layout.count() - 1,
            container
        )
        self.scroll_to_bottom()

    # ========================================================
    # DRAG AND DROP / PASTE
    # ========================================================

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        files = []
        if event.mimeData().hasUrls():
            files = [
                u.toLocalFile()
                for u in event.mimeData().urls()
                if u.isLocalFile()
            ]
        elif event.mimeData().hasImage():
            files = [
                "clipboard_image.png"
            ]

        if files:
            self.attached_files.extend(files)
            self._show_attachment_preview()

        event.acceptProposedAction()
        super().dropEvent(event)

    def keyPressEvent(self, event):
        if (
            event.modifiers() == Qt.KeyboardModifier.ControlModifier
            and event.key() == Qt.Key.Key_V
        ):
            clipboard = QApplication.clipboard()
            if clipboard is not None and clipboard.mimeData().hasImage():
                temp_path = Path(tempfile.gettempdir()) / "avora_paste.png"
                image = clipboard.image()
                if image.save(str(temp_path)):
                    self.attached_files.append(str(temp_path))
                    self._show_attachment_preview()
                    event.accept()
                    return
        super().keyPressEvent(event)

    # ========================================================
    # FILE ATTACHMENTS
    # ========================================================

    def _attach_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Attach Files",
            "",
            "All Files (*);;Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;Documents (*.pdf *.docx *.xlsx *.pptx *.txt *.csv);;Code (*.py *.java *.cpp *.js *.html *.css);;Archives (*.zip *.rar *.7z)",
        )
        if file_paths:
            self.attached_files.extend(file_paths)
            self._show_attachment_preview()

    def _show_attachment_preview(self):
        if not self.attached_files:
            return
        preview_text = f"📎 {len(self.attached_files)} file(s) attached"
        if len(self.attached_files) == 1:
            preview_text = f"📎 {Path(self.attached_files[0]).name}"
        self.user_input.setPlaceholderText(preview_text)

    def _clear_attachments(self):
        self.attached_files = []
        self.user_input.setPlaceholderText("Message your AI Friend...")

    def _process_attachments_for_ai(self):
        results = []
        for path in self.attached_files:
            p = Path(path)
            if not p.exists():
                continue
            suffix = p.suffix.lower()
            if suffix in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}:
                try:
                    import base64
                    with open(p, 'rb') as f:
                        data = base64.b64encode(f.read()).decode('utf-8')
                    results.append({
                        'type': 'image',
                        'path': str(p),
                        'name': p.name,
                        'data': data,
                        'mime': f'image/{suffix[1:]}',
                    })
                except Exception as e:
                    print(f"[ATTACH] Image read error: {e}")
            else:
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    results.append({
                        'type': 'text',
                        'path': str(p),
                        'name': p.name,
                        'content': content,
                    })
                except Exception as e:
                    results.append({
                        'type': 'text',
                        'path': str(p),
                        'name': p.name,
                        'content': f'[Binary or unreadable file: {p.name}]',
                    })
        return results

    # ========================================================
    # SEND MESSAGE (STREAMING)
    # ========================================================

    def send_message(self):

        if self.is_closing:
            return

        if self.is_processing:
            return

        message = sanitize_user_text(
            self.user_input.text()
        )

        if not message:
            return

        # Validate message length
        max_length = get_setting("chat.max_message_length", 2000)
        if len(message) > max_length:
            self.add_ai_message_rich(
                f"Brooo, that message is too long! 😅\n\n"
                f"Maximum length is {max_length} characters.\n"
                f"Your message is {len(message)} characters.\n\n"
                f"Try splitting it into smaller messages."
            )
            return

        self.add_user_message(message)
        self._append_user_message_to_chat(message)

        # Display any attached images in chat
        for att in self._process_attachments_for_ai():
            if att['type'] == 'image':
                self.add_image_message(att['path'])

        self._clear_attachments()
        self.user_input.clear()

        if self.companion is not None:
            self.companion.on_user_message(message)

        self.set_processing_state(True)

        self.update_status(
            "thinking",
            "Thinking",
        )

        self.character_call("react_to_message", message)
        self.character_call("set_state", "thinking")
        self.character_call(
            "react",
            "thinking",
            {"message": "I'm thinking through your request…"}
        )

        self.show_thinking()

        # Create streaming worker
        attachments = self._process_attachments_for_ai()
        self.worker = StreamingWorker(message, self, attachments=attachments)
        self._current_message = message
        self._current_browser = None
        self._current_full_text = ""

        # Connect signals
        self.worker.stream_started.connect(self._on_stream_started)
        self.worker.chunk_ready.connect(self._on_chunk_ready)
        self.worker.stream_finished.connect(self._on_stream_finished)
        self.worker.stream_failed.connect(self._on_stream_failed)

        self.worker.start()

    # ========================================================
    # STREAMING HANDLERS
    # ========================================================

    def _on_stream_started(self):
        """Called when streaming begins - create the message bubble."""
        if self.is_closing:
            return

        self.remove_thinking()
        self._current_browser = self.add_ai_message_rich("")
        self._current_full_text = ""

    def _on_chunk_ready(self, chunk):
        """Called when a new chunk of text is available."""
        if self.is_closing or self._current_browser is None:
            return

        self._current_full_text += chunk

        # Update the browser with rendered HTML
        html = markdown_to_html(self._current_full_text)
        self._current_browser.setHtml(html)

        # Adjust height
        self._adjust_browser_height(self._current_browser)

        self.scroll_to_bottom()

    def _on_stream_finished(self, full_text):
        """Called when streaming is complete."""
        if self.is_closing:
            return

        self._current_full_text = str(full_text)

        # Final render
        if self._current_browser is not None:
            html = markdown_to_html(self._current_full_text)
            self._current_browser.setHtml(html)
            self._adjust_browser_height(self._current_browser)

            # Store full text for regenerate
            self._current_browser.setProperty("full_text", self._current_full_text)
            self._current_browser.setProperty("user_message", self._current_message)

            # Add regenerate button
            self._add_message_actions(self._current_browser)

        self._append_assistant_message_to_chat(str(full_text))

        self.update_status("ready", "Ready")

        self.character_call("set_state", "idle")
        self.character_call(
            "react",
            "speaking",
            {"message": "I've got an answer for you."}
        )

        if self.companion is not None:
            self.companion.on_ai_response(str(full_text))

        # Voice
        should_speak = (
            self.voice_enabled
            and bool(get_setting("voice.speak_after_response", True))
        )
        if should_speak:
            self.start_voice(self._current_full_text)
        else:
            self.character_call("set_state", "idle")

        self.set_processing_state(False)
        self.cleanup_worker()

    def _on_stream_failed(self, error_msg):
        """Called when streaming fails."""
        if self.is_closing:
            return

        self.remove_thinking()
        self.update_status("error", "Error")

        self.character_call("set_state", "error")
        self.character_call(
            "react",
            "error",
            {"message": "Something went wrong."}
        )

        if self.companion is not None:
            self.companion.on_error(error_msg)

        self.add_ai_message_rich(
            "Sorry brooo 😭\n\n"
            "Something went wrong while processing your request.\n\n"
            "Please try again."
        )

        self._append_assistant_message_to_chat(
            "Sorry brooo 😭\n\n"
            "Something went wrong while processing your request.\n\n"
            "Please try again."
        )

        print("========== AI ERROR ==========")
        print(error_msg)
        print("==============================\n")

        self.set_processing_state(False)
        self.cleanup_worker()

    # ========================================================
    # MESSAGE ACTIONS (Stop / Regenerate)
    # ========================================================

    def _add_message_actions(self, browser):
        """Add regenerate button below an AI message."""
        if browser is None:
            return

        # Create actions row
        actions_row = QHBoxLayout()
        actions_row.setContentsMargins(0, 0, 0, 0)
        actions_row.setSpacing(6)

        # Regenerate button
        regen_btn = QPushButton("🔄 Regenerate")
        regen_btn.setFixedHeight(28)
        regen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        regen_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: transparent;"
            "  border: 1px solid #3A3A50;"
            "  border-radius: 10px;"
            "  padding: 4px 12px;"
            "  color: #A0A0B5;"
            "  font-size: 11px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #292944;"
            "  color: #FFFFFF;"
            "  border-color: #6C63FF;"
            "}"
        )
        user_msg = browser.property("user_message") or ""
        regen_btn.clicked.connect(
            lambda checked, msg=user_msg: self.regenerate_response(msg)
        )

        actions_row.addWidget(regen_btn)
        actions_row.addStretch()

        # Insert after the browser's parent row
        parent_layout = browser.parent().layout() if browser.parent() else None
        if parent_layout:
            # Find the index of the browser's row
            for i in range(self.message_layout.count()):
                item = self.message_layout.itemAt(i)
                if item and item.layout() and self._layout_contains(item.layout(), browser):
                    self.message_layout.insertLayout(i + 1, actions_row)
                    break
        else:
            self.message_layout.insertLayout(
                self.message_layout.count() - 1,
                actions_row
            )

    def _layout_contains(self, layout, widget):
        """Check if a layout contains a specific widget."""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() == widget:
                return True
            if item.layout() and self._layout_contains(item.layout(), widget):
                return True
        return False

    def regenerate_response(self, message):
        """Regenerate the last AI response."""
        if self.is_processing or not message:
            return

        self.set_processing_state(True)
        self.update_status("thinking", "Thinking")

        self.character_call("set_state", "thinking")
        self.character_call(
            "react",
            "thinking",
            {"message": "Let me try again..."}
        )

        self.show_thinking()

        self.worker = RegenerateWorker(message, self)
        self._current_message = message

        self.worker.finished.connect(self._on_regenerate_finished)
        self.worker.failed.connect(self._on_regenerate_failed)
        self.worker.finished.connect(self.cleanup_worker)
        self.worker.failed.connect(self.cleanup_worker)

        self.worker.start()

    def _on_regenerate_finished(self, reply):
        """Handle regenerated response."""
        if self.is_closing:
            return

        self.remove_thinking()

        self.update_status("ready", "Ready")

        self.character_call("set_state", "idle")
        reply = clean_ai_reply(reply)
        self.add_ai_message_rich(str(reply))
        self._append_assistant_message_to_chat(str(reply))

        should_speak = (
            self.voice_enabled
            and bool(get_setting("voice.speak_after_response", True))
        )
        if should_speak:
            self.start_voice(str(reply))
        else:
            self.character_call("set_state", "idle")

        self.set_processing_state(False)

    def _on_regenerate_failed(self, error):
        """Handle regenerate failure."""
        if self.is_closing:
            return

        self.remove_thinking()
        self.update_status("error", "Error")

        self.character_call("set_state", "error")

        self.add_ai_message_rich(
            "Sorry brooo 😭\n\n"
            "Could not regenerate the response.\n\n"
            "Please try again."
        )

        self.set_processing_state(False)

    # ========================================================
    # STOP GENERATION
    # ========================================================

    def stop_generation(self):
        """Stop the current AI generation."""
        if self.worker is not None and self.worker.isRunning():
            if hasattr(self.worker, "cancel"):
                self.worker.cancel()
            self.worker.quit()
            self.worker.wait(1000)

        self.remove_thinking()
        self.update_status("ready", "Ready")

        self.set_processing_state(False)
        self.cleanup_worker()

    # ========================================================
    # SAFE VOICE START
    # ========================================================

    def start_voice(
        self,
        reply,
    ):

        try:

            # New voice.py versions
            # may support callbacks.

            speak(
                reply,
                on_start=self.start_talking,
                on_finish=self.finish_talking
            )

        except TypeError:

            # Compatibility fallback for
            # older voice.py versions.

            try:

                speak(
                    reply
                )

                self.character_call(
                    "set_expression",
                    "happy"
                )

            except Exception as error:

                print(
                    "VOICE ERROR:",
                    error
                )

                self.finish_talking()

        except Exception as error:

            print(
                "VOICE ERROR:",
                error
            )

            self.finish_talking()

    # ========================================================
    # ERROR RESPONSE
    # ========================================================

    def show_error_response(
        self,
        error,
    ):

        if self.is_closing:

            return

        self.remove_thinking()

        self.update_status(
            "error",
            "Error",
        )

        self.character_call(
            "set_thinking",
            False
        )

        self.character_call(
            "set_expression",
            "sad"
        )

        self.character_call(
            "react",
            "error",
            {
                "message": "Something went wrong."
            }
        )

        self.add_ai_message(
            "Sorry brooo 😭\n\n"
            "Something went wrong while processing your request.\n\n"
            "Please try again."
        )

        print(
            "\n========== AI ERROR =========="
        )

        print(
            error
        )

        print(
            "==============================\n"
        )

        self.set_processing_state(
            False
        )

    # ========================================================
    # WORKER CLEANUP
    # ========================================================

    def cleanup_worker(
        self,
        *args,
    ):

        worker = self.worker

        if worker is None:

            return

        self.worker = None

        worker.deleteLater()

    # ========================================================
    # PROCESSING STATE
    # ========================================================

    def set_processing_state(
        self,
        processing,
    ):

        self.is_processing = bool(
            processing
        )

        self.user_input.setEnabled(
            not self.is_processing
        )

        self.send_button.setEnabled(
            not self.is_processing
        )

        self.new_chat_button.setEnabled(
            not self.is_processing
        )

        if not self.is_processing:

            self.mic_button.setEnabled(
                True
            )

        if not self.is_processing:

            self.user_input.setFocus()

    # ========================================================
    # TALKING
    # ========================================================

    def start_talking(
        self,
    ):

        if not self.voice_enabled:

            return

        QTimer.singleShot(
            0,
            self._apply_start_talking,
        )

    def _apply_start_talking(
        self,
    ):

        if self.is_closing:

            return

        self.update_status(
            "speaking",
            "Speaking",
        )

        self.character_talking_signal.emit(
            True
        )

    # ========================================================
    # FINISH TALKING
    # ========================================================

    def finish_talking(
        self,
    ):

        QTimer.singleShot(
            0,
            self._apply_finish_talking,
        )

    def _apply_finish_talking(
        self,
    ):

        if self.is_closing:

            return

        self.character_talking_signal.emit(
            False
        )

        self.update_status(
            "ready",
            "Ready",
        )

    # ========================================================
    # RETURN TO IDLE
    # ========================================================

    def return_to_idle(
        self,
    ):

        self.character_call(
            "set_expression",
            "idle"
        )

    # ========================================================
    # NEW CHAT
    # ========================================================

    def new_chat(
        self,
    ):

        if self.is_processing:

            return

        try:

            stop_speaking()

        except Exception:

            pass

        self.character_talking_signal.emit(
            False
        )

        self.remove_thinking()

        # Clear message layout by removing items one by one
        # with defensive error handling to prevent deleted-object crashes
        try:
            while self.message_layout.count() > 1:
                item = self.message_layout.takeAt(0)
                if item is None:
                    break
                widget = item.widget()
                if widget is not None:
                    try:
                        widget.setParent(None)
                        widget.deleteLater()
                    except (RuntimeError, AttributeError):
                        pass
                else:
                    # Handle nested layouts
                    layout = item.layout()
                    if layout is not None:
                        try:
                            while layout.count() > 0:
                                child = layout.takeAt(0)
                                if child.widget():
                                    try:
                                        child.widget().setParent(None)
                                        child.widget().deleteLater()
                                    except (RuntimeError, AttributeError):
                                        pass
                        except (RuntimeError, AttributeError):
                            pass
        except (RuntimeError, AttributeError):
            pass

        self.update_status(
            "ready",
            "Ready",
        )

        self.character_call(
            "set_expression",
            "happy"
        )

        self.add_ai_message(
            "New conversation started 😎🔥\n\n"
            "What do you want to talk about?"
        )

        QTimer.singleShot(
            1500,
            self.return_to_idle
        )

    # ========================================================
    # CHAT MANAGEMENT
    # ========================================================

    def load_chats(self):
        """Load chats from persistent storage."""
        try:
            self.chats, self.active_chat_id = load_conversations()
            if self.chat_sidebar is not None:
                self.chat_sidebar.set_chats(self.chats)
                self.chat_sidebar.set_active_chat(self.active_chat_id)
        except Exception as error:
            print("[CHAT] Load error:", error)
            self.chats = []
            self.active_chat_id = None

    def save_chats(self):
        """Save chats to persistent storage."""
        try:
            save_conversations(self.chats, self.active_chat_id)
        except Exception as error:
            print("[CHAT] Save error:", error)

    def _get_active_chat(self) -> Optional[dict]:
        """Return the currently active chat dict, or None."""
        if not self.active_chat_id:
            return None
        for chat in self.chats:
            if chat.get("id") == self.active_chat_id:
                return chat
        return None

    def create_new_chat(self):
        """Create a new empty chat and activate it."""
        if self.is_processing:
            return

        # Block rapid calls to prevent libshiboken crashes
        if hasattr(self, '_new_chat_lock') and self._new_chat_lock:
            return
        self._new_chat_lock = True

        try:
            try:
                stop_speaking()
            except Exception:
                pass

            self.character_talking_signal.emit(False)

            chat_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            new_chat = {
                "id": chat_id,
                "title": "New Conversation",
                "messages": [],
                "created_at": now,
                "updated_at": now,
                "pinned": False,
                "favorite": False,
                "tags": [],
            }

            self.chats.insert(0, new_chat)
            self.active_chat_id = chat_id

            if self.chat_sidebar is not None:
                self.chat_sidebar.set_chats(self.chats)
                self.chat_sidebar.set_active_chat(self.active_chat_id)

            self.new_chat()
        finally:
            # Release lock after a longer delay to ensure UI is fully settled
            QTimer.singleShot(500, lambda: setattr(self, '_new_chat_lock', False))

    def switch_chat(self, chat_id: str):
        """Switch to the chat with the given ID."""
        if self.is_processing:
            return

        self.active_chat_id = chat_id

        if self.chat_sidebar is not None:
            self.chat_sidebar.set_active_chat(self.active_chat_id)

        chat = self._get_active_chat()
        if chat is None:
            return

        self._updating_chat = True

        try:
            self.new_chat()

            messages = chat.get("messages", [])
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    self.add_user_message(content)
                elif role == "assistant":
                    self.add_ai_message_rich(content)
        finally:
            self._updating_chat = False

        self.save_chats()

    def delete_chat(self, chat_id: str):
        """Delete a chat after confirmation."""
        chat = None
        for c in self.chats:
            if c.get("id") == chat_id:
                chat = c
                break

        if chat is None:
            return

        reply = QMessageBox.question(
            self,
            "Delete Chat",
            "Are you sure you want to delete this conversation?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        was_active = self.active_chat_id == chat_id
        self.chats = [c for c in self.chats if c.get("id") != chat_id]

        if was_active:
            if self.chats:
                self.active_chat_id = self.chats[0]["id"]
                self.switch_chat(self.active_chat_id)
            else:
                self.active_chat_id = None
                self.new_chat()

        if self.chat_sidebar is not None:
            self.chat_sidebar.remove_chat(chat_id)

        self.save_chats()

        self.chat_sidebar.chat_deleted.emit(chat_id)

    def rename_chat(self, chat_id: str):
        """Rename a chat via input dialog."""
        chat = None
        for c in self.chats:
            if c.get("id") == chat_id:
                chat = c
                break

        if chat is None:
            return

        current_title = chat.get("title", "New Conversation")
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Chat",
            "Enter new title:",
            QLineEdit.EchoMode.Normal,
            current_title,
        )
        if not ok or not new_title.strip():
            return

        chat["title"] = new_title.strip()
        chat["updated_at"] = datetime.now().isoformat()

        if self.chat_sidebar is not None:
            self.chat_sidebar.update_chat(chat_id)

        self.save_chats()

    def toggle_pin(self, chat_id: str):
        """Toggle pin state for a chat."""
        chat = None
        for c in self.chats:
            if c.get("id") == chat_id:
                chat = c
                break

        if chat is None:
            return

        chat["pinned"] = not chat.get("pinned", False)
        chat["updated_at"] = datetime.now().isoformat()

        if self.chat_sidebar is not None:
            self.chat_sidebar.update_chat(chat_id)

        self.save_chats()

    def toggle_favorite(self, chat_id: str):
        """Toggle favorite state for a chat."""
        chat = None
        for c in self.chats:
            if c.get("id") == chat_id:
                chat = c
                break

        if chat is None:
            return

        chat["favorite"] = not chat.get("favorite", False)
        chat["updated_at"] = datetime.now().isoformat()

        if self.chat_sidebar is not None:
            self.chat_sidebar.update_chat(chat_id)

        self.save_chats()

    def _on_chat_deleted(self, chat_id: str):
        """Handle chat deletion from sidebar."""
        if self.active_chat_id == chat_id:
            self.active_chat_id = None
            self.new_chat()

    def _append_user_message_to_chat(self, text: str):
        """Append a user message to the active chat."""
        if self._updating_chat:
            return
        chat = self._get_active_chat()
        if chat is None:
            return
        now = datetime.now().isoformat()
        chat["messages"].append({
            "role": "user",
            "content": text,
            "timestamp": now,
        })
        chat["updated_at"] = now
        self._auto_title_chat(chat)
        self.save_chats()

    def _append_assistant_message_to_chat(self, text: str):
        """Append an assistant message to the active chat."""
        if self._updating_chat:
            return
        chat = self._get_active_chat()
        if chat is None:
            return
        now = datetime.now().isoformat()
        chat["messages"].append({
            "role": "assistant",
            "content": text,
            "timestamp": now,
        })
        chat["updated_at"] = now
        self._auto_title_chat(chat)
        self.save_chats()

    def _auto_title_chat(self, chat: dict):
        """Auto-generate a title if chat has 2+ messages and no custom title."""
        messages = chat.get("messages", [])
        if len(messages) >= 2 and chat.get("title") == "New Conversation":
            title = generate_title_from_messages(messages)
            chat["title"] = title

    # ========================================================
    # SCROLL
    # ========================================================

    def scroll_to_bottom(
        self,
    ):

        QTimer.singleShot(
            50,
            self._scroll_to_bottom_now
        )

    def _scroll_to_bottom_now(
        self,
    ):

        scrollbar = (
            self.chat_area
            .verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )

    # ========================================================
    # CHARACTER POSITION
    # ========================================================

    def get_character_scale_factor(
        self,
    ):

        try:

            user_size = float(
                get_setting(
                    "character.size",
                    1.0,
                )
            )

        except (TypeError, ValueError):

            user_size = 1.0

        user_size = max(0.3, min(3.0, user_size))

        if self.width() <= 900:

            responsive = max(
                0.55,
                min(
                    1.0,
                    self.width() / 1400.0,
                ),
            )

            return max(0.3, min(3.0, user_size * responsive))

        return user_size

    def restore_main_window(
        self,
    ):

        if self.isMinimized():

            self.showNormal()

        self.raise_()

        self.activateWindow()

        self.show()

        self.restore_character_to_window()

    def enter_compact_character_mode(
        self,
    ):

        if self.character is None:

            return

        if self.compact_character_mode:

            return

        if self.character.parent() is self:

            self.character.setParent(
                None
            )

        self.character.setWindowFlag(
            Qt.WindowType.Tool,
            True,
        )

        self.character.setWindowFlag(
            Qt.WindowType.FramelessWindowHint,
            True,
        )

        self.character.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint,
            True,
        )

        self.character.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )

        self.character.set_scale_factor(
            0.62
        )

        self.character.show()

        self.character.raise_()

        self.compact_character_mode = True

        self.position_character()

    def restore_character_to_window(
        self,
    ):

        if self.character is None:

            return

        if not self.compact_character_mode:

            return

        self.character.hide()

        self.character.setParent(
            self
        )

        self.character.setWindowFlag(
            Qt.WindowType.Tool,
            False,
        )

        self.character.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint,
            False,
        )

        self.character.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )

        self.character.show()

        self.character.raise_()

        self.compact_character_mode = False

        self.position_character()

    def position_character(
        self,
    ):

        if self.character is None:

            return

        if not self.character.isVisible():

            return

        if self.character.parent() is not self.sidebar:
            self.character.setParent(
                self.sidebar
            )

        self.character.set_scale_factor(
            self.get_character_scale_factor()
        )

        sidebar_rect = self.sidebar.contentsRect()
        margin = 18
        x = max(
            0,
            (sidebar_rect.width() - self.character.width()) // 2,
        )
        y = max(
            margin,
            sidebar_rect.bottom() - self.character.height() - margin,
        )

        self.character.move(
            x,
            y
        )

        self.character.raise_()

    # ========================================================
    # RESIZE
    # ========================================================

    def changeEvent(
        self,
        event,
    ):

        super().changeEvent(
            event
        )

        if event.type() == QEvent.Type.WindowStateChange:

            if self.isMinimized():

                self.enter_compact_character_mode()

            elif self.compact_character_mode:

                self.restore_character_to_window()

        self.position_character()

    def resizeEvent(
        self,
        event,
    ):

        super().resizeEvent(
            event
        )

        # Resize neural canvas
        if self.neural_canvas:
            self.neural_canvas.setGeometry(self.rect())

        self.position_character()

        # Reflow messages to fit new width
        QTimer.singleShot(100, self._reflow_messages)

    # ========================================================
    # CLOSE
    # ========================================================

    def _check_panic_status(
        self,
    ):
        """Check panic state and update UI accordingly."""
        if is_panic():
            self.update_status(
                "error",
                "PANIC MODE - Automation Stopped",
            )
            if self.is_processing:
                self.stop_generation()

    def closeEvent(
        self,
        event,
    ):

        self.is_closing = True

        # Stop microphone if recording
        if is_recording():

            try:
                listen_stop()
            except Exception:
                pass

        try:

            stop_speaking()

        except Exception as error:

            print(
                "VOICE STOP ERROR:",
                error
            )

        self.character_talking_signal.emit(
            False
        )

        self.remove_thinking()

        # ----------------------------------------------------
        # STOP AI WORKER
        # ----------------------------------------------------

        if self.worker is not None:

            try:

                if self.worker.isRunning():

                    self.worker.requestInterruption()

                    self.worker.quit()

                    if not self.worker.wait(
                        2500
                    ):

                        print(
                            "AI worker did not stop "
                            "within timeout."
                        )

            except Exception as error:

                print(
                    "WORKER CLOSE ERROR:",
                    error
                )

        # ----------------------------------------------------
        # CLOSE SETTINGS
        # ----------------------------------------------------

        if self.settings_window is not None:

            try:

                self.settings_window.close()

            except Exception:

                pass

        # ----------------------------------------------------
        # STOP TIMERS
        # ----------------------------------------------------

        if self.neural_timer is not None:
            try:
                self.neural_timer.stop()
            except Exception:
                pass
            self.neural_timer = None

        if self.companion_timer is not None:
            try:
                self.companion_timer.stop()
            except Exception:
                pass

        # ----------------------------------------------------
        # CLEANUP NEURAL CANVAS
        # ----------------------------------------------------

        if self.neural_canvas is not None:
            try:
                self.neural_canvas.setVisible(False)
            except Exception:
                pass
            self.neural_canvas = None

        # ----------------------------------------------------
        # STOP SCREEN AWARENESS
        # ----------------------------------------------------

        if hasattr(self, 'screen_awareness') and self.screen_awareness is not None:
            try:
                self.screen_awareness.stop()
            except Exception:
                pass

        # ----------------------------------------------------
        # STOP ACTIVITY MONITOR
        # ----------------------------------------------------

        try:
            self.stop_activity_monitor()
        except Exception:
            pass

        # ----------------------------------------------------
        # CLEANUP AVORA SYSTEMS
        # ----------------------------------------------------

        try:
            stop_hotkey_listener()
        except Exception:
            pass

        try:
            stop_clipboard_monitor()
        except Exception:
            pass

        try:
            self.stop_companion()
        except Exception:
            pass

        try:
            log_activity(
                "SYSTEM",
                "Avora shutting down",
                level="info",
            )
        except Exception:
            pass

        event.accept()


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================


def show_splash_screen():
    """Show a cinematic splash screen on startup."""
    splash = QWidget()
    splash.setWindowFlags(
        Qt.WindowType.FramelessWindowHint |
        Qt.WindowType.WindowStaysOnTopHint
    )
    splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    splash.setFixedSize(500, 300)

    # Center on screen
    screen = QApplication.primaryScreen().availableGeometry()
    x = (screen.width() - 500) // 2
    y = (screen.height() - 300) // 2
    splash.move(x, y)

    # Layout
    layout = QVBoxLayout(splash)
    layout.setContentsMargins(0, 0, 0, 0)

    # Content
    content = QFrame()
    content.setStyleSheet("""
        QFrame {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0B0B12, stop:1 #11111B);
            border-radius: 20px;
            border: 1px solid #303044;
        }
    """)
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(40, 40, 40, 40)
    content_layout.setSpacing(20)

    # Logo
    logo = QLabel("✦")
    logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    logo.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
    logo.setStyleSheet("color: #8B7AFF; background: transparent;")

    # Title
    title = QLabel("AVORA")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("""
        font-size: 42px;
        font-weight: 800;
        letter-spacing: -1px;
        color: #F5F5F5;
        background: transparent;
    """)

    # Subtitle
    subtitle = QLabel("Intelligence, redefined.")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle.setStyleSheet("""
        font-size: 13px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #858599;
        background: transparent;
    """)

    content_layout.addStretch()
    content_layout.addWidget(logo)
    content_layout.addWidget(title)
    content_layout.addWidget(subtitle)
    content_layout.addStretch()

    layout.addWidget(content)

    # Show splash
    splash.show()
    QApplication.processEvents()

    return splash


def main():

    app = QApplication(
        sys.argv
    )

    app.setStyle(
        "Fusion"
    )

    app.setApplicationName(
        "Avora"
    )

    app.setOrganizationName(
        "Avora"
    )

    app.setWindowIcon(
        QIcon(
            str(ICON_PATH)
        )
    )

    try:
        APP_DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )
    except Exception:
        pass

    # Show splash screen
    splash = None
    try:
        splash = show_splash_screen()
    except Exception:
        splash = None

    # ====================================================
    # INITIALIZE AVORA SYSTEMS
    # ====================================================

    try:
        init_safety()
    except Exception as error:
        print("[AVORA SAFETY INIT ERROR]", error)

    try:
        init_hotkey()
    except Exception as error:
        print("[AVORA HOTKEY INIT ERROR]", error)

    try:
        init_clipboard()
    except Exception as error:
        print("[AVORA CLIPBOARD INIT ERROR]", error)

    try:
        init_automation()
    except Exception as error:
        print("[AVORA AUTOMATION INIT ERROR]", error)

    # ====================================================
    # INITIALIZE CORE ENGINES (modular architecture)
    # ====================================================

    try:
        bootstrap_results = get_bootstrap().start()
        skills_count = bootstrap_results.get("skills_registered", 0)
        print(f"[CORE] Bootstrap complete - {skills_count} skills registered")
    except Exception as error:
        print("[CORE] Bootstrap error:", error)

    # ====================================================
    # MAIN WINDOW
    # ====================================================

    # Apply theme at startup
    try:
        apply_theme_to_app()
    except Exception as error:
        print("[THEME] Startup apply error:", error)

    window = MainWindow()

    # Hide splash and show window
    if splash is not None:
        try:
            QTimer.singleShot(800, lambda: splash.close())
        except Exception:
            pass

    window.show()

    window.user_input.setFocus()

    # ====================================================
    # START ACTIVITY MONITOR
    # ====================================================

    try:
        window.start_activity_monitor()
    except Exception as e:
        print("[ACTIVITY] Failed to start:", e)

    # ====================================================
    # INITIALIZE COMPANION INTELLIGENCE
    # ====================================================

    try:
        window.start_companion()
    except Exception as e:
        print("[COMPANION] Failed to start:", e)

    # ====================================================
    # INITIALIZE MISSIONS SYSTEM
    # ====================================================

    try:
        from mission_tracker import get_mission_tracker
        from mission_ui import WelcomeBackWidget
        mission_tracker = get_mission_tracker()
        print("[MISSIONS] Mission system initialized")
        
        # Show welcome back widget if there are active missions
        if mission_tracker.get_active_missions():
            welcome_back = WelcomeBackWidget(window)
            if welcome_back.parent() is None:
                welcome_back.setParent(window)
            welcome_back.show()
            print("[MISSIONS] Active missions found - showing welcome back")
    except Exception as e:
        print("[MISSIONS] Failed to initialize:", e)

    # ====================================================
    # START SCREEN AWARENESS IF ENABLED
    # ====================================================

    try:
        from settings import is_screen_awareness_enabled
        if is_screen_awareness_enabled():
            window.start_screen_awareness()
            print("[SCREEN AWARENESS] Auto-started")
    except Exception as e:
        print("[SCREEN AWARENESS] Failed to auto-start:", e)

    # ====================================================
    # AVORA STATUS CHECK TIMER
    # ====================================================

    panic_timer = QTimer()
    panic_timer.timeout.connect(lambda: window._check_panic_status())
    panic_timer.start(500)

    # ====================================================
    # CLEANUP ON EXIT
    # ====================================================

    def cleanup_on_exit():
        try:
            window.stop_companion()
        except Exception:
            pass
        try:
            window.stop_activity_monitor()
        except Exception:
            pass
        try:
            get_bootstrap().stop()
        except Exception:
            pass

    app.aboutToQuit.connect(cleanup_on_exit)

    sys.exit(
        app.exec()
    )


# ============================================================
# RUN
# ============================================================


if __name__ == "__main__":

    main()
    def save_window_geometry(self):
        """Save window geometry and position to settings."""
        try:
            geometry = self.saveGeometry()
            geometry_str = geometry.toBase64().data().decode('utf-8') if geometry else ""
            settings = get_setting("window_geometry", {})
            settings["geometry"] = geometry_str
            set_setting("window_geometry", settings)
        except Exception as e:
            print("Save window geometry error:", e)

    def restore_window_geometry(self):
        """Restore window geometry and position from settings, with multi-monitor handling."""
        try:
            settings = get_setting("window_geometry", {})
            geometry_str = settings.get("geometry", "")
            if geometry_str:
                geometry = Qt.QByteArray.fromBase64(geometry_str.encode('utf-8'))
                if geometry.isValid():
                    self.restoreGeometry(geometry)
                else:
                    # Position outside current monitor - use center screen
                    available = self.screen().availableGeometry()
                    self.resize(1200, 800)
                    self.move(
                        (available.width() - 1200) // 2,
                        (available.height() - 800) // 2
                    )
            else:
                # No saved geometry - center on current screen
                available = self.screen().availableGeometry()
                self.resize(1200, 800)
                self.move(
                    (available.width() - 1200) // 2,
                    (available.height() - 800) // 2
            )
        except Exception as e:
            print("Restore window geometry error:", e)
            # Fallback: center on screen
            available = self.screen().availableGeometry()
            self.resize(1200, 800)
            self.move(
                (available.width() - 1200) // 2,
                (available.height() - 800) // 2
            )