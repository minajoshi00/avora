# ============================================================
#                     CHAT SIDEBAR
# ============================================================
# Collapsible sidebar for recent chats with search,
# grouping, pinning, favoriting, and context menu.
# ============================================================

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from app_paths import APP_DATA_DIR, BASE_DIR, ICON_PATH

from PySide6.QtCore import (
    Qt,
    QDateTime,
    QPoint,
    QSize,
    Signal,
    Slot,
)

from PySide6.QtGui import (
    QAction,
    QCursor,
    QFont,
    QIcon,
    QMouseEvent,
    QPainter,
    QColor,
)

from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from theme import (
    get_current_theme,
    is_dark_mode,
    get_accent_color,
    get_text_color,
    get_muted_text_color,
    get_surface_color,
    get_border_color,
)

BASE_DIR = Path(__file__).resolve().parent
CONVERSATIONS_FILE = APP_DATA_DIR / "conversations.json"


def _get_theme_token(path: str) -> str:
    parts = path.split(".")
    theme = get_current_theme()
    current = theme
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return ""
    if isinstance(current, str):
        return current
    return ""


def get_secondary_text_color() -> str:
    theme = get_current_theme()
    return theme.get("text", {}).get("secondary", "#B0B0C0")


def get_grouped_chats(chats: list[dict]) -> dict[str, list[dict]]:
    now = datetime.now()
    groups: dict[str, list[dict]] = {
        "Pinned": [],
        "Today": [],
        "Yesterday": [],
        "This Week": [],
        "Last Month": [],
        "Older": [],
    }
    for chat in chats:
        if chat.get("pinned", False):
            groups["Pinned"].append(chat)
            continue
        updated_str = chat.get("updated_at", "")
        try:
            if updated_str.endswith("Z"):
                updated_str = updated_str[:-1]
            updated = datetime.fromisoformat(updated_str)
        except (ValueError, TypeError):
            groups["Older"].append(chat)
            continue
        if updated.date() == now.date():
            groups["Today"].append(chat)
        elif updated.date() == (now - timedelta(days=1)).date():
            groups["Yesterday"].append(chat)
        elif updated.isocalendar()[1] == now.isocalendar()[1] and updated.year == now.year:
            groups["This Week"].append(chat)
        elif updated >= now - timedelta(days=30):
            groups["Last Month"].append(chat)
        else:
            groups["Older"].append(chat)
    return groups


def truncate_title(title: str, max_len: int = 40) -> str:
    if len(title) <= max_len:
        return title
    return title[:max_len].rstrip() + "..."


def generate_title_from_messages(messages: list[dict]) -> str:
    if not messages:
        return "New Conversation"
    for msg in messages:
        if msg.get("role") == "user":
            text = msg.get("content", "")
            return truncate_title(text)
    first_msg = messages[0]
    content = first_msg.get("content", "")
    return truncate_title(content)


