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
import tempfile
import traceback
import uuid
from datetime import datetime
from pathlib import Path

from activity_monitor import (
    ActivityMonitor,
)
from app_paths import (
    APP_DATA_DIR,
    ICON_PATH,
)
from app_utils import (
    clean_ai_reply,
    format_status,
    sanitize_user_text,
)
from avora_automation import (
    initialize as init_automation,
)
from avora_clipboard import (
    initialize as init_clipboard,
)
from avora_clipboard import (
    stop_clipboard_monitor,
)
from avora_hotkey import (
    initialize as init_hotkey,
)
from avora_hotkey import (
    stop_hotkey_listener,
)

# ============================================================
# AVORA SYSTEMS
# ============================================================
from avora_safety import (
    initialize as init_safety,
)
from avora_safety import (
    is_panic,
    log_activity,
)
from character import (
    Character,
)
from chat_sidebar import (
    ChatSidebar,
    generate_title_from_messages,
    load_conversations,
    save_conversations,
)
from companion_behavior import (
    CompanionBehaviorController,
)
from companion_intelligence import (
    CompanionIntelligence,
    CompanionMood,
)
from core.bootstrap import (
    get_bootstrap,
)

# ============================================================
# PY SIDE 6
# ============================================================
from PySide6.QtCore import (
    QEvent,
    QPoint,
    Qt,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QIcon,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from settings import (
    add_settings_listener,
    get_setting,
    is_character_enabled,
    is_voice_enabled,
    set_setting,
)
from skills.chat_worker import (
    RegenerateWorker,
    StreamingWorker,
)
from skills.markdown_renderer import (
    markdown_to_html,
)
from theme import (
    add_theme_listener,
    apply_theme_to_app,
    generate_qss,
    get_current_theme,
    is_dark_mode,
)

# ============================================================
# PROJECT IMPORTS
# ============================================================
from voice import (
    is_recording,
    listen_start,
    listen_stop,
    speak,
    stop_speaking,
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
# ================================================================
# CHAT COMPOSER (MULTILINE, CHATGPT-STYLE)
# ================================================================

class ChatComposer(QTextEdit):
    """
    Multiline message composer.

    • Enter  -> send the message
    • Shift + Enter -> insert a new line
    • Grows with content up to a sensible maximum height,
      then scrolls internally.
    """

    MIN_HEIGHT = 46
    MAX_HEIGHT = 160

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("InputBox")
        self.setAcceptRichText(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(self.MIN_HEIGHT)

        if hasattr(self, "setPlaceholderText"):
            self.setPlaceholderText("Message your AI Friend...")

        # Handler resolved dynamically at keypress time so the rest of the
        # app can keep overriding/re-wiring send logic safely.
        self.send_handler = None
        self.send_owner = None

        self.textChanged.connect(self._auto_resize)
        QTimer.singleShot(0, self._auto_resize)

    def _resolve_send_handler(self):
        """Find the current send callback (owner lookup happens live)."""

        owner = getattr(self, "send_owner", None)

        if owner is not None:
            handler = getattr(owner, "send_message", None)

            if callable(handler):
                return handler

        return self.send_handler if callable(self.send_handler) else None

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            handler = self._resolve_send_handler()

            if handler is not None:
                handler()
                return

        super().keyPressEvent(event)

    def _auto_resize(self):
        try:
            doc_height = int(self.document().size().height()) + 12
            new_height = max(self.MIN_HEIGHT, min(doc_height, self.MAX_HEIGHT))
            if new_height != self.height():
                self.setFixedHeight(new_height)
        except Exception:
            pass

    # ------------------------------------------------------------
    # Compatibility API — the rest of the app used the old single
    # line QLineEdit interface. These shims keep every existing
    # handler working unchanged.
    # ------------------------------------------------------------

    def text(self):
        return self.toPlainText()

    def setText(self, text):
        self.setPlainText(str(text))

    def clear(self):
        self.setPlainText("")


class MainWindow(QWidget):
    # Used to control character talking animation.
    character_talking_signal = Signal(bool)

    # Used to marshal companion observations to the main thread safely.
    _activity_changed_signal = Signal(dict)

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(parent)

        # ====================================================
        # APPLICATION STATE
        # ====================================================

        self.worker = None

        self.settings_window = None

        self.thinking_label = None

        self.is_processing = False

        self.is_closing = False

        self.voice_enabled = bool(is_voice_enabled())

        self.character_enabled = bool(is_character_enabled())

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

        # Cursor glow effect
        self._cursor_glow = None
        self._cursor_glow_target = None
        self._cursor_glow_timer = None
        self._cursor_glow_anim = None

        # Chat Sidebar System
        self.chats = []
        self.active_chat_id = None
        self.chat_sidebar = None
        self._updating_chat = False

        self._current_message = None

        # ====================================================
        # SIGNALS
        # ====================================================

        self.character_talking_signal.connect(self.character_talking)

        # ====================================================
        # WINDOW
        # ====================================================

        self.setWindowTitle("AVORA AI")

        self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.setObjectName("MainWindow")

        self.resize(1200, 800)

        self.setMinimumSize(950, 700)

        # ====================================================
        # UI
        # ====================================================

        self.apply_styles()

        self.create_neural_background()

        self.create_cursor_glow()

        self.create_ui()

        self.load_chats()

        self.create_character()

        # ====================================================
        # SETTINGS LISTENER
        # ====================================================

        try:
            add_settings_listener(self.on_setting_changed)

        except Exception as error:
            print("SETTINGS LISTENER ERROR:", error)

        # ====================================================
        # THEME LISTENER
        # ====================================================

        try:
            add_theme_listener(self.on_theme_changed)

        except Exception as error:
            print("THEME LISTENER ERROR:", error)

    # ========================================================
    # THEME CHANGE
    # ========================================================

    def on_theme_changed(
        self,
        theme,
    ):

        self.setStyleSheet(generate_qss())

        # Refresh character theme colors
        if self.character is not None:
            try:
                self.character.update_theme()

            except Exception as error:
                print("CHARACTER THEME ERROR:", error)

    # ========================================================
    # STYLES
    # ========================================================

    def apply_styles(
        self,
    ):

        self.setStyleSheet(generate_qss())

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
            self.neural_nodes.append(
                {
                    "x": random.randint(0, self.width()),
                    "y": random.randint(0, self.height()),
                    "vx": random.uniform(-0.3, 0.3),
                    "vy": random.uniform(-0.3, 0.3),
                    "size": random.uniform(2.0, 5.0),
                    "opacity": random.uniform(0.3, 0.8),
                }
            )

        self.neural_timer = QTimer()
        self.neural_timer.timeout.connect(self.animate_neural_background)
        self.neural_timer.start(100)  # 10 FPS - smoother, less CPU

    def animate_neural_background(self):
        """Animate neural nodes and repaint."""
        if self.is_closing:
            return

        # Reduced motion: keep the ambience completely still.
        try:
            from settings import get_setting

            if not get_setting("appearance.show_message_animations", True):
                return

        except Exception:
            pass

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

        # The ambience is painted directly on the main window, so request a
        # repaint of the window itself for the next animation frame.
        self.update()

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
            # Paint the ambience onto the window itself (behind all child
            # widgets). Painting a child widget (neural_canvas) directly from
            # the window's paintEvent bypasses the child's own paint path and
            # triggers "QWidget::paintEngine: Should no longer be called".
            painter = QPainter(self)
        except Exception:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get theme colors
        theme = get_current_theme()
        is_dark = is_dark_mode()

        node_color = QColor(0, 255, 136)  # Accent color
        connection_color = QColor(0, 255, 136)

        # Draw connections
        max_dist = 180
        painter.setPen(
            QColor(
                connection_color.red(),
                connection_color.green(),
                connection_color.blue(),
                25,
            )
        )
        for i, node1 in enumerate(self.neural_nodes):
            for j, node2 in enumerate(self.neural_nodes):
                if i >= j:
                    continue
                dx = node1["x"] - node2["x"]
                dy = node1["y"] - node2["y"]
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < max_dist:
                    alpha = int(255 * (1 - dist / max_dist) * 0.15)
                    painter.setPen(
                        QColor(
                            connection_color.red(),
                            connection_color.green(),
                            connection_color.blue(),
                            alpha,
                        )
                    )
                    painter.drawLine(
                        int(node1["x"]),
                        int(node1["y"]),
                        int(node2["x"]),
                        int(node2["y"]),
                    )

        # Draw nodes
        painter.setBrush(node_color)
        for node in self.neural_nodes:
            alpha = int(255 * node.get("opacity", 0.5) * 0.6)
            painter.setPen(
                QColor(node_color.red(), node_color.green(), node_color.blue(), alpha)
            )
            painter.drawEllipse(
                int(node["x"]), int(node["y"]), int(node["size"]), int(node["size"])
            )

        painter.end()

    def mouseMoveEvent(self, event):
        """Track mouse position for neural interaction."""
        self.mouse_pos = event.pos()
        if self._cursor_glow_target is None:
            self._cursor_glow_target = event.pos()
        else:
            self._cursor_glow_target = event.pos()
        super().mouseMoveEvent(event)

    # ========================================================
    # CURSOR GLOW
    # ========================================================

    def create_cursor_glow(self):
        """Create a soft neon-green cursor-following glow."""
        if self._cursor_glow is not None:
            return

        glow = QWidget(self)
        glow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        glow.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        glow.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)
        glow.setFixedSize(320, 320)
        glow.hide()

        effect = QGraphicsDropShadowEffect(glow)
        effect.setBlurRadius(120)
        effect.setOffset(0, 0)
        effect.setColor(QColor(0, 255, 136, 60))
        glow.setGraphicsEffect(effect)

        self._cursor_glow = glow
        self._cursor_glow_pos = QPoint(-200, -200)
        self._cursor_glow_target = None

        self._cursor_glow_timer = QTimer(self)
        self._cursor_glow_timer.timeout.connect(self._update_cursor_glow)
        self._cursor_glow_timer.start(16)

    def _update_cursor_glow(self):
        """Smoothly interpolate cursor glow toward target."""
        if self._cursor_glow is None:
            return

        if self._cursor_glow_target is None:
            self._cursor_glow.hide()
            return

        current = self._cursor_glow_pos
        target = self._cursor_glow_target

        dx = target.x() - current.x()
        dy = target.y() - current.y()

        if abs(dx) < 1 and abs(dy) < 1:
            self._cursor_glow_pos = target
        else:
            self._cursor_glow_pos = QPoint(
                int(current.x() + dx * 0.18),
                int(current.y() + dy * 0.18),
            )

        self._cursor_glow.move(
            self._cursor_glow_pos.x() - 160,
            self._cursor_glow_pos.y() - 160,
        )
        self._cursor_glow.show()
        self._cursor_glow.raise_()

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
    # SLIDE-DOWN-TO-CLOSE GESTURE
    # ========================================================

    def _get_current_screen(self):
        """Get the screen where AVORA is currently located."""
        screen = self.screen()
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        return screen

    def mousePressEvent(self, event):
        """Handle mouse press."""
        self.mouse_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move."""
        self.mouse_pos = event.pos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        super().mouseReleaseEvent(event)

    def changeEvent(self, event):
        """Pause expensive animations when minimized/hidden to save CPU.

        The character is deliberately EXCLUDED from this pause: a desktop
        companion must keep animating while the main window is minimized.
        On minimize the character is detached into its independent
        floating companion window (see enter_compact_character_mode), so
        it stays visible and its paint loop keeps producing frames. On
        restore it is reattached without restarting its timers.
        """
        try:
            if event.type() == QEvent.Type.WindowStateChange:
                is_min = bool(self.windowState() & Qt.WindowState.WindowMinimized)
                for name in ("neural_timer", "_cursor_glow_timer"):
                    t = getattr(self, name, None)
                    if t is not None:
                        if is_min:
                            if t.isActive():
                                t.stop()
                        else:
                            if not t.isActive():
                                t.start(100 if name == "neural_timer" else 16)
                # Character visibility across minimize/restore. Only act on
                # actual minimized-state transitions (Windows fires
                # WindowStateChange for activation changes too).
                if is_min != getattr(self, "_character_was_minimized", False):
                    self._character_was_minimized = is_min
                    self._handle_minimize_transition(is_min)
            elif event.type() == QEvent.Type.Hide:
                for name in ("neural_timer", "_cursor_glow_timer"):
                    t = getattr(self, name, None)
                    if t is not None and t.isActive():
                        t.stop()
            elif event.type() == QEvent.Type.Show:
                for name, interval in (("neural_timer", 100), ("_cursor_glow_timer", 16)):
                    t = getattr(self, name, None)
                    if t is not None and not t.isActive() and not self.isMinimized():
                        t.start(interval)
        except Exception:
            pass
        super().changeEvent(event)

    def _handle_minimize_transition(self, minimized: bool):
        """Keep the companion alive across main-window minimize/restore.

        minimized=True  → detach the character into its floating
                          always-on-top companion window so it stays
                          visible and keeps animating.
        minimized=False → reattach it to the main window (timers are
                          never stopped, so no restart/reset occurs).
        """
        if self.character is None:
            return
        try:
            if minimized:
                if not self.compact_character_mode and self.character.isVisible():
                    self._minimize_compacted = True
                    self.enter_compact_character_mode()
            else:
                if getattr(self, "_minimize_compacted", False):
                    self._minimize_compacted = False
                    self.restore_character_to_window()
        except Exception:
            pass

    # ========================================================
    # CREATE UI
    # ========================================================

    def create_ui(
        self,
    ):

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.setSpacing(0)

        # ====================================================
        # SIDEBAR
        # ====================================================

        self.sidebar = QFrame()

        self.sidebar.setObjectName("Sidebar")

        self.sidebar.setFixedWidth(290)

        self.apply_shadow(
            self.sidebar,
            blur=24,
            offset=0,
            alpha=90,
        )

        sidebar_layout = QVBoxLayout(self.sidebar)

        sidebar_layout.setContentsMargins(18, 18, 18, 16)

        sidebar_layout.setSpacing(8)

        # ====================================================
        # LOGO
        # ====================================================

        logo = QLabel("✦  AVORA")

        logo.setObjectName("Logo")

        logo.setStyleSheet("""
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.5px;
            padding: 4px 0;
        """)

        subtitle = QLabel("Intelligence, redefined.")

        subtitle.setObjectName("SubText")

        subtitle.setStyleSheet("""
            font-size: 10px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            font-weight: 500;
        """)

        sidebar_layout.addWidget(logo)

        sidebar_layout.addWidget(subtitle)

        sidebar_layout.addSpacing(16)

        # ====================================================
        # NEW CHAT (single primary action)
        # ====================================================

        self.new_chat_button = QPushButton("＋   New Chat")

        self.new_chat_button.setObjectName("NewChatButton")

        self.new_chat_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.new_chat_button.setFixedHeight(38)

        self.new_chat_button.clicked.connect(self.create_new_chat)

        self.new_chat_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00CC6A, stop:1 #00FF88);
                border: none;
                border-radius: 10px;
                padding: 8px 12px;
                color: #030703;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00DD77, stop:1 #33FFAA);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00AA55, stop:1 #00DD77);
            }
        """)

        sidebar_layout.addWidget(self.new_chat_button)

        # ====================================================
        # VOICE
        # ====================================================

        self.voice_button = QPushButton()

        self.voice_button.setObjectName("VoiceButton")

        self.voice_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.voice_button.setFixedHeight(32)

        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 4px 10px;
                color: #9A9AAC;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #F5F5F5;
            }
            QPushButton[listening="true"] {
                color: #FF6B6B;
            }
        """)

        self.voice_button.clicked.connect(self.toggle_voice)

        self.update_voice_button()

        sidebar_layout.addWidget(self.voice_button)

        # ====================================================
        # SETTINGS
        # ====================================================

        self.settings_button = QPushButton("⚙️   Settings")

        self.settings_button.setObjectName("SettingsButton")

        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.settings_button.setFixedHeight(32)

        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 4px 10px;
                color: #9A9AAC;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #F5F5F5;
            }
        """)

        self.settings_button.clicked.connect(self.open_settings)

        sidebar_layout.addWidget(self.settings_button)

        sidebar_layout.addSpacing(6)

        # ====================================================
        # CHAT SIDEBAR (RECENT CHATS)
        # ====================================================

        self.chat_sidebar = ChatSidebar(self.sidebar)

        # Single primary New Chat action lives at the top of the sidebar;
        # hide the duplicate button inside the recent-chats panel (its
        # signal stays wired so nothing else breaks).
        try:
            self.chat_sidebar.new_chat_btn.setVisible(False)

        except Exception:
            pass

        self.chat_sidebar.chat_selected.connect(self.switch_chat)

        self.chat_sidebar.new_chat_requested.connect(self.create_new_chat)

        self.chat_sidebar.chat_deleted.connect(self._on_chat_deleted)

        sidebar_layout.addWidget(
            self.chat_sidebar,
            1,
        )

        sidebar_layout.addSpacing(15)

        sidebar_layout.addStretch()

        # ====================================================
        # RIGHT SIDE
        # ====================================================

        right_side = QFrame()

        right_side.setObjectName("RightSide")

        right_layout = QVBoxLayout(right_side)

        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.setSpacing(0)

        # ====================================================
        # HEADER
        # ====================================================

        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(52)
        # Header is fixed — never scrolls, subtle polish
        header.setStyleSheet("QFrame#Header { background: rgba(255,255,255,0.015); border-bottom: 1px solid rgba(255,255,255,0.06); }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_inner = QVBoxLayout()
        header_inner.setContentsMargins(0, 6, 0, 6)
        header_inner.setSpacing(1)
        header_title = QLabel("AVORA")
        header_title.setObjectName("HeaderTitle")
        header_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_inner.addWidget(header_title)
        # Status indicator ("Ready" / "Thinking" / "Error" ...)
        self.status_label = QLabel("● Ready")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            color: #65E6A5;
            font-size: 11px;
            letter-spacing: 0.6px;
            background: transparent;
        """)
        header_inner.addWidget(self.status_label)
        header_layout.addStretch(1)
        header_layout.addLayout(header_inner)
        header_layout.addStretch(1)
        right_layout.addWidget(header)

        # ====================================================
        # CHAT AREA — ONLY SCROLLABLE AREA (FIXED VIEWPORT PATTERN)
        # ROOT = overflow hidden, CHAT = overflow-y auto, COMPOSER = fixed
        # ====================================================

        self.chat_area = QScrollArea()
        self.chat_area.setObjectName("ChatArea")
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Chat area expands to fill available space between header and composer
        self.chat_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.message_widget = QWidget()
        self.message_widget.setObjectName("MessageArea")

        self.message_layout = QVBoxLayout(self.message_widget)
        # Premium vertical rhythm: comfortable top breathing room below the
        # header, side gutters, and bottom clearance above the pinned composer.
        self.message_layout.setContentsMargins(24, 28, 24, 24)
        self.message_layout.setSpacing(14)
        self.message_layout.addStretch()

        self.chat_area.setWidget(self.message_widget)

        right_layout.addWidget(self.chat_area, 1)

        # Smart auto-scroll: only force scroll if user is near bottom
        self._auto_scroll_enabled = True
        self.chat_area.verticalScrollBar().valueChanged.connect(self._on_chat_scroll)

        # Floating "scroll to latest" button (appears when user scrolls up)
        from PySide6.QtWidgets import QPushButton as _PB
        self._scroll_down_btn = _PB("↓", self.chat_area.viewport())
        self._scroll_down_btn.setObjectName("ScrollDownBtn")
        self._scroll_down_btn.setFixedSize(36, 36)
        self._scroll_down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scroll_down_btn.setStyleSheet("""
            QPushButton#ScrollDownBtn {
                background: rgba(0,255,136,0.16);
                border: 1px solid rgba(0,255,136,0.28);
                border-radius: 18px;
                color: #E6FFEC;
                font-size: 16px;
            }
            QPushButton#ScrollDownBtn:hover {
                background: rgba(0,255,136,0.26);
                border-color: rgba(0,255,136,0.45);
            }
        """)
        self._scroll_down_btn.clicked.connect(lambda: self.scroll_to_bottom(force=True))
        self._scroll_down_btn.hide()
        # Position on resize
        self._chat_area_prev_resize = self.chat_area.viewport().size

        # ====================================================
        # COMPOSER — ALWAYS VISIBLE, NEVER INSIDE SCROLL
        # ====================================================

        input_outer = QFrame()
        input_outer.setObjectName("ComposerOuter")
        input_outer.setFixedHeight(84)
        # Composer outer: subtle top border, fixed — never scrolls away
        input_outer.setStyleSheet("QFrame#ComposerOuter { background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.06); }")
        input_layout = QHBoxLayout(input_outer)
        input_layout.setContentsMargins(16, 10, 16, 14)
        input_layout.setSpacing(0)

        self.input_container = QFrame()
        self.input_container.setObjectName("InputContainer")
        self.apply_shadow(
            self.input_container,
            blur=18,
            offset=0,
            alpha=80,
        )
        input_container_layout = QHBoxLayout(self.input_container)
        input_container_layout.setContentsMargins(8, 5, 8, 5)
        input_container_layout.setSpacing(6)

        self.user_input = ChatComposer()
        self.user_input.setObjectName("InputBox")
        self.user_input.setPlaceholderText("Message your AI Friend...")
        self.user_input.send_handler = self.send_message
        self.user_input.send_owner = self

        self.attach_button = QPushButton("📎")
        self.attach_button.setObjectName("AttachButton")
        self.attach_button.setFixedSize(36, 36)
        self.attach_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_button.setToolTip("Attach file")
        self.attach_button.clicked.connect(self._attach_file)
        self.attach_button.setStyleSheet("""
            QPushButton#AttachButton {
                background: transparent;
                border: none;
                border-radius: 10px;
                color: #8A8A99;
                font-size: 16px;
            }
            QPushButton#AttachButton:hover {
                background: rgba(255,255,255,0.06);
                color: #E6FFEC;
            }
        """)
        self.attached_files = []

        self.send_button = QPushButton("➤")
        self.send_button.setObjectName("SendButton")
        self.send_button.setFixedSize(40, 36)
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.setToolTip("Send message (Enter)")
        self.send_button.clicked.connect(self.send_message)

        self.mic_button = QPushButton("🎤")
        self.mic_button.setObjectName("MicButton")
        self.mic_button.setFixedSize(40, 36)
        self.mic_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_button.setToolTip("Voice input")
        self.mic_button.clicked.connect(self.toggle_voice_input)
        self.is_listening = False

        # Order: attach — input — mic — send  (chatgpt-style)
        input_container_layout.addWidget(self.attach_button)
        input_container_layout.addWidget(self.user_input, 1)
        input_container_layout.addWidget(self.mic_button)
        input_container_layout.addWidget(self.send_button)

        input_layout.addWidget(self.input_container)

        right_layout.addWidget(input_outer)

        # ====================================================
        # ADD TO WINDOW
        # ====================================================

        main_layout.addWidget(self.sidebar)

        main_layout.addWidget(right_side, 1)

        # ====================================================
        # INITIAL STATE
        # ====================================================

        self.show_empty_state()

        try:
            self.update_status(
                "ready",
                "Ready",
            )
        except Exception:
            pass

        # The welcome is integrated into the empty-state design above.
        # No separate floating greeting bubble is added to the chat flow.

    # ========================================================
    # STYLES
    # ========================================================

    # ========================================================
    # EMPTY STATE (FIRST-USE CONVERSATION)
    # ========================================================

    def show_empty_state(
        self,
    ):
        """
        Centered welcome shown for a fresh/empty conversation.
        Replaced naturally by real messages as they arrive.
        """

        container = QWidget()

        container.setObjectName("EmptyState")

        layout = QVBoxLayout(container)

        layout.setContentsMargins(16, 48, 16, 24)

        layout.setSpacing(12)

        icon = QLabel("✦")

        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon.setStyleSheet("""
            font-size: 42px;
            color: #00CC6A;
            background: transparent;
        """)

        title = QLabel("How can I help you today?")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #FFFFFF;
            background: transparent;
        """)

        subtitle = QLabel(
            "Ask anything — Enter sends your message, "
            "Shift + Enter adds a new line."
        )

        subtitle.setWordWrap(True)

        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle.setStyleSheet("""
            font-size: 13px;
            color: #8A8A99;
            background: transparent;
        """)

        layout.addWidget(icon)

        layout.addWidget(title)

        layout.addWidget(subtitle)

        layout.addStretch()

        self.message_layout.insertWidget(self.message_layout.count() - 1, container)

        self.empty_state = container

        QTimer.singleShot(0, lambda: self._center_empty_state(container))

    def _update_empty_state(self):
        """Show the welcome state for an empty conversation, otherwise hide it."""

        empty = getattr(self, "empty_state", None)

        if empty is None:
            return

        has_messages = self.message_layout.count() > 1

        try:
            empty.setVisible(not has_messages)

        except RuntimeError:
            # Widget was deleted (e.g. new_chat cleanup) — recreate it.
            self.empty_state = None

            if not has_messages:
                self.show_empty_state()

    def _center_empty_state(self, container):
        """Vertically center the empty state within the chat area."""

        if not container.isVisible():
            return

        viewport_height = self.chat_area.viewport().height()

        total_height = container.sizeHint().height()

        top_margin = max(0, int((viewport_height - total_height) / 2.5))

        container.layout().setContentsMargins(16, top_margin, 16, 24)

    def apply_shadow(
        self,
        widget,
        blur=24,
        offset=0,
        alpha=120,
    ):

        effect = QGraphicsDropShadowEffect(widget)

        effect.setBlurRadius(blur)

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

        widget.setGraphicsEffect(effect)

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
            self.character = Character(parent=self)

        except TypeError:
            try:
                self.character = Character()

            except Exception as error:
                print("CHARACTER CREATION ERROR:", error)

                self.character = None

                return

        # --- FIX: Make character an independent top-level window
        # so that minimizing the main window does NOT suppress
        # the character's paint events / animation timer.
        # Without this, the character is a QWidget child of the
        # MainWindow and its painting is suspended when the
        # parent is minimized/hidden.
        try:
            from PySide6.QtCore import Qt

            # Remove any parent-child relationship so the character
            # becomes a genuine independent window.
            if self.character.parent() is not None:
                self.character.setParent(None)
            # Promote to a true top-level Qt window.
            self.character.setWindowFlags(
                self.character.windowFlags()
                | Qt.Window
            )
            # Ensure the window stays on top of all other windows
            # so the companion is always visible.
            self.character.setWindowFlags(
                self.character.windowFlags()
                | Qt.WindowStaysOnTopHint
            )
        except Exception:
            pass  # non-critical — character still works as child

        self.character.show()

        self.character.raise_()

        self.character.clicked.connect(self._on_character_clicked)

        self.character.restore_requested.connect(self.save_companion_position)

        self.character_talking_signal.connect(self.character_talking)

        self._activity_changed_signal.connect(self._apply_companion_observation)

        self.position_character()

        try:
            self.character.apply_companion_settings()

            self.restore_companion_position()

        except Exception:
            pass

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
            self.activity_monitor.add_listener(self.on_activity_changed)
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
                activity_name = (
                    activity.value if hasattr(activity, "value") else str(activity)
                )
                idle_minutes = (
                    self.activity_monitor.idle_minutes if self.activity_monitor else 0.0
                )
                process_name = (
                    self.activity_monitor.process_name if self.activity_monitor else ""
                )

                observation = self.companion.cycle(
                    activity_type=activity_name,
                    window_title=title,
                    process_name=process_name,
                    idle_minutes=idle_minutes,
                    is_processing=self.is_processing,
                    is_voice_active=self.is_listening,
                )

                # Marshal observation to main thread for UI updates
                self._activity_changed_signal.emit(
                    observation if isinstance(observation, dict) else {}
                )
        except Exception as e:
            print("[COMPANION] Cycle error:", e)

    def _apply_companion_observation(self, observation: dict):
        """Apply companion observation to character and UI."""
        if not observation:
            return

        # 1. Update character emotion
        if self.character is not None:
            mood_value = (
                observation.get("mood", CompanionMood.NEUTRAL).value
                if hasattr(observation.get("mood"), "value")
                else str(observation.get("mood", "neutral"))
            )
            intensity = observation.get("mood_intensity", 0.5)

            # Check for intervention
            intervention = observation.get("intervention")
            if intervention:
                char_emotion = intervention.get("character_emotion", "idle")
                message = intervention.get("message")

                if message and observation.get("silent_mode") is False:
                    self.character_call(
                        "react_naturally", mood_value, intensity, False, message
                    )
                    if self.behavior_controller is not None:
                        self.behavior_controller.show_speech_bubble(message)
                else:
                    # Silent awareness - just change expression
                    self.character_call(
                        "react_naturally", mood_value, intensity, True, None
                    )
            else:
                # No intervention - just update expression silently
                self.character_call(
                    "react_naturally", mood_value, intensity, True, None
                )

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
            state_label = (
                user_state.value if hasattr(user_state, "value") else str(user_state)
            )
            self.update_status("ready", str(state_label).capitalize())

    def start_companion(self):
        """Initialize and start the Companion Intelligence system."""
        try:
            personality = get_setting("personality.current_personality", "friendly")
            self.companion = CompanionIntelligence(
                activity_monitor=self.activity_monitor,
                personality=personality,
            )
            # Register as global singleton so context_provider reads the same live state
            try:
                from companion_intelligence import set_companion_intelligence
                set_companion_intelligence(self.companion)
            except Exception:
                pass
            print("[COMPANION] Intelligence system initialized")

            self.behavior_controller = CompanionBehaviorController(self)
            self.behavior_controller.start()

            # Companion message bridge: task events -> short natural
            # character messages through the existing speech bubble.
            try:
                from companion_messages import CompanionMessenger
                self.companion_messenger = CompanionMessenger(self.behavior_controller)
            except Exception:
                self.companion_messenger = None

            self._start_companion_timer()
        except Exception as e:
            print("[COMPANION] Failed to initialize:", e)

    def start_screen_awareness(self):
        """Initialize and start the Screen Awareness system."""
        try:
            if not hasattr(self, "screen_awareness") or self.screen_awareness is None:
                from screen_awareness import ScreenAwareness

                self.screen_awareness = ScreenAwareness(main_window=self)
            self.screen_awareness.start()
            print("[SCREEN AWARENESS] Started")
        except Exception as e:
            print("[SCREEN AWARENESS] Failed to start:", e)

    def stop_screen_awareness(self):
        """Stop the screen awareness system."""
        if hasattr(self, "screen_awareness") and self.screen_awareness is not None:
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
        try:
            from companion_intelligence import set_companion_intelligence
            set_companion_intelligence(None)
        except Exception:
            pass
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
            activity_name = (
                activity.value if hasattr(activity, "value") else str(activity)
            )
            observation = self.companion.cycle(
                activity_type=activity_name,
                window_title=self.activity_monitor.window_title,
                process_name=self.activity_monitor.process_name,
                idle_minutes=self.activity_monitor.idle_minutes,
                is_processing=self.is_processing,
                is_voice_active=getattr(self, "is_listening", False),
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

            self.settings_window.setWindowTitle("AI Friend Settings")

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

            self.settings_window.settings_changed.connect(self.on_setting_changed)

            self.settings_window.navigate_back.connect(self.back_to_chat)

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
            print("SETTINGS IMPORT ERROR:", error)

            QMessageBox.warning(
                self, "Settings Error", "settings_ui.py could not be loaded."
            )

        except Exception as error:
            print("SETTINGS WINDOW ERROR:", error)

            traceback.print_exc()

            QMessageBox.warning(self, "Settings Error", str(error))

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

        print(f"SETTING CHANGED: {path} {old_value} -> {new_value}")

        # ----------------------------------------------------
        # VOICE
        # ----------------------------------------------------

        if path == "voice.enabled":
            self.voice_enabled = bool(new_value)

            self.update_voice_button()

            if not self.voice_enabled:
                try:
                    stop_speaking()

                except Exception:
                    pass

                self.character_talking_signal.emit(False)

        # ----------------------------------------------------
        # CHARACTER
        # ----------------------------------------------------

        elif path == "character.enabled":
            self.update_character_visibility(bool(new_value))

        # ----------------------------------------------------
        # VOICE AUTO STOP
        # ----------------------------------------------------

        elif path == "voice.auto_stop_previous":
            pass

        # ----------------------------------------------------
        # VOICE PRIVACY — never auto-enable microphone/wake word
        # ----------------------------------------------------

        elif path == "voice_extended.continuous_listening":
            # User toggled continuous listening in Settings — privacy:
            # never start microphone automatically. Only manual mic button
            # or explicit wake-word opt-in via UI should start listening.
            if not new_value:
                try:
                    from voice import stop_wake_word
                    stop_wake_word()
                except Exception:
                    pass
            # When enabling via Settings, do NOT call start_wake_word.
            # The user must explicitly activate it via the companion UI.

        # ----------------------------------------------------
        # CHARACTER SIZE
        # ----------------------------------------------------

        elif path == "character.size":
            self.apply_character_size(new_value)

        # ----------------------------------------------------
        # SCREEN AWARENESS
        # ----------------------------------------------------

        elif path == "screen_awareness.enabled":
            if new_value:
                self.start_screen_awareness()

            else:
                self.stop_screen_awareness()

        # ----------------------------------------------------
        # COMPANION WIDGET
        # ----------------------------------------------------

        elif path == "companion_widget.enabled":
            self.update_companion_visibility(bool(new_value))

        elif path == "companion_widget.size":
            self.apply_companion_size(new_value)

        elif path == "companion_widget.glow_intensity":
            self.apply_companion_glow(new_value)

        elif path == "companion_widget.glow_color":
            self.apply_companion_glow_color(new_value)

        elif path == "companion_widget.animation":
            self.apply_companion_animation(new_value)

        elif path in {
            "companion_widget.position_x",
            "companion_widget.position_y",
        }:
            self.restore_companion_position()

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
            getattr(self.character, "set_scale_factor", None),
        )

        if callable(method):
            try:
                method(size)

            except Exception as error:
                print("CHARACTER SIZE ERROR:", error)

        self.position_character()

    # ========================================================
    # COMPANION WIDGET
    # ========================================================

    def update_companion_visibility(
        self,
        enabled,
    ):

        if self.character is None:
            return

        if enabled:
            self.character.show()

            self.character.raise_()

            self.restore_companion_position()

        else:
            self.character.hide()

    def apply_companion_size(
        self,
        value,
    ):

        # Keep character.size in sync so both size controls share one
        # source of truth (fixes the two-key size conflict).
        try:
            from settings import set_setting

            set_setting(
                "character.size",
                float(value),
            )

        except Exception:
            pass

        if self.character is None:
            return

        try:
            size = float(value)

        except Exception:
            return

        method = getattr(
            self.character,
            "set_character_size",
            getattr(self.character, "set_scale_factor", None),
        )

        if callable(method):
            try:
                method(size)

            except Exception as error:
                print("COMPANION SIZE ERROR:", error)

        self.position_character()

    def apply_companion_glow(
        self,
        value,
    ):

        if self.character is None:
            return

        try:
            intensity = float(value)

        except Exception:
            return

        try:
            self.character.update_glow(
                intensity,
                self.character._last_glow_color or "#00FF88",
            )

        except Exception:
            pass

    def apply_companion_glow_color(
        self,
        value,
    ):

        if self.character is None:
            return

        try:
            from settings import get_setting

            intensity = float(
                get_setting(
                    "companion_widget.glow_intensity",
                    0.5,
                )
            )

        except Exception:
            intensity = 0.5

        try:
            self.character.update_glow(
                intensity,
                str(value),
            )

            self.character._last_glow_color = str(value)

        except Exception:
            pass

    def apply_companion_animation(
        self,
        value,
    ):

        if self.character is None:
            return

        try:
            self.character.update_animation(str(value))

        except Exception:
            pass

    def save_companion_position(
        self,
    ):

        if self.character is None:
            return

        try:
            from settings import set_setting

            pos = self.character.pos()

            set_setting(
                "companion_widget.position_x",
                pos.x(),
            )

            set_setting(
                "companion_widget.position_y",
                pos.y(),
            )

        except Exception:
            pass

    def restore_companion_position(
        self,
    ):

        if self.character is None:
            return

        try:
            from settings import get_setting

            x = float(
                get_setting(
                    "companion_widget.position_x",
                    -1,
                )
            )

            y = float(
                get_setting(
                    "companion_widget.position_y",
                    -1,
                )
            )

        except Exception:
            x = -1

            y = -1

        if x < 0 or y < 0:
            # Default: bottom-RIGHT corner so the companion never sits
            # on top of the sidebar (left) or the conversation column.
            margin = 16

            x = self.width() - self.character.width() - margin

            y = max(
                margin,
                self.height() - self.character.height() - margin,
            )

        self.character._user_positioned = True

        self.character.move(
            int(x),
            int(y),
        )

        self.character.raise_()

    # ========================================================
    # VOICE BUTTON
    # ========================================================

    def update_voice_button(
        self,
    ):

        if self.voice_enabled:
            self.voice_button.setText("🔊  Voice: ON")

        else:
            self.voice_button.setText("🔇  Voice: OFF")

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

        self.status_label.setText(f"● {label}")

        if state == "error":
            self.status_label.setStyleSheet("color: #FF6B6B;")

        elif state in {"thinking", "speaking", "listening"}:
            self.status_label.setStyleSheet("color: #FFD166;")

        else:
            self.status_label.setStyleSheet("color: #65E6A5;")

        if self.character is not None:
            try:
                self.character.set_ai_state(state)

            except Exception:
                pass

    # ========================================================
    # TOGGLE VOICE
    # ========================================================

    def toggle_voice(
        self,
    ):

        self.voice_enabled = not self.voice_enabled

        try:
            set_setting("voice.enabled", self.voice_enabled)

        except Exception as error:
            print("VOICE SETTING ERROR:", error)

        if not self.voice_enabled:
            try:
                stop_speaking()

            except Exception:
                pass

            self.character_talking_signal.emit(False)

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
                "Please check your microphone device.",
            )
            return

        self.is_listening = True

        self.mic_button.setText("🔴")

        self.mic_button.setProperty("listening", True)

        self.mic_button.style().unpolish(self.mic_button)

        self.mic_button.style().polish(self.mic_button)

        self.update_status(
            "listening",
            "Listening...",
        )

        self.user_input.setPlaceholderText("Listening... speak now")

    def stop_voice_input(
        self,
    ):

        self.is_listening = False

        self.mic_button.setText("🎤")

        self.mic_button.setProperty("listening", False)

        self.mic_button.style().unpolish(self.mic_button)

        self.mic_button.style().polish(self.mic_button)

        self.update_status(
            "ready",
            "Ready",
        )

        self.user_input.setPlaceholderText("Message your AI Friend...")

        # Stop recording and recognize in a background thread
        self.voice_input_worker = VoiceRecognitionWorker()
        self.voice_input_worker.result_ready.connect(self._on_voice_recognition_done)
        self.voice_input_worker.start()

    def _on_voice_recognition_done(
        self,
        text,
    ):

        if self.voice_input_worker is not None:
            self.voice_input_worker.deleteLater()
            self.voice_input_worker = None

        if text:
            self.user_input.setText(str(text))

            self.user_input.setFocus()

        else:
            QMessageBox.warning(
                self, "Microphone", "Could not understand audio.\n\nPlease try again."
            )

    # ========================================================
    # CHARACTER VISIBILITY
    # ========================================================

    def update_character_visibility(
        self,
        enabled,
    ):

        self.character_enabled = bool(enabled)

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

                self.character_talking_signal.emit(False)

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

        method = getattr(self.character, method_name, None)

        if not callable(method):
            return

        try:
            method(*args)

        except Exception as error:
            print(f"CHARACTER ERROR ({method_name}):", error)

    # ========================================================
    # CHARACTER TALKING
    # ========================================================

    def character_talking(
        self,
        talking,
    ):

        if self.character is None:
            return

        self.character_call("set_talking", bool(talking))

        if not talking:
            QTimer.singleShot(700, self.return_to_idle)

    def _animate_widget_entrance(self, widget):
        """Subtle fade/slide for new messages (respects reduced-motion)."""
        try:
            from settings import get_setting
            if not get_setting("appearance.show_message_animations", True):
                return
        except Exception:
            pass
        try:
            eff = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(eff)
            from PySide6.QtCore import QEasingCurve, QPropertyAnimation
            # Opacity animation
            anim = QPropertyAnimation(eff, b"opacity")
            anim.setDuration(280)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            # Keep reference to prevent GC
            if not hasattr(self, "_entrance_anims"):
                self._entrance_anims = []
            self._entrance_anims.append(anim)
            anim.finished.connect(lambda: self._entrance_anims.remove(anim) if anim in self._entrance_anims else None)
            eff.setOpacity(0.0)
            anim.start()
        except Exception:
            pass

    def _wrap_centered_row(self, bubble_widget, align_right=False):
        """Wrap bubble in a centered max-width container (ChatGPT-like column)."""
        # Outer row centered within scroll viewport
        outer = QWidget()
        outer.setObjectName("MessageRow")
        outer_layout = QHBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Center column — max 860px readable width
        center = QWidget()
        center.setMaximumWidth(860)
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        center_layout = QHBoxLayout(center)
        center_layout.setContentsMargins(0, 2, 0, 2)
        center_layout.setSpacing(0)

        if align_right:
            center_layout.addStretch()
            center_layout.addWidget(bubble_widget)
        else:
            # Left-aligned content that fills the centered column's width.
            # Stretch factor 1 makes the content absorb available width first
            # (capped by its maximum width) before any spacer takes space.
            center_layout.addWidget(bubble_widget, 1)
            center_layout.addStretch()

        outer_layout.addStretch()
        # Stretch factor 100: the conversation column wins all available
        # width (up to its max) BEFORE the two spacer items get any share.
        # Without this, Qt split extra space equally between the spacers and
        # the column, collapsing the conversation into a narrow floating strip.
        outer_layout.addWidget(center, 100)
        outer_layout.addStretch()
        return outer

    # ========================================================
    # ADD USER MESSAGE — POLISHED, COMPACT
    # ========================================================

    def add_user_message(self, text):
        self._update_empty_state()
        bubble = QLabel(str(text))
        bubble.setObjectName("UserBubble")
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        # ChatGPT-like max width — matches the resize-reflow formula below
        chat_width = self.chat_area.viewport().width() if self.chat_area else 800
        max_w = min(560, max(240, int(chat_width * 0.62)))
        bubble.setMaximumWidth(max_w)
        bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self._animate_widget_entrance(bubble)
        row_widget = self._wrap_centered_row(bubble, align_right=True)
        self.message_layout.insertWidget(self.message_layout.count() - 1, row_widget)
        self.scroll_to_bottom()

    # ========================================================
    # ADD AI MESSAGE (RICH MARKDOWN) — POLISHED
    # ========================================================

    def add_ai_message_rich(self, text, message_id=None, streaming=False):
        """Add a Markdown-rendered AI message using QTextBrowser."""
        self._update_empty_state()
        text_str = str(text) if text is not None else ""
        # Ghost-bubble guard: never render an empty assistant container.
        if not text_str.strip():
            return None
        browser = QTextBrowser()
        browser.setObjectName("AIBubble")
        chat_width = self.chat_area.viewport().width() if self.chat_area else 800
        max_w = min(860, max(400, int(chat_width * 0.85)))
        browser.setMaximumWidth(max_w)
        browser.setMinimumHeight(40)
        browser.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        browser.setOpenExternalLinks(True)
        browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        browser.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
        html = markdown_to_html(text_str, streaming=streaming)
        browser.setHtml(html)
        try:
            browser.document().setDocumentMargin(2)
            browser.document().setIndentWidth(12)
            # Comfortable conversation density — QTextBrowser otherwise
            # inherits the widget default (12pt) which reads too large.
            browser.document().setDefaultFont(QFont("Segoe UI", 10))
        except Exception:
            pass
        QTimer.singleShot(0, lambda: self._adjust_browser_height(browser, max_w))
        if message_id:
            browser.setProperty("message_id", message_id)
        browser.setProperty("full_text", text_str)
        # Subtle assistant identity above the content — continuous feed,
        # no boxed card around the response.
        name_label = QLabel("AVORA")
        name_label.setObjectName("AIName")
        container = QWidget()
        col = QVBoxLayout(container)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(3)
        col.addWidget(name_label)
        col.addWidget(browser)
        self._animate_widget_entrance(container)
        row_widget = self._wrap_centered_row(container, align_right=False)
        self.message_layout.insertWidget(self.message_layout.count() - 1, row_widget)
        self.scroll_to_bottom()
        return browser

    def _adjust_browser_height(self, browser, width=None):
        """Safely adjust QTextBrowser height to fit content without scrollbars."""
        try:
            doc = browser.document()
            actual_width = width or browser.maximumWidth() or 680
            doc.setTextWidth(actual_width)
            cloned = doc.clone()
            cloned.setTextWidth(actual_width)
            height = int(cloned.size().height()) + 24
            browser.setMinimumHeight(max(40, height))
            browser.setMaximumHeight(height)
            # Ensure parent row also updates
            try:
                browser.updateGeometry()
                if browser.parentWidget():
                    browser.parentWidget().updateGeometry()
            except Exception:
                pass
        except Exception:
            pass

    def _find_bubble_in_row(self, row_widget):
        """Recursively find UserBubble/AIBubble inside centered wrapper."""
        if row_widget is None:
            return None
        if row_widget.objectName() in ("UserBubble", "AIBubble"):
            return row_widget
        for child in row_widget.findChildren(QLabel):
            if child.objectName() == "UserBubble":
                return child
        for child in row_widget.findChildren(QTextBrowser):
            if child.objectName() == "AIBubble":
                return child
        return None

    def _reflow_messages(self):
        """Reflow all messages to fit the current chat area width."""
        if not self.chat_area or not self.message_layout:
            return
        chat_width = self.chat_area.viewport().width() if self.chat_area else 800
        if chat_width <= 0:
            return
        for i in range(self.message_layout.count()):
            item = self.message_layout.itemAt(i)
            row_widget = item.widget() if item else None
            if row_widget is None or row_widget.objectName() != "MessageRow":
                continue
            bubble = self._find_bubble_in_row(row_widget)
            if bubble is None:
                continue
            if bubble.objectName() == "UserBubble":
                max_w = min(560, max(240, int(chat_width * 0.62)))
                bubble.setMaximumWidth(max_w)
            elif bubble.objectName() == "AIBubble":
                # Same formula used at message creation — keeps text width
                # consistent between initial render and window resizes.
                max_w = min(860, max(400, int(chat_width * 0.85)))
                bubble.setMaximumWidth(max_w)
                QTimer.singleShot(0, lambda b=bubble, w=max_w: self._adjust_browser_height(b, w))
            # Update center wrapper max width
            for child in row_widget.findChildren(QWidget):
                if child.maximumWidth() == 860:
                    # keep centered column max width stable at 860 — no change needed
                    pass

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

        container.setObjectName("ImageBubble")

        container.setMaximumWidth(680)

        container_layout = QVBoxLayout(container)

        container_layout.setContentsMargins(8, 8, 8, 8)

        container_layout.setSpacing(8)

        # Caption label
        if caption:
            caption_label = QLabel(str(caption))

            caption_label.setWordWrap(True)

            caption_label.setStyleSheet("color: #F5F5F5; font-size: 14px;")

            container_layout.addWidget(caption_label)

        # Image label
        image_label = QLabel()

        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Load and scale image
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)

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

                image_label.setPixmap(scaled)

            else:
                image_label.setText("[Image could not be loaded]")

        else:
            image_label.setText("[Image file not found]")

        container_layout.addWidget(image_label)

        # Use centered row wrapper
        row_widget = self._wrap_centered_row(container, align_right=False)
        self.message_layout.insertWidget(self.message_layout.count() - 1, row_widget)
        self.scroll_to_bottom()

    # ========================================================
    # THINKING — integrated with centered column
    # ========================================================

    def show_thinking(self):
        if self.thinking_label is not None:
            return
        self.thinking_label = QLabel("● Creating")
        self.thinking_label.setObjectName("Typing")
        self.thinking_label.setStyleSheet("""
            font-size: 12px;
            color: #8A8A99;
            background-color: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 12px;
            padding: 6px 14px;
        """)
        self.dots_label = QLabel("")
        try:
            accent = get_current_theme().get("accent", {})
            dot_color = accent.get("default", "#00CC6A") if isinstance(accent, dict) else "#00CC6A"
        except Exception:
            dot_color = "#00CC6A"
        self.dots_label.setStyleSheet(f"font-size: 13px; color: {dot_color}; background: transparent;")
        self.dot_animation_state = 0
        self.dot_timer = QTimer()
        self.dot_timer.timeout.connect(self._update_dots_animation)
        self.dot_timer.start(480)
        try:
            if get_setting("appearance.show_message_animations", True):
                eff = QGraphicsDropShadowEffect(self.thinking_label)
                eff.setBlurRadius(0)
                eff.setColor(QColor(0, 0, 0, 0))
                self.thinking_label.setGraphicsEffect(eff)
                self._thinking_breath_dir = 1
                self._thinking_breath_opacity = 0.55
        except Exception:
            pass
        thinking_inner = QWidget()
        thinking_layout = QHBoxLayout(thinking_inner)
        thinking_layout.setContentsMargins(0, 0, 0, 0)
        thinking_layout.setSpacing(6)
        thinking_layout.addWidget(self.thinking_label)
        thinking_layout.addWidget(self.dots_label)
        thinking_layout.addStretch()
        row_widget = self._wrap_centered_row(thinking_inner, align_right=False)
        # Keep reference for removal
        self._thinking_row_widget = row_widget
        self.message_layout.insertWidget(self.message_layout.count() - 1, row_widget)
        self.scroll_to_bottom()

    def _update_dots_animation(self):
        """Animate the thinking-indicator dots (… cycling) + breathing opacity."""

        try:
            self.dot_animation_state = (self.dot_animation_state + 1) % 4
            self.dots_label.setText("." * self.dot_animation_state)
            # Subtle breathing: toggle thinking label opacity
            if hasattr(self, "_thinking_breath_opacity"):
                self._thinking_breath_opacity += 0.08 * self._thinking_breath_dir
                if self._thinking_breath_opacity >= 0.95:
                    self._thinking_breath_dir = -1
                elif self._thinking_breath_opacity <= 0.55:
                    self._thinking_breath_dir = 1
                try:
                    # Use stylesheet alpha as lightweight breathing without extra animation objects
                    alpha = int(180 * self._thinking_breath_opacity)
                    self.thinking_label.setStyleSheet(f"""
                        font-size: 12px;
                        color: rgba(138, 138, 153, {alpha});
                        background-color: rgba(255, 255, 255, 0.04);
                        border: 1px solid rgba(255, 255, 255, 0.07);
                        border-radius: 12px;
                        padding: 5px 14px;
                    """)
                except Exception:
                    pass
        except (RuntimeError, AttributeError):
            pass

    # ========================================================
    # REMOVE THINKING
    # ========================================================

    def remove_thinking(self):
        if self.thinking_label is None:
            return
        dot_timer = getattr(self, "dot_timer", None)
        if dot_timer is not None:
            try:
                dot_timer.stop()
            except RuntimeError:
                pass
            self.dot_timer = None
        # Remove the whole centered row widget, not just label
        row_widget = getattr(self, "_thinking_row_widget", None)
        if row_widget is not None:
            try:
                self.message_layout.removeWidget(row_widget)
                row_widget.setParent(None)
                row_widget.deleteLater()
            except Exception:
                pass
            self._thinking_row_widget = None
        try:
            if self.thinking_label is not None:
                self.thinking_label.deleteLater()
        except RuntimeError:
            pass
        self.thinking_label = None
        # Dots label was inside row widget, already deleted; clear refs
        if hasattr(self, "dots_label"):
            try:
                self.dots_label.deleteLater()
            except Exception:
                pass
            self.dots_label = None

    # ========================================================
    # ERROR MESSAGE — POLISHED NOTIFICATION (NOT A BUBBLE)
    # ========================================================

    def add_error_message(self, user_message=None):
        """Render a clean AVORA-branded error notification with Retry.

        No empty bubble, no duplicate error boxes — a single subtle
        notification that fits the conversation feed.
        """
        self._update_empty_state()

        note = QWidget()
        note.setObjectName("ErrorNote")
        note.setMaximumWidth(560)
        note.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(14, 10, 14, 10)
        note_layout.setSpacing(6)

        name_label = QLabel("AVORA")
        name_label.setObjectName("AIName")
        note_layout.addWidget(name_label)

        body = QLabel(
            "Sorry brooo 😭\n\n"
            "Something went wrong while processing your request.\n"
            "Please try again."
        )
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        note_layout.addWidget(body)

        # Keep retry functionality — reuse the existing regenerate path
        if user_message:
            retry_btn = QPushButton("↻ Retry")
            retry_btn.setFixedHeight(26)
            retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            retry_btn.setToolTip("Try sending your message again")
            retry_btn.setStyleSheet(
                "QPushButton {"
                "  background: transparent;"
                "  border: 1px solid rgba(255,107,107,0.35);"
                "  border-radius: 12px;"
                "  padding: 3px 12px;"
                "  color: #FF9B9B;"
                "  font-size: 11px;"
                "}"
                "QPushButton:hover {"
                "  background: rgba(255,107,107,0.10);"
                "  color: #FFC4C4;"
                "  border-color: rgba(255,107,107,0.55);"
                "}"
                "QPushButton:focus {"
                "  border-color: rgba(255,107,107,0.75);"
                "}"
            )
            retry_btn.clicked.connect(
                lambda checked, msg=user_message: self.regenerate_response(msg)
            )
            note_layout.addWidget(retry_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self._animate_widget_entrance(note)
        row_widget = self._wrap_centered_row(note, align_right=False)
        self.message_layout.insertWidget(self.message_layout.count() - 1, row_widget)
        self.scroll_to_bottom()

    # ========================================================
    # IMAGE MESSAGE
    # ========================================================

    def add_image_message(
        self,
        image_path,
    ):

        pixmap = QPixmap(image_path)

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
        label.setCursor(Qt.CursorShape.PointingHandCursor)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        layout.setAlignment(label, Qt.AlignmentFlag.AlignLeft)
        row_widget = self._wrap_centered_row(container, align_right=False)
        self.message_layout.insertWidget(self.message_layout.count() - 1, row_widget)
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
                u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()
            ]
        elif event.mimeData().hasImage():
            files = ["clipboard_image.png"]

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
            if suffix in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}:
                try:
                    import base64

                    with open(p, "rb") as f:
                        data = base64.b64encode(f.read()).decode("utf-8")
                    results.append(
                        {
                            "type": "image",
                            "path": str(p),
                            "name": p.name,
                            "data": data,
                            "mime": f"image/{suffix[1:]}",
                        }
                    )
                except Exception as e:
                    print(f"[ATTACH] Image read error: {e}")
            else:
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    results.append(
                        {
                            "type": "text",
                            "path": str(p),
                            "name": p.name,
                            "content": content,
                        }
                    )
                except Exception:
                    results.append(
                        {
                            "type": "text",
                            "path": str(p),
                            "name": p.name,
                            "content": f"[Binary or unreadable file: {p.name}]",
                        }
                    )
        return results

    # ========================================================
    # SEND MESSAGE (STREAMING)
    # ========================================================

    def send_message(self):

        if self.is_closing:
            return

        if self.is_processing:
            return

        message = sanitize_user_text(self.user_input.text())

        if not message:
            return

        # Validate message length
        max_length = get_setting("chat.max_message_length", 2000)
        if len(message) > max_length:
            self.add_ai_message_rich(
                f"that message is too long! 😅\n\n"
                f"Maximum length is {max_length} characters.\n"
                f"Your message is {len(message)} characters.\n\n"
                f"Try splitting it into smaller messages."
            )
            return

        self.add_user_message(message)
        self._append_user_message_to_chat(message)

        # Display any attached images in chat
        for att in self._process_attachments_for_ai():
            if att["type"] == "image":
                self.add_image_message(att["path"])

        self._clear_attachments()
        self.user_input.clear()

        if self.companion is not None:
            self.companion.on_user_message(message)

        # V2: Capture journey memories (projects, problems, goals,
        # decisions, milestones) and working preferences from the
        # user message. Respects memory settings internally.
        try:
            from memory import capture_journey_memories, capture_preferences

            captured = capture_journey_memories(message)

            for jtype, title in captured:
                print(f"[JOURNEY] Remembered {jtype}: {title}")

            prefs = capture_preferences(message)

            for key, value in prefs:
                print(f"[PREF] Learned: {key} = {value}")

        except Exception as error:
            print("[JOURNEY] Capture error:", error)

        self.set_processing_state(True)

        # Screen-vision distinct status: show "Looking…" before thinking when vision intent
        _lower = message.lower().strip()
        _vision_phrases = ("see my screen", "look at my screen", "what's on my screen", "what is on my screen", "what am i doing", "what i'm doing", "describe my screen", "what do you see", "can you see my screen")
        if any(p in _lower for p in _vision_phrases):
            self.update_status("thinking", "Looking at your screen…")
            self.character_call("react", "thinking", {"message": "Let me look at your screen…"})
        else:
            self.update_status("thinking", "Thinking")
            self.character_call("react_to_message", message)
            self.character_call("set_thinking", True)
            self.character_call("react", "thinking", {"message": "I'm thinking through your request…"})

        self.show_thinking()

        # Create streaming worker
        attachments = self._process_attachments_for_ai()
        self.worker = StreamingWorker(message, self, attachments=attachments)
        self._current_message = message
        self._current_browser = None
        self._current_full_text = ""

        # Companion: acknowledge the request like a friend would
        messenger = getattr(self, "companion_messenger", None)
        if messenger is not None:
            try:
                messenger.announce(CompanionEvent.TASK_STARTED)
            except Exception:
                pass

        # Connect signals
        self.worker.stream_started.connect(self._on_stream_started)
        self.worker.chunk_ready.connect(self._on_chunk_ready)
        self.worker.stream_finished.connect(self._on_stream_finished)
        self.worker.stream_failed.connect(self._on_stream_failed)

        # Safety watchdog: reset processing state if worker never signals completion
        self._worker_watchdog = QTimer(self)
        self._worker_watchdog.setSingleShot(True)
        self._worker_watchdog.timeout.connect(self._on_worker_timeout)
        self._worker_watchdog.start(60000)  # 60 second hard timeout

        self.worker.start()

    # ========================================================
    # STREAMING HANDLERS
    # ========================================================

    def _on_stream_started(self):
        """Called when streaming begins.

        Do NOT create an empty assistant container here — that was the
        ghost/empty-bubble bug. Keep the AVORA typing indicator visible
        until the first real chunk arrives.
        """
        if self.is_closing:
            return

        self._current_browser = None
        self._current_full_text = ""
        # Ensure status reflects active streaming
        self.update_status("thinking", "Creating")

    def _on_chunk_ready(self, chunk):
        """Called when a new chunk of text is available."""
        if self.is_closing:
            return

        text_chunk = str(chunk)

        # First token: swap the typing indicator for the real response
        # in-place — the indicator disappears the moment content exists.
        if self._current_browser is None:
            if not text_chunk.strip():
                return
            self.remove_thinking()
            self._current_browser = self.add_ai_message_rich(text_chunk, streaming=True)
            self._current_full_text = text_chunk
            return

        self._current_full_text += text_chunk

        # Update the browser with rendered HTML. streaming=True hides
        # trailing incomplete markers (### / ** / `) so raw Markdown
        # never flashes while the response is arriving.
        html = markdown_to_html(self._current_full_text, streaming=True)
        self._current_browser.setHtml(html)

        # Adjust height
        self._adjust_browser_height(self._current_browser)

        self.scroll_to_bottom()

    def _on_stream_finished(self, full_text):
        """Called when streaming is complete."""
        if self.is_closing:
            return

        self._current_full_text = str(full_text)

        # Safety: if no chunks ever rendered (empty/whitespace-only reply),
        # do NOT create a ghost bubble — just finalize state.
        if self._current_browser is None:
            if str(full_text).strip():
                self._current_browser = self.add_ai_message_rich(full_text)
            if self._current_browser is None:
                self.update_status("ready", "Ready")
                self.character_call("set_thinking", False)
                self.character_call("set_expression", "idle")
                self.set_processing_state(False)
                self.cleanup_worker()
                return

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

        self.character_call("set_thinking", False)
        self.character_call(
            "react", "speaking", {"message": "I've got an answer for you."}
        )

        if self.companion is not None:
            self.companion.on_ai_response(str(full_text))

        # Voice
        should_speak = self.voice_enabled and bool(
            get_setting("voice.speak_after_response", True)
        )
        if should_speak:
            self.start_voice(self._current_full_text)
        else:
            self.character_call("set_expression", "idle")

        self.set_processing_state(False)
        self.cleanup_worker()

    def _on_stream_failed(self, error_msg):
        """Called when streaming fails."""
        if self.is_closing:
            return

        self.remove_thinking()
        self.update_status("error", "Error")

        self.character_call("set_thinking", False)
        self.character_call("set_expression", "sad")
        self.character_call("react", "error", {"message": "Something went wrong."})

        messenger = getattr(self, "companion_messenger", None)
        if messenger is not None:
            try:
                messenger.announce(CompanionEvent.TASK_FAILED)
            except Exception:
                pass

        if self.companion is not None:
            self.companion.on_error(error_msg)

        # Clean single error notification — no empty bubble, no duplicates.
        # (Errors are not persisted as assistant messages, so reloading the
        # conversation never shows a duplicate error bubble.)
        self.add_error_message(self._current_message)

        print("========== AI ERROR ==========")
        print(error_msg)
        print("==============================\n")

        self.set_processing_state(False)
        self.cleanup_worker()

    # ========================================================
    # MESSAGE ACTIONS (Stop / Regenerate)
    # ========================================================

    def _add_message_actions(self, browser):
        """Small subtle regenerate action aligned within centered column."""
        if browser is None:
            return
        # Find the MessageRow that contains this browser
        row_widget = None
        for i in range(self.message_layout.count()):
            item = self.message_layout.itemAt(i)
            w = item.widget() if item else None
            if w is not None and w.objectName() == "MessageRow":
                found = self._find_bubble_in_row(w)
                if found is browser:
                    row_widget = w
                    row_index = i
                    break
        if row_widget is None:
            return
        regen_btn = QPushButton("↻ Regenerate")
        regen_btn.setFixedHeight(26)
        regen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        regen_btn.setToolTip("Regenerate response")
        regen_btn.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: 1px solid rgba(255,255,255,0.08);"
            "  border-radius: 12px;"
            "  padding: 3px 10px;"
            "  color: #6B6B80;"
            "  font-size: 11px;"
            "}"
            "QPushButton:hover {"
            "  background: rgba(0,255,136,0.08);"
            "  color: #A0FFCC;"
            "  border-color: rgba(0,255,136,0.22);"
            "}"
        )
        user_msg = browser.property("user_message") or ""
        regen_btn.clicked.connect(lambda checked, msg=user_msg: self.regenerate_response(msg))
        # Wrap button in centered row similar to messages
        btn_center = QWidget()
        btn_center.setMaximumWidth(860)
        btn_layout = QHBoxLayout(btn_center)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(regen_btn)
        btn_layout.addStretch()
        outer = QWidget()
        outer.setObjectName("MessageRowAction")
        outer_layout = QHBoxLayout(outer)
        outer_layout.setContentsMargins(0, 2, 0, 2)
        outer_layout.addStretch()
        # Factor 100: the action column claims full width (up to 860px) so the
        # button aligns with the LEFT edge of the conversation column, matching
        # the AVORA response above it — instead of floating mid-viewport.
        outer_layout.addWidget(btn_center, 100)
        outer_layout.addStretch()
        self.message_layout.insertWidget(row_index + 1, outer)

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

        self.character_call("set_thinking", True)
        self.character_call("react", "thinking", {"message": "Let me try again..."})

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

        self.character_call("set_thinking", False)

        reply = clean_ai_reply(reply)
        self.add_ai_message_rich(str(reply))
        self._append_assistant_message_to_chat(str(reply))

        should_speak = self.voice_enabled and bool(
            get_setting("voice.speak_after_response", True)
        )
        if should_speak:
            self.start_voice(str(reply))
        else:
            self.character_call("set_expression", "idle")

        self.set_processing_state(False)

    def _on_regenerate_failed(self, error):
        """Handle regenerate failure."""
        if self.is_closing:
            return

        self.remove_thinking()
        self.update_status("error", "Error")

        self.character_call("set_thinking", False)
        self.character_call("set_expression", "sad")

        self.add_error_message(self._current_message)

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

        self.character_call("set_thinking", False)
        self.character_call("set_expression", "idle")

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

            speak(reply, on_start=self.start_talking, on_finish=self.finish_talking)

        except TypeError:
            # Compatibility fallback for
            # older voice.py versions.

            try:
                speak(reply)

                self.character_call("set_expression", "happy")

            except Exception as error:
                print("VOICE ERROR:", error)

                self.finish_talking()

        except Exception as error:
            print("VOICE ERROR:", error)

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

        self.character_call("set_thinking", False)

        self.character_call("set_expression", "sad")

        self.character_call("react", "error", {"message": "Something went wrong."})

        self.add_ai_message(
            "Sorry brooo 😭\n\n"
            "Something went wrong while processing your request.\n\n"
            "Please try again."
        )

        print("\n========== AI ERROR ==========")

        print(error)

        print("==============================\n")

        self.set_processing_state(False)

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

        # Stop the watchdog timer if it's still running
        if hasattr(self, "_worker_watchdog") and self._worker_watchdog is not None:
            self._worker_watchdog.stop()
            self._worker_watchdog = None

    def _on_worker_timeout(self):
        """Safety fallback: reset UI state if worker never completed."""
        print("[WARNING] Worker did not complete within timeout — resetting state.")
        self._current_browser = None
        self.update_status("error", "Timeout")
        self.set_processing_state(False)
        self.remove_thinking()
        self.cleanup_worker()

    # ========================================================
    # PROCESSING STATE
    # ========================================================

    def set_processing_state(
        self,
        processing,
    ):

        self.is_processing = bool(processing)

        self.user_input.setEnabled(not self.is_processing)

        self.send_button.setEnabled(not self.is_processing)
        # Visual send/stop feedback — subtle opacity change without layout shift
        try:
            if self.is_processing:
                self.send_button.setStyleSheet(self.send_button.styleSheet() + "\nQPushButton:disabled { opacity: 0.45; }")
            else:
                # Trigger polish to restore disabled style cleanly
                self.send_button.style().unpolish(self.send_button)
                self.send_button.style().polish(self.send_button)
        except Exception:
            pass

        self.new_chat_button.setEnabled(not self.is_processing)

        if not self.is_processing:
            self.mic_button.setEnabled(True)

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

        self.character_talking_signal.emit(True)

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

        self.character_talking_signal.emit(False)

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

        self.character_call("set_expression", "idle")

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

        self.character_talking_signal.emit(False)

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

        self.character_call("set_expression", "happy")

        self.add_ai_message(
            "New conversation started 😎🔥\n\nWhat do you want to talk about?"
        )

        QTimer.singleShot(1500, self.return_to_idle)

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

    def _get_active_chat(self) -> dict | None:
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
        if hasattr(self, "_new_chat_lock") and self._new_chat_lock:
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
            QTimer.singleShot(500, lambda: setattr(self, "_new_chat_lock", False))

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
        chat["messages"].append(
            {
                "role": "user",
                "content": text,
                "timestamp": now,
            }
        )
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
        chat["messages"].append(
            {
                "role": "assistant",
                "content": text,
                "timestamp": now,
            }
        )
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
    # SCROLL — CHAT IS ONLY SCROLLABLE AREA
    # ========================================================

    def _is_near_bottom(self, threshold=120):
        """Check if user is near bottom (don't force scroll if reading history)."""
        sb = self.chat_area.verticalScrollBar()
        return (sb.maximum() - sb.value()) <= threshold

    def _on_chat_scroll(self, value):
        """Show/hide floating scroll button based on position."""
        try:
            sb = self.chat_area.verticalScrollBar()
            near_bottom = (sb.maximum() - value) <= 120
            self._auto_scroll_enabled = near_bottom
            if hasattr(self, "_scroll_down_btn") and self._scroll_down_btn is not None:
                if near_bottom:
                    self._scroll_down_btn.hide()
                else:
                    # Only show if there are messages
                    has_msgs = self.message_layout.count() > 1
                    if has_msgs:
                        self._scroll_down_btn.show()
                        self._scroll_down_btn.raise_()
                    else:
                        self._scroll_down_btn.hide()
                self._position_scroll_btn()
        except Exception:
            pass

    def _position_scroll_btn(self):
        """Position floating scroll button bottom-center above composer."""
        try:
            if not hasattr(self, "_scroll_down_btn") or self._scroll_down_btn is None:
                return
            vp = self.chat_area.viewport()
            btn = self._scroll_down_btn
            x = (vp.width() - btn.width()) // 2
            y = vp.height() - btn.height() - 12
            btn.move(x, y)
        except Exception:
            pass

    def scroll_to_bottom(self, force=False):
        """Smart scroll — only auto-scroll if near bottom, unless forced."""
        if not force and not getattr(self, "_auto_scroll_enabled", True):
            # User is reading history — don't yank them down; show button instead
            try:
                if hasattr(self, "_scroll_down_btn"):
                    self._scroll_down_btn.show()
                    self._scroll_down_btn.raise_()
                    self._position_scroll_btn()
            except Exception:
                pass
            return
        QTimer.singleShot(30, self._scroll_to_bottom_now)

    def _scroll_to_bottom_now(self):
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self._position_scroll_btn()
        # Re-pin while bubble heights settle, but respect user intent
        self._repin_budget = 6
        try:
            scrollbar.rangeChanged.disconnect(self._repin_scroll)
        except Exception:
            pass
        scrollbar.rangeChanged.connect(self._repin_scroll)

    def _repin_scroll(self):
        """Briefly follow growing conversation if still near bottom."""
        if self._repin_budget <= 0:
            try:
                self.chat_area.verticalScrollBar().rangeChanged.disconnect(self._repin_scroll)
            except (RuntimeError, TypeError):
                pass
            return
        self._repin_budget -= 1
        if not self._is_near_bottom(threshold=160):
            # User scrolled away — stop repinning
            try:
                self.chat_area.verticalScrollBar().rangeChanged.disconnect(self._repin_scroll)
            except Exception:
                pass
            return
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self._position_scroll_btn()

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
            self.character.setParent(None)

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

        self.character.set_scale_factor(0.62)

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

        self.character.setParent(self)

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

        if self.character.parent() is self.sidebar:
            self.character.set_scale_factor(self.get_character_scale_factor())

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

            self.character.move(x, y)

            self.character.raise_()

        elif self.character.parent() is self:
            if (
                not hasattr(self.character, "_user_positioned")
                or not self.character._user_positioned
            ):
                margin = 12
                x = margin
                y = max(
                    margin,
                    self.height() - self.character.height() - margin,
                )
                self.character.move(x, y)
                self.character.raise_()

            else:
                margin = 12
                x = max(
                    margin,
                    min(
                        self.character.x(),
                        self.width() - self.character.width() - margin,
                    ),
                )
                y = max(
                    margin,
                    min(
                        self.character.y(),
                        self.height() - self.character.height() - margin,
                    ),
                )

                if self.character.x() != x or self.character.y() != y:
                    self.character.move(x, y)

                    self.save_companion_position()

                self.character.raise_()

    # ========================================================
    # RESIZE
    # ========================================================

    def changeEvent(
        self,
        event,
    ):

        # Preserve timer/CPU optimization for minimize/hide (merged from earlier changeEvent)
        try:
            if event.type() == QEvent.Type.WindowStateChange:
                is_min = bool(self.windowState() & Qt.WindowState.WindowMinimized)
                for name in ("neural_timer", "_cursor_glow_timer"):
                    t = getattr(self, name, None)
                    if t is not None:
                        if is_min:
                            if t.isActive():
                                t.stop()
                        else:
                            if not t.isActive():
                                t.start(100 if name == "neural_timer" else 16)
            elif event.type() == QEvent.Type.Hide:
                for name in ("neural_timer", "_cursor_glow_timer"):
                    t = getattr(self, name, None)
                    if t is not None and t.isActive():
                        t.stop()
            elif event.type() == QEvent.Type.Show:
                for name, interval in (("neural_timer", 100), ("_cursor_glow_timer", 16)):
                    t = getattr(self, name, None)
                    if t is not None and not t.isActive() and not self.isMinimized():
                        t.start(interval)
        except Exception:
            pass
        super().changeEvent(event)

        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                self.enter_compact_character_mode()

            elif self.compact_character_mode:
                self.restore_character_to_window()

        self.position_character()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.neural_canvas:
            self.neural_canvas.setGeometry(self.rect())
        self.position_character()
        QTimer.singleShot(80, self._reflow_messages)
        QTimer.singleShot(80, self._position_scroll_btn)
        # Update empty state centering on resize
        try:
            empty = getattr(self, "empty_state", None)
            if empty is not None and empty.isVisible():
                QTimer.singleShot(80, lambda: self._center_empty_state(empty))
        except Exception:
            pass

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
            print("VOICE STOP ERROR:", error)

        self.character_talking_signal.emit(False)

        self.remove_thinking()

        # ----------------------------------------------------
        # STOP AI WORKER
        # ----------------------------------------------------

        if self.worker is not None:
            try:
                if self.worker.isRunning():
                    self.worker.requestInterruption()

                    self.worker.quit()

                    if not self.worker.wait(2500):
                        print("AI worker did not stop within timeout.")

            except Exception as error:
                print("WORKER CLOSE ERROR:", error)

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

        if getattr(self, "_cursor_glow_timer", None) is not None:
            try:
                self._cursor_glow_timer.stop()
            except Exception:
                pass
            self._cursor_glow_timer = None

        if getattr(self, "dot_timer", None) is not None:
            try:
                self.dot_timer.stop()
            except Exception:
                pass
            self.dot_timer = None

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

        if hasattr(self, "screen_awareness") and self.screen_awareness is not None:
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
        Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
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
    logo.setStyleSheet("color: #00FF88; background: transparent;")

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

    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    app.setApplicationName("Avora")

    app.setOrganizationName("Avora")

    app.setWindowIcon(QIcon(str(ICON_PATH)))

    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
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

    sys.exit(app.exec())


# ============================================================
# RUN
# ============================================================


if __name__ == "__main__":
    main()
