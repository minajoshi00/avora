"""
===============================================================
                    AVORA AI THEME SYSTEM v1.0
===============================================================

Centralized design token system with Light Mode, Dark Mode, and System Mode.

Usage from any widget:

    from theme import get_current_theme

    current = get_current_theme()

    current["background"]["primary"]   -> "#0B0B12"
    current["surface"]["card"]         -> "#111827"
    current["text"]["primary"]         -> "#F5F5F5"

    # Or in stylesheets:

    from theme import apply_theme_to_widget

    apply_theme_to_widget(self)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .settings import get_setting, set_setting, is_voice_enabled, is_character_enabled, add_settings_listener

from PySide6.QtWidgets import QApplication


# ================================================================
# DESIGN TOKENS
# ================================================================
# All colors are documented with a single place of truth.
# No more hardcoded hex values.

LIGHT_THEME: Dict[str, Any] = {
    "mode": "Light",
    "id": "light",

    # ── Backgrounds ─────────────────────────────────────────────
    "background": {
        "primary":   "#F7F7FA",   # overall window
        "secondary": "#FFFFFF",   # sidebar / panels
        "tertiary":  "#EDEDF0",   # input containers / hover surfaces
    },

    # ── Surfaces ────────────────────────────────────────────────
    "surface": {
        "card":       "#FFFFFF",
        "elevated":   "#FFFFFF",
        "hover":      "#F0F0F5",
        "pressed":    "#E6E6EC",
        "input":      "#FFFFFF",
    },

    # ── Text ────────────────────────────────────────────────────
    "text": {
        "primary":   "#1A1D2B",
        "secondary": "#5A5D6E",
        "muted":     "#8C8F99",
        "inverse":   "#FFFFFF",
    },

    # ── Borders ─────────────────────────────────────────────────
    "border": {
        "default":  "#D4D4DC",
        "subtle":   "#E8E8EE",
        "focus":    "#7B61FF",
    },

    # ── Dividers ────────────────────────────────────────────────
    "divider": "#E4E4EC",

    # ── Accent ──────────────────────────────────────────────────
    "accent": {
        "default":  "#7B61FF",
        "hover":    "#9478FF",
        "pressed":  "#5E47D9",
        "muted":    "#E9E4FF",
        "glow":     "rgba(123, 97, 255, 0.15)",
    },

    # ── Semantics ───────────────────────────────────────────────
    "semantic": {
        "success": "#16A34A",
        "success_bg": "#DCFCE7",
        "error":   "#DC2626",
        "error_bg": "#FEE2E2",
        "warning": "#D97706",
        "warning_bg": "#FEF3C7",
        "info":    "#2563EB",
        "info_bg": "#DBEAFE",
    },

    # ── Button colors are derived from accent above; keep placeholders
    "button": {
        "primary_bg":       "#7B61FF",
        "primary_hover":    "#9478FF",
        "primary_pressed":  "#5E47D9",
        "primary_text":     "#FFFFFF",
        "secondary_bg":     "#FFFFFF",
        "secondary_hover":  "#F0F0F5",
        "secondary_pressed":"#E6E6EC",
        "secondary_text":   "#1A1D2B",
        "danger_bg":        "#DC2626",
        "danger_hover":     "#EF4444",
        "danger_pressed":   "#B91C1C",
        "danger_text":      "#FFFFFF",
        "disabled_bg":      "#E4E4EC",
        "disabled_text":    "#A0A3B1",
    },

    # ── Shadows ─────────────────────────────────────────────────
    "shadow": {
        "sm":   "rgba(0, 0, 0, 0.06)",
        "md":   "rgba(0, 0, 0, 0.10)",
        "lg":   "rgba(0, 0, 0, 0.14)",
        "xl":   "rgba(0, 0, 0, 0.20)",
    },

    # ── Chat-specific ───────────────────────────────────────────
    "chat": {
        "user_bubble":   "#7B61FF",
        "user_text":     "#FFFFFF",
        "ai_bubble":     "#FFFFFF",
        "ai_border":     "#D4D4DC",
        "ai_text":       "#1A1D2B",
        "code_bg":       "#F3F4F6",
        "typing_indicator":"#8C8F99",
    },
}

DARK_THEME: Dict[str, Any] = {
    "mode": "Dark",
    "id": "dark",

    # ── Backgrounds ─────────────────────────────────────────────
    "background": {
        "primary":   "#0B0B12",
        "secondary": "#11111B",
        "tertiary":  "#171722",
    },

    # ── Surfaces ────────────────────────────────────────────────
    "surface": {
        "card":       "#191925",
        "elevated":   "#1E1E2D",
        "hover":      "#252538",
        "pressed":    "#30304A",
        "input":      "#20202D",
    },

    # ── Text ────────────────────────────────────────────────────
    "text": {
        "primary":   "#F5F5F5",
        "secondary": "#B0B0C0",
        "muted":     "#858599",
        "inverse":   "#0B0B12",
    },

    # ── Borders ─────────────────────────────────────────────────
    "border": {
        "default":  "#303044",
        "subtle":   "#252538",
        "focus":    "#8B7AFF",
    },

    # ── Dividers ────────────────────────────────────────────────
    "divider": "#252538",

    # ── Accent ──────────────────────────────────────────────────
    "accent": {
        "default":  "#8B7AFF",
        "hover":    "#9E91FF",
        "pressed":  "#6C63FF",
        "muted":    "#2A2540",
        "glow":     "rgba(139, 122, 255, 0.20)",
    },

    # ── Semantics ───────────────────────────────────────────────
    "semantic": {
        "success": "#34D399",
        "success_bg": "rgba(52, 211, 153, 0.12)",
        "error":   "#FF6B6B",
        "error_bg": "rgba(255, 107, 107, 0.12)",
        "warning": "#FBBF24",
        "warning_bg": "rgba(251, 191, 36, 0.12)",
        "info":    "#60A5FA",
        "info_bg": "rgba(96, 165, 250, 0.12)",
    },

    # ── Button colors ───────────────────────────────────────────
    "button": {
        "primary_bg":       "#6C63FF",
        "primary_hover":    "#817AFF",
        "primary_pressed":  "#5149D8",
        "primary_text":     "#FFFFFF",
        "secondary_bg":     "#292944",
        "secondary_hover":  "#3B3B5D",
        "secondary_pressed":"#4A477A",
        "secondary_text":   "#F5F5F5",
        "danger_bg":        "#FF4757",
        "danger_hover":     "#FF6B7A",
        "danger_pressed":   "#D63447",
        "danger_text":      "#FFFFFF",
        "disabled_bg":      "#20202D",
        "disabled_text":    "#777783",
    },

    # ── Shadows ─────────────────────────────────────────────────
    "shadow": {
        "sm":   "rgba(0, 0, 0, 0.20)",
        "md":   "rgba(0, 0, 0, 0.35)",
        "lg":   "rgba(0, 0, 0, 0.50)",
        "xl":   "rgba(0, 0, 0, 0.65)",
    },

    # ── Chat-specific ───────────────────────────────────────────
    "chat": {
        "user_bubble":   "#6C63FF",
        "user_text":     "#FFFFFF",
        "ai_bubble":     "#20202D",
        "ai_border":     "#303044",
        "ai_text":       "#F5F5F5",
        "code_bg":       "#11111B",
        "typing_indicator":"#8B8B9E",
    },
}


# ================================================================
# SYSTEM MODE DETECTION
# ================================================================

_SYSTEM_DARK = False

try:
    import winreg

    def _detect_windows_dark():
        global _SYSTEM_DARK
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                0,
                winreg.KEY_READ,
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            _SYSTEM_DARK = (value == 0)
        except Exception:
            _SYSTEM_DARK = True  # default dark

    try:
        _detect_windows_dark()
    except Exception:
        _SYSTEM_DARK = True

except ImportError:
    # Non-Windows fallback: default to dark
    _SYSTEM_DARK = True


# ================================================================
# THEME MANAGEMENT
# ================================================================

def get_available_themes() -> Dict[str, str]:
    return {
        "light":      "☀️ Light Mode",
        "dark":       "🌙 Dark Mode",
        "system":     "💻 System Mode",
    }


def _resolve_theme_setting() -> str:
    raw = get_setting("appearance.theme", "dark")
    theme = str(raw).strip().lower()
    if theme not in ("light", "dark", "system"):
        return "dark"
    return theme


def _get_active_theme_id() -> str:
    resolved = _resolve_theme_setting()
    if resolved == "system":
        return "dark" if _SYSTEM_DARK else "light"
    return resolved


def get_current_theme() -> Dict[str, Any]:
    theme_id = _get_active_theme_id()
    return DARK_THEME.copy() if theme_id == "dark" else LIGHT_THEME.copy()


def get_current_theme_id() -> str:
    return _get_active_theme_id()


# ================================================================
# THEME LISTENER SYSTEM
# ================================================================

_theme_listeners = []


def add_theme_listener(callback):
    _theme_listeners.append(callback)


def remove_theme_listener(callback):
    if callback in _theme_listeners:
        _theme_listeners.remove(callback)


def _notify_theme_changed(new_theme: Dict[str, Any]):
    for cb in _theme_listeners:
        try:
            cb(new_theme)
        except Exception as e:
            print("[THEME] Listener error:", e)


def on_settings_changed(key: str, value):
    if key == "appearance.theme":
        new = get_current_theme()
        _notify_theme_changed(new)


# Register early so theme changes are caught
try:
    add_settings_listener(on_settings_changed)
except Exception:
    pass


# ================================================================
# QSS (Qt StyleSheet) GENERATION
# ================================================================

def _t(cat: str, key: str) -> str:
    """Shorthand to get token value: token('accent','hover')."""
    return get_current_theme().get(cat, {}).get(key, "")


def generate_qss() -> str:
    """Return a complete stylesheet for the current theme."""
    t = get_current_theme()
    b = t["background"]
    s = t["surface"]
    tx = t["text"]
    br = t["border"]
    a = t["accent"]
    bt = t["button"]
    sh = t["shadow"]
    ch = t["chat"]
    d = t["divider"]
    sem = t["semantic"]

    return f"""
    /* =================================================
       GLOBAL
    ================================================= */

    QWidget {{
        font-family: "Segoe UI";
        color: {tx["primary"]};
        background-color: transparent;
    }}

    QLabel {{
        background-color: transparent;
    }}

    QPushButton {{
    }}

    QCheckBox {{
    }}

    QSlider::handle:horizontal {{
    }}

    /* =================================================
       MAIN WINDOW
    ================================================= */

    #MainWindow {{
        background-color: {b["primary"]};
    }}

    /* =================================================
       SIDEBAR (MAIN APP)
    ================================================= */

    #Sidebar {{
        background-color: {b["secondary"]};
        border-right: 1px solid {br["subtle"]};
    }}

    #Logo {{
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: {tx["primary"]};
        padding: 4px 0 0 0;
    }}

    #SubText {{
        color: {tx["muted"]};
        font-size: 11px;
        letter-spacing: 1.3px;
        text-transform: uppercase;
    }}

    /* =================================================
       PROFILE CARD
    ================================================= */

    #ProfileCard {{
        background-color: {s["card"]};
        border-radius: 18px;
        border: 1px solid {br["subtle"]};
    }}

    #ProfileName {{
        font-size: 15px;
        font-weight: bold;
        color: {tx["primary"]};
    }}

    #Online {{
        color: {sem["success"]};
        font-size: 12px;
    }}

    /* =================================================
       SIDEBAR BUTTONS
    ================================================= */

    #NewChatButton,
    #SettingsButton {{
        background-color: {s["hover"]};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 12px 14px;
        color: {tx["primary"]};
        font-size: 14px;
        font-weight: 600;
    }}

    #NewChatButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #8B7AFF, stop:1 #6C63FF);
        border: none;
        color: white;
    }}

    #NewChatButton:hover,
    #SettingsButton:hover {{
        background-color: {s["pressed"]};
    }}

    #NewChatButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #9E91FF, stop:1 #817AFF);
    }}

    #NewChatButton:pressed,
    #SettingsButton:pressed {{
        background-color: {br["default"]};
    }}

    /* =================================================
       VOICE BUTTON
    ================================================= */

    #VoiceButton {{
        background-color: {s["input"]};
        border: 1px solid {br["default"]};
        border-radius: 12px;
        padding: 12px;
        color: {tx["primary"]};
        font-size: 13px;
    }}

    #VoiceButton:hover {{
        background-color: {s["hover"]};
        color: {tx["primary"]};
        border-color: {a["default"]};
    }}

    #VoiceButton:listening {{
        background-color: {sem["error"]};
        border-color: {sem["error"]};
        color: white;
    }}

    /* =================================================
       HEADER
    ================================================= */

    #Header {{
        background-color: transparent;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }}

    #HeaderTitle {{
        font-size: 18px;
        font-weight: 700;
        color: {tx["primary"]};
    }}

    #HeaderStatus {{
        color: {sem["success"]};
        font-size: 12px;
        font-weight: 600;
    }}

    /* =================================================
       CHAT AREA
    ================================================= */

    #ChatArea {{
        background-color: {b["primary"]};
        border: none;
    }}

    #MessageArea {{
        background-color: transparent;
        padding: 6px 0 0 0;
    }}

    /* =================================================
       MESSAGE BUBBLES
    ================================================= */

    #UserBubble {{
        background-color: {ch["user_bubble"]};
        border-radius: 18px;
        padding: 12px 16px;
        font-size: 14px;
        line-height: 1.5;
        color: {ch["user_text"]};
    }}

    #AIBubble {{
        background-color: {ch["ai_bubble"]};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 18px;
        padding: 12px 16px;
        font-size: 14px;
        line-height: 1.6;
        color: {ch["ai_text"]};
    }}

    #ImageBubble {{
        background-color: {ch["ai_bubble"]};
        border: 1px solid {ch["ai_border"]};
        border-radius: 16px;
        padding: 12px 16px;
    }}

    #Typing {{
        color: {ch["typing_indicator"]};
        font-size: 13px;
    }}

    /* =================================================
       INPUT AREA
    ================================================= */

    #InputContainer {{
        background-color: {s["input"]};
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 20px;
    }}

    #InputContainer:focus-within {{
        border: 1px solid rgba(139,122,255,0.7);
        background-color: {s["hover"]};
    }}

    #InputBox {{
        background-color: transparent;
        border: none;
        color: {tx["primary"]};
        font-size: 15px;
        padding: 12px 10px;
        selection-background-color: {a["muted"]};
        selection-color: {tx["primary"]};
    }}

    #InputBox::placeholder {{
        color: {tx["muted"]};
    }}

    #InputBox:disabled {{
        color: {tx["muted"]};
    }}

    /* =================================================
       SEND & MIC BUTTONS
    ================================================= */

    #SendButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #8B7AFF, stop:1 #5BC0FF);
        border: none;
        border-radius: 14px;
        color: {bt["primary_text"]};
        font-size: 18px;
        font-weight: 700;
    }}

    #SendButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #9E91FF, stop:1 #75C9FF);
    }}

    #SendButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #7567F0, stop:1 #3FA8E8);
    }}

    #SendButton:disabled {{
        background-color: {bt["disabled_bg"]};
        color: {bt["disabled_text"]};
    }}

    #MicButton {{
        background-color: {s["input"]};
        border: 1px solid {br["default"]};
        border-radius: 13px;
        color: {tx["secondary"]};
        font-size: 18px;
    }}

    #MicButton:hover {{
        background-color: {s["hover"]};
        color: {tx["primary"]};
        border-color: {a["default"]};
    }}

    #MicButton:listening {{
        background-color: {sem["error"]};
        border-color: {sem["error"]};
        color: white;
    }}

    /* =================================================
       SCROLLBARS
    ================================================= */

    QScrollBar:vertical {{
        background: transparent;
        width: 9px;
        margin: 3px;
    }}

    QScrollBar::handle:vertical {{
        background: {br["default"]};
        border-radius: 4px;
        min-height: 40px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {br["focus"]};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* =================================================
       SETTINGS WINDOW
    ================================================= */

    QWidget#SettingsBackground {{
        background-color: {b["primary"]};
    }}

    QFrame#SidebarSettings {{
        background-color: {b["secondary"]};
        border-right: 1px solid {br["subtle"]};
    }}

    QFrame#MainAreaSettings {{
        background-color: {b["primary"]};
    }}

    QWidget#ContentWidgetSettings {{
        background: transparent;
    }}

    QLabel#PageTitle {{
        color: {tx["primary"]};
        font-size: 27px;
        font-weight: 700;
        background: transparent;
    }}

    QLabel#PageDescription {{
        color: {tx["muted"]};
        font-size: 13px;
        background: transparent;
    }}

    QLabel#SectionTitle {{
        color: {tx["primary"]};
        font-size: 16px;
        font-weight: 600;
        background: transparent;
    }}

    QLabel#SettingName {{
        color: {tx["primary"]};
        font-size: 14px;
        font-weight: 600;
        background: transparent;
    }}

    QLabel#SettingDescription {{
        color: {tx["muted"]};
        font-size: 12px;
        background: transparent;
    }}

    QFrame#SettingCardFrame {{
        background: {s["card"]};
        border: 1px solid {br["subtle"]};
        border-radius: 16px;
    }}

    QFrame#SettingCardFrame:hover {{
        background: {s["hover"]};
        border: 1px solid {a["default"]};
    }}

    QListWidget {{
        background: transparent;
        border: none;
        outline: none;
        color: {tx["muted"]};
        font-size: 13px;
    }}

    QListWidget::item {{
        padding: 13px 14px;
        border-radius: 10px;
        margin: 1px 0;
        color: {tx["muted"]};
    }}

    QListWidget::item:hover {{
        background: {s["hover"]};
        color: {tx["primary"]};
    }}

    QListWidget::item:selected {{
        background: {s["pressed"]};
        color: {tx["primary"]};
        border-left: 3px solid {a["default"]};
    }}

    QPushButton {{
        background: {s["hover"]};
        color: {tx["primary"]};
        border: 1px solid {br["default"]};
        border-radius: 9px;
        padding: 9px 15px;
        font-size: 12px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background: {s["pressed"]};
        border-color: {a["default"]};
        color: {tx["primary"]};
    }}

    QPushButton:pressed {{
        background: {br["default"]};
    }}

    QPushButton#BackButton {{
        background: {s["input"]};
        border: 1px solid {a["default"]};
        color: {tx["primary"]};
        padding: 9px 17px;
    }}

    QPushButton#BackButton:hover {{
        background: {a["default"]};
        border-color: {a["hover"]};
        color: {bt["primary_text"]};
    }}

    QCheckBox {{
        spacing: 8px;
        color: {tx["primary"]};
    }}

    QCheckBox::indicator {{
        width: 52px;
        height: 28px;
        border-radius: 14px;
        background: {s["input"]};
        border: 1px solid {br["default"]};
    }}

    QCheckBox::indicator:checked {{
        background: {a["default"]};
        border: 1px solid {a["default"]};
    }}

    QCheckBox::indicator:unchecked:hover {{
        background: {s["hover"]};
        border-color: {a["hover"]};
    }}

    QCheckBox::indicator:checked:hover {{
        background: {a["hover"]};
        border: 1px solid {a["hover"]};
    }}

    QComboBox {{
        background: {s["input"]};
        color: {tx["primary"]};
        border: 1px solid {br["default"]};
        border-radius: 8px;
        padding: 8px 10px;
        min-width: 130px;
    }}

    QComboBox:hover {{
        border-color: {a["default"]};
    }}

    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid none;
        border-right: 5px solid none;
        border-top: 6px solid {tx["secondary"]};
        margin-right: 6px;
    }}

    QComboBox QAbstractItemView {{
        background: {s["elevated"]};
        color: {tx["primary"]};
        border: 1px solid {br["default"]};
        selection-background-color: {a["default"]};
        selection-color: {bt["primary_text"]};
        border-radius: 8px;
        padding: 4px;
    }}

    QSlider::groove:horizontal {{
        height: 5px;
        background: {br["default"]};
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        width: 16px;
        height: 16px;
        margin: -6px 0;
        background: {a["default"]};
        border-radius: 8px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {a["hover"]};
    }}

    QSlider::sub-page:horizontal {{
        background: {a["default"]};
        border-radius: 2px;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 9px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical {{
        background: {br["default"]};
        border-radius: 4px;
        min-height: 45px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {a["default"]};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """


# ================================================================
# THEME APPLICATION
# ================================================================

def apply_theme_to_app():
    """Apply theme to the QApplication instance."""
    app = QApplication.instance()
    if app is None:
        raise RuntimeError("QApplication not running")

    app.setStyleSheet(generate_qss())


def apply_theme_to_widget(widget):
    """Apply the current theme stylesheet to a single widget."""
    try:
        widget.setStyleSheet(generate_qss())
    except Exception:
        pass


def refresh_theme():
    """Force a full theme refresh: re-apply and notify."""
    apply_theme_to_app()
    _notify_theme_changed(get_current_theme())


# ================================================================
# UTILITIES
# ================================================================

def is_dark_mode() -> bool:
    return get_current_theme_id() == "dark"


def is_light_mode() -> bool:
    return get_current_theme_id() == "light"


def is_system_mode() -> bool:
    return _resolve_theme_setting() == "system"


def get_accent_color() -> str:
    return get_current_theme()["accent"]["default"]


def get_background_color() -> str:
    return get_current_theme()["background"]["primary"]


def get_surface_color() -> str:
    return get_current_theme()["surface"]["card"]


def get_text_color() -> str:
    return get_current_theme()["text"]["primary"]


def get_border_color() -> str:
    return get_current_theme()["border"]["default"]


def get_muted_text_color() -> str:
    return get_current_theme()["text"]["muted"]


# ================================================================
# CHARACTER THEME HELPERS
# ================================================================

def get_character_theme() -> Dict[str, Any]:
    """Return theme colors in a format the character.py painter can use."""
    theme = get_current_theme()
    return {
        "is_dark": is_dark_mode(),
        "primary": theme["background"]["primary"],
        "secondary": theme["background"]["secondary"],
        "surface": theme["surface"]["card"],
        "text_primary": theme["text"]["primary"],
        "text_secondary": theme["text"]["secondary"],
        "accent": theme["accent"]["default"],
        "accent_glow": theme["accent"]["glow"],
        "border": theme["border"]["default"],
        "success": theme["semantic"]["success"],
        "error": theme["semantic"]["error"],
        "warning": theme["semantic"]["warning"],
    }


# ================================================================
# LIGHTWEIGHT NOTIFICATION
# ================================================================

class ThemeNotifier:
    """Minimal helper to show a brief toast when theme changes."""

    def __init__(self):
        self._last_id = get_current_theme_id()

    def check(self):
        current = get_current_theme_id()
        if current != self._last_id:
            self._last_id = current
            label = "Light" if current == "light" else "Dark" if current == "dark" else "System"
            try:
                from PySide6.QtWidgets import QSystemTrayIcon
                from PySide6.QtGui import QIcon
                
                # Find tray icon (if it exists)
                main_window = QApplication.activeWindow()
                if main_window and hasattr(main_window, 'tray_icon'):
                    icon = QSystemTrayIcon.MessageIcon.Information
                    main_window.tray_icon.showMessage(
                        "Theme Changed",
                        f"Switched to {label} Mode",
                        icon,
                        1500,
                    )
            except Exception:
                pass