class ChatListTile(QWidget):
    chat_selected = Signal(str)

    def __init__(self, chat: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.chat = chat
        self._pinned = chat.get("pinned", False)
        self._favorite = chat.get("favorite", False)
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(60)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.icon_label = QLabel("💬")
        self.icon_label.setFixedWidth(32)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self.icon_label)

        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.title_label = QLabel("")
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        text_layout.addWidget(self.title_label)

        self.preview_label = QLabel("")
        self.preview_label.setFont(QFont("Segoe UI", 9))
        self.preview_label.setStyleSheet("color: #858599;")
        self.preview_label.setMaximumHeight(30)
        text_layout.addWidget(self.preview_label)

        layout.addWidget(text_container, 1)

        self.time_label = QLabel("")
        self.time_label.setFont(QFont("Segoe UI", 8))
        self.time_label.setStyleSheet("color: #858599;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.time_label)

    def _apply_theme(self):
        theme = get_current_theme()
        text_primary = theme["text"]["primary"]
        text_secondary = theme["text"]["secondary"]
        surface_hover = theme["surface"]["hover"]
        accent = theme["accent"]["default"]
        border = theme["border"]["subtle"]

        self.setStyleSheet(
            f"ChatListTile {{\n"
            f"  background: transparent;\n"
            f"  border-radius: 10px;\n"
            f"  padding: 0px;\n"
            f"}}\n"
            f"ChatListTile:hover {{\n"
            f"  background: {surface_hover};\n"
            f"}}"
        )

        self.title_label.setStyleSheet(f"color: {text_primary};")
        self.preview_label.setStyleSheet(f"color: {text_secondary};")
        self.time_label.setStyleSheet(f"color: {text_secondary};")

        if self._pinned:
            self.icon_label.setText("📌")
        if self._favorite:
            self.icon_label.setText("⭐")

    def set_active(self, active: bool):
        if active:
            theme = get_current_theme()
            accent = theme["accent"]["default"]
            surface = theme["surface"]["card"]
            self.setStyleSheet(
                f"ChatListTile {{\n"
                f"  background: {surface};\n"
                f"  border-left: 3px solid {accent};\n"
                f"  border-radius: 10px;\n"
                f"}}\n"
                f"ChatListTile:hover {{\n"
                f"  background: {get_current_theme()['surface']['hover']};\n"
                f"}}"
            )
        else:
            self._apply_theme()

    def load_chat(self, chat: dict):
        self.chat = chat
        self._pinned = chat.get("pinned", False)
        self._favorite = chat.get("favorite", False)
        self._update_display()
        self._apply_theme()

    def _update_display(self):
        title = self.chat.get("title", "New Conversation")
        messages = self.chat.get("messages", [])
        updated_at = self.chat.get("updated_at", "")

        self.title_label.setText(truncate_title(title))

        preview_text = ""
        if messages:
            last_msg = messages[-1]
            role = last_msg.get("role", "")
            content = last_msg.get("content", "")
            if role == "user":
                preview_text = f"You: {content[:60]}"
            else:
                preview_text = content[:60]
            if len(content) > 60:
                preview_text += "..."

        self.preview_label.setText(preview_text)

        try:
            if updated_at:
                if updated_at.endswith("Z"):
                    updated_at = updated_at[:-1]
                dt = datetime.fromisoformat(updated_at)
                now = datetime.now()
                diff = now - dt
                if diff.days == 0:
                    self.time_label.setText(dt.strftime("%I:%M %p"))
                elif diff.days == 1:
                    self.time_label.setText("Yesterday")
                elif diff.days < 7:
                    self.time_label.setText(f"{diff.days}d ago")
                elif diff.days < 30:
                    self.time_label.setText(f"{diff.days // 7}w ago")
                else:
                    self.time_label.setText(dt.strftime("%m/%d/%y"))
            else:
                self.time_label.setText("")
        except (ValueError, TypeError):
            self.time_label.setText("")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.chat_selected.emit(self.chat.get("id", ""))
        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QMouseEvent):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu {"
            "  background-color: #1E1E2D;"
            "  border: 1px solid #303044;"
            "  border-radius: 8px;"
            "  padding: 6px;"
            "}"
            "QMenu::item {"
            "  padding: 8px 16px;"
            "  color: #F5F5F5;"
            "  border-radius: 4px;"
            "}"
            "QMenu::item:selected {"
            "  background-color: #292944;"
            "}"
        )

        pin_action = QAction("📌 Pin" if not self._pinned else "📌 Unpin", self)
        fav_action = QAction("⭐ Favorite" if not self._favorite else "⭐ Unfavorite", self)
        rename_action = QAction("✏️ Rename", self)
        delete_action = QAction("🗑️ Delete", self)

        pin_action.triggered.connect(
            lambda: self.parentWidget().parentWidget().toggle_pin(self.chat.get("id", ""))
            if self.parentWidget() and self.parentWidget().parentWidget()
            else None
        )
        fav_action.triggered.connect(
            lambda: self.parentWidget().parentWidget().toggle_favorite(self.chat.get("id", ""))
            if self.parentWidget() and self.parentWidget().parentWidget()
            else None
        )
        rename_action.triggered.connect(
            lambda: self.parentWidget().parentWidget().rename_chat(self.chat.get("id", ""))
            if self.parentWidget() and self.parentWidget().parentWidget()
            else None
        )
        delete_action.triggered.connect(
            lambda: self.parentWidget().parentWidget().delete_chat(self.chat.get("id", ""))
            if self.parentWidget() and self.parentWidget().parentWidget()
            else None
        )

        menu.addAction(pin_action)
        menu.addAction(fav_action)
        menu.addSeparator()
        menu.addAction(rename_action)
        menu.addAction(delete_action)

        menu.exec(QCursor.pos())


class ChatSidebar(QFrame):

    chat_selected = Signal(str)
    chat_deleted = Signal(str)
    new_chat_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._collapsed = False
        self._search_text = ""
        self._chats: list[dict] = []
        self._active_chat_id: Optional[str] = None
        self._chat_tiles: dict[str, ChatListTile] = {}
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        self.setObjectName("ChatSidebar")
        self.setMinimumWidth(240)
        self.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding,
            QSizePolicy.Policy.Expanding,
        )

        self.setStyleSheet(
            "QFrame#ChatSidebar {"
            "  background-color: #11111B;"
            "  border-right: 1px solid #252538;"
            "}"
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Header row: title + collapse toggle
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.header_label = QLabel("Recent Chats")
        self.header_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.header_label.setStyleSheet("color: #F5F5F5; padding: 4px 0;")
        header_layout.addWidget(self.header_label)

        self.toggle_btn = QPushButton("◀")
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_btn.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: none;"
            "  color: #858599;"
            "  font-size: 14px;"
            "  border-radius: 6px;"
            "}"
            "QPushButton:hover {"
            "  background: #252538;"
            "  color: #F5F5F5;"
            "}"
        )
        self.toggle_btn.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self.toggle_btn)

        main_layout.addLayout(header_layout)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search conversations...")
        self.search_input.setFixedHeight(34)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setStyleSheet(
            "QLineEdit {"
            "  background-color: #20202D;"
            "  border: 1px solid #303044;"
            "  border-radius: 10px;"
            "  padding: 6px 12px;"
            "  color: #F5F5F5;"
            "  font-size: 12px;"
            "}"
            "QLineEdit:focus {"
            "  border: 1px solid #8B7AFF;"
            "}"
            "QLineEdit::placeholder {"
            "  color: #858599;"
            "}"
        )
        main_layout.addWidget(self.search_input)

        # New Chat button
        self.new_chat_btn = QPushButton("＋  New Chat")
        self.new_chat_btn.setFixedHeight(36)
        self.new_chat_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.new_chat_btn.clicked.connect(self._on_new_chat)
        self.new_chat_btn.setStyleSheet(
            "QPushButton {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop:0 #8B7AFF, stop:1 #6C63FF);"
            "  border: none;"
            "  border-radius: 10px;"
            "  padding: 8px 16px;"
            "  color: #FFFFFF;"
            "  font-size: 13px;"
            "  font-weight: 600;"
            "}"
            "QPushButton:hover {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop:0 #9E91FF, stop:1 #817AFF);"
            "}"
            "QPushButton:pressed {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop:0 #6C63FF, stop:1 #5149D8);"
            "}"
        )
        main_layout.addWidget(self.new_chat_btn)

        # Chat list scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setStyleSheet(
            "QScrollArea {"
            "  background: transparent;"
            "  border: none;"
            "}"
            "QScrollBar:vertical {"
            "  background: transparent;"
            "  width: 6px;"
            "  margin: 4px;"
            "}"
            "QScrollBar::handle:vertical {"
            "  background: #303044;"
            "  border-radius: 3px;"
            "  min-height: 30px;"
            "}"
        )

        self.chat_list_widget = QWidget()
        self.chat_list_layout = QVBoxLayout(self.chat_list_widget)
        self.chat_list_layout.setContentsMargins(4, 4, 4, 4)
        self.chat_list_layout.setSpacing(4)
        self.chat_list_layout.addStretch()

        self.scroll_area.setWidget(self.chat_list_widget)
        main_layout.addWidget(self.scroll_area, 1)

        # Stats label at bottom
        self.stats_label = QLabel("0 conversations")
        self.stats_label.setFont(QFont("Segoe UI", 9))
        self.stats_label.setStyleSheet("color: #858599; padding: 4px 0;")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.stats_label)

    def _apply_theme(self):
        theme = get_current_theme()
        bg_primary = theme["background"]["primary"]
        bg_secondary = theme["background"]["secondary"]
        text_primary = theme["text"]["primary"]
        text_secondary = theme["text"]["secondary"]
        muted = theme["text"]["muted"]
        accent = theme["accent"]["default"]
        surface_card = theme["surface"]["card"]
        border_subtle = theme["border"]["subtle"]

        self.setStyleSheet(
            f"QFrame#ChatSidebar {{"
            f"  background-color: {bg_secondary};"
            f"  border-right: 1px solid {border_subtle};"
            f"}}"
        )

        self.header_label.setStyleSheet(f"color: {text_primary};")
        self.search_input.setStyleSheet(
            f"QLineEdit {{"
            f"  background-color: {surface_card};"
            f"  border: 1px solid {border_subtle};"
            f"  border-radius: 10px;"
            f"  padding: 6px 12px;"
            f"  color: {text_primary};"
            f"}}"
            f"QLineEdit:focus {{"
            f"  border: 1px solid {accent};"
            f"}}"
            f"QLineEdit::placeholder {{"
            f"  color: {muted};"
            f"}}"
        )

        self.stats_label.setStyleSheet(f"color: {muted};")

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        if self._collapsed:
            self.setFixedWidth(0)
            self.setMinimumWidth(0)
            self.setMaximumWidth(0)
        else:
            self.setFixedWidth(280)
            self.setMinimumWidth(280)
            self.setMaximumWidth(280)

    def _on_search_changed(self, text: str):
        self._search_text = text.strip().lower()
        self._refresh_chat_list()

    def _on_new_chat(self):
        self.new_chat_requested.emit()

    def set_chats(self, chats: list[dict]):
        self._chats = chats
        self._refresh_chat_list()

    def set_active_chat(self, chat_id: Optional[str]):
        self._active_chat_id = chat_id
        self._refresh_active_state()

    def _refresh_chat_list(self):
        while self.chat_list_layout.count() > 1:
            item = self.chat_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        filtered = self._chats
        if self._search_text:
            filtered = [
                c for c in self._chats
                if self._search_text in c.get("title", "").lower()
                or self._search_text in self._get_last_message_preview(c).lower()
            ]

        grouped = get_grouped_chats(filtered)

        group_display_order = ["Pinned", "Today", "Yesterday", "This Week", "Last Month", "Older"]
        group_labels = {
            "Pinned": "📌 Pinned",
            "Today": "Today",
            "Yesterday": "Yesterday",
            "This Week": "This Week",
            "Last Month": "Last Month",
            "Older": "Older",
        }

        for group_key in group_display_order:
            group_chats = grouped.get(group_key, [])
            if not group_chats:
                continue

            group_header = QLabel(group_labels[group_key])
            group_header.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            group_header.setStyleSheet(
                f"color: #858599; padding: 10px 4px 4px 12px; font-size: 10px;"
                f"text-transform: uppercase; letter-spacing: 0.5px;"
            )
            self.chat_list_layout.addWidget(group_header)

            for chat in group_chats:
                chat_id = chat.get("id", "")
                if chat_id not in self._chat_tiles:
                    tile = ChatListTile(chat, self.chat_list_widget)
                    tile.chat_selected.connect(self._on_tile_selected)
                    self._chat_tiles[chat_id] = tile
                else:
                    self._chat_tiles[chat_id].load_chat(chat)

                tile = self._chat_tiles[chat_id]
                is_active = chat_id == self._active_chat_id
                tile.set_active(is_active)
                self.chat_list_layout.addWidget(tile)

        self.chat_list_layout.addStretch()

        total = len(self._chats)
        self.stats_label.setText(f"{total} conversation{'s' if total != 1 else ''}")

    def _on_tile_selected(self, chat_id: str):
        self.chat_selected.emit(chat_id)

    def _refresh_active_state(self):
        for chat_id, tile in self._chat_tiles.items():
            tile.set_active(chat_id == self._active_chat_id)

    def _get_last_message_preview(self, chat: dict) -> str:
        messages = chat.get("messages", [])
        if messages:
            last = messages[-1]
            content = last.get("content", "")
            return content[:60]
        return ""

    def add_chat(self, chat: dict):
        self._chats.insert(0, chat)
        self._refresh_chat_list()

    def remove_chat(self, chat_id: str):
        self._chats = [c for c in self._chats if c.get("id") != chat_id]
        if chat_id in self._chat_tiles:
            tile = self._chat_tiles.pop(chat_id)
            tile.deleteLater()
        self._refresh_chat_list()

    def update_chat(self, chat_id: str):
        for i, chat in enumerate(self._chats):
            if chat.get("id") == chat_id:
                self._chats[i] = chat
                break
        self._refresh_chat_list()

    def get_chats(self) -> list[dict]:
        return list(self._chats)


def save_conversations(chats: list[dict], active_chat_id: Optional[str]) -> bool:
    try:
        data = {
            "chats": chats,
            "active_chat_id": active_chat_id,
        }
        filepath = CONVERSATIONS_FILE
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as error:
        print(f"[CHAT SIDEBAR] Save error: {error}")
        return False


def load_conversations() -> tuple[list[dict], Optional[str]]:
    try:
        filepath = CONVERSATIONS_FILE
        if not filepath.exists():
            return [], None
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        chats = data.get("chats", [])
        active_chat_id = data.get("active_chat_id")
        return chats, active_chat_id
    except Exception as error:
        print(f"[CHAT SIDEBAR] Load error: {error}")
        return [], None