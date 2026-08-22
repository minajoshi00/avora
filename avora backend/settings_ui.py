# ================================================================
#                    AI FRIEND SETTINGS UI
# ================================================================
#
# AI Friend - Advanced Settings Control Center
#
# Usage from main.py:
#
#     from settings_ui import SettingsWindow
#
#     self.settings_window = SettingsWindow(self)
#     self.settings_window.show()
#
# ================================================================

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
)

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from settings import (
    get_setting,
    set_setting,
    reset_all_settings,
    export_settings,
    import_settings,
    create_settings_backup,
    get_available_backups,
    restore_backup,
)

from secure_storage import (
    get_secure_storage,
    mask_key,
    validate_key_format,
    test_provider_connection,
)

try:
    from skills.email import (
        add_gmail_account,
        get_connected_accounts,
        is_gmail_available,
    )
except ImportError:
    def add_gmail_account():
        return {"error": "Gmail skill not available"}
    def get_connected_accounts():
        return []
    def is_gmail_available():
        return False

from theme import (
    get_current_theme,
    generate_qss,
    apply_theme_to_app,
    refresh_theme,
    add_theme_listener,
)


# ================================================================
# COLORS
# ================================================================

BACKGROUND = "#080B14"
SIDEBAR = "#0D111D"
CARD = "#111827"
CARD_HOVER = "#151E30"
BORDER = "#24324D"

TEXT = "#F5F7FF"
MUTED = "#8995AE"

ACCENT = "#9B5CFF"
ACCENT_HOVER = "#AC73FF"

SUCCESS = "#36D399"
DANGER = "#FF5577"


# ================================================================
# SETTINGS CATEGORIES
# ================================================================

CATEGORIES = [
    (
        "General",
        "General application behavior",
    ),

    (
        "Voice & Audio",
        "Voice and speech settings",
    ),

    (
        "AI Engine",
        "AI provider and response behavior",
    ),

    (
        "API Keys",
        "Manage AI provider API keys",
    ),

    (
        "Memory",
        "Long-term memory controls",
    ),

    (
        "Character",
        "AI Friend character behavior",
    ),

    (
        "Companion Settings",
        "Customize the floating companion appearance and behavior",
    ),

    (
        "Appearance",
        "Theme and visual preferences",
    ),

    (
        "Privacy & Security",
        "Permissions and confirmations",
    ),

    (
        "Power & Automation",
        "Computer power controls",
    ),

    (
        "Gmail",
        "Email integration settings",
    ),

    (
        "Files & Computer",
        "File and computer permissions",
    ),

    (
        "Advanced",
        "Developer and system controls",
    ),

    (
        "Activity Awareness",
        "Proactive behavior and activity detection",
    ),

    (
        "Personality",
        "AI Friend personality and tone",
    ),

    (
        "Timer",
        "Timer notifications and sounds",
    ),

    (
        "System",
        "Application information",
    ),
]


# ================================================================
# CUSTOM SWITCH
# ================================================================

class SettingSwitch(QCheckBox):

    def __init__(
        self,
        checked=False,
        parent=None,
    ):

        super().__init__(parent)

        self.setChecked(
            bool(checked)
        )

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setFixedSize(
            52,
            28,
        )

        self.setStyleSheet(
            f"""
            QCheckBox {{
                background: transparent;
                border: none;
            }}

            QCheckBox::indicator {{
                width: 52px;
                height: 28px;
                border-radius: 14px;
                background: #202A40;
                border: 1px solid {BORDER};
            }}

            QCheckBox::indicator:checked {{
                background: {ACCENT};
                border: 1px solid {ACCENT};
            }}

            QCheckBox::indicator:unchecked:hover {{
                background: #2A3650;
            }}

            QCheckBox::indicator:checked:hover {{
                background: {ACCENT_HOVER};
            }}
            """
        )


# ================================================================
# SETTING CARD
# ================================================================

class SettingCard(QFrame):

    def __init__(
        self,
        title: str,
        description: str,
        control: QWidget,
        parent=None,
    ):

        super().__init__(parent)

        self.setObjectName(
            "SettingCard"
        )

        self.setMinimumHeight(
            82
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setStyleSheet(
            f"""
            QFrame#SettingCard {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}

            QFrame#SettingCard:hover {{
                background: {CARD_HOVER};
                border: 1px solid #35466A;
            }}
            """
        )

        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            22,
            15,
            22,
            15,
        )

        layout.setSpacing(
            20
        )

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            4
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            """
        )

        description_label = QLabel(
            description
        )

        description_label.setWordWrap(
            True
        )

        description_label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 12px;
            background: transparent;
            """
        )

        text_layout.addWidget(
            title_label
        )

        text_layout.addWidget(
            description_label
        )

        layout.addLayout(
            text_layout,
            1,
        )

        layout.addWidget(
            control,
            0,
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter,
        )


# ================================================================
# SECTION HEADER
# ================================================================

class SectionHeader(QWidget):

    def __init__(
        self,
        title: str,
        description: str,
        parent=None,
    ):

        super().__init__(parent)

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            6,
            0,
            10,
        )

        layout.setSpacing(
            5
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 27px;
            font-weight: 700;
            background: transparent;
            """
        )

        description_label = QLabel(
            description
        )

        description_label.setWordWrap(
            True
        )

        description_label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 14px;
            background: transparent;
            """
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            description_label
        )


# ================================================================
# SETTINGS WINDOW
# ================================================================

class SettingsPage(QWidget):

    settings_changed = Signal(
        str,
        object,
    )

    navigate_back = Signal()

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.setWindowTitle(
            "AI Friend Settings"
        )

        self.setMinimumSize(
            950,
            650,
        )

        self.build_ui()

        self.apply_styles()

    # ============================================================
    # BACK TO CHAT
    # ============================================================

    def back_to_chat(self):

        self.navigate_back.emit()

    # ============================================================
    # BUILD UI
    # ============================================================

    def build_ui(self):

        root_layout = QHBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(
            0
        )

        # ========================================================
        # SIDEBAR
        # ========================================================

        self.sidebar = QFrame()

        self.sidebar.setObjectName(
            "Sidebar"
        )

        self.sidebar.setFixedWidth(
            270
        )

        sidebar_layout = QVBoxLayout(
            self.sidebar
        )

        sidebar_layout.setContentsMargins(
            20,
            26,
            20,
            20,
        )

        sidebar_layout.setSpacing(
            10
        )

        # --------------------------------------------------------
        # BRAND
        # --------------------------------------------------------

        brand_title = QLabel(
            "AI FRIEND"
        )

        brand_title.setStyleSheet(
            f"""
            color: {ACCENT};
            font-size: 21px;
            font-weight: 800;
            letter-spacing: 2px;
            background: transparent;
            """
        )

        brand_subtitle = QLabel(
            "CONTROL CENTER"
        )

        brand_subtitle.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 10px;
            letter-spacing: 2px;
            background: transparent;
            """
        )

        sidebar_layout.addWidget(
            brand_title
        )

        sidebar_layout.addWidget(
            brand_subtitle
        )

        sidebar_layout.addSpacing(
            18
        )

        # ========================================================
        # CATEGORY LIST
        # ========================================================

        self.category_list = QListWidget()

        self.category_list.setSpacing(
            5
        )

        self.category_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.category_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        for category_name, description in CATEGORIES:

            item = QListWidgetItem(
                category_name
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                category_name,
            )

            self.category_list.addItem(
                item
            )

        self.category_list.currentRowChanged.connect(
            self.change_category
        )

        sidebar_layout.addWidget(
            self.category_list,
            1,
        )

        # ========================================================
        # SIDEBAR FOOTER
        # ========================================================

        footer = QLabel(
            "AI Friend Settings\n"
            "Changes are saved automatically."
        )

        footer.setWordWrap(
            True
        )

        footer.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 11px;
            padding-top: 10px;
            background: transparent;
            """
        )

        sidebar_layout.addWidget(
            footer
        )

        root_layout.addWidget(
            self.sidebar
        )

        # ========================================================
        # MAIN AREA
        # ========================================================

        self.main_area = QFrame()

        self.main_area.setObjectName(
            "MainArea"
        )

        main_layout = QVBoxLayout(
            self.main_area
        )

        main_layout.setContentsMargins(
            38,
            28,
            38,
            28,
        )

        main_layout.setSpacing(
            0
        )

        # ========================================================
        # TOP BAR
        # ========================================================

        top_bar = QHBoxLayout()

        top_bar.setSpacing(
            10
        )

        self.page_title = QLabel(
            "General"
        )

        self.page_title.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 28px;
            font-weight: 700;
            background: transparent;
            """
        )

        self.page_description = QLabel(
            "General application behavior"
        )

        self.page_description.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 13px;
            background: transparent;
            """
        )

        title_layout = QVBoxLayout()

        title_layout.setSpacing(
            4
        )

        title_layout.addWidget(
            self.page_title
        )

        title_layout.addWidget(
            self.page_description
        )

        top_bar.addLayout(
            title_layout
        )

        top_bar.addStretch()

        # ========================================================
        # BACK TO CHAT BUTTON
        # ========================================================

        self.back_button = QPushButton(
            "←  Back to Chat"
        )

        self.back_button.setObjectName(
            "BackButton"
        )

        self.back_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.back_button.clicked.connect(
            self.back_to_chat
        )

        top_bar.addWidget(
            self.back_button
        )

        # ========================================================
        # BACKUP BUTTON
        # ========================================================

        backup_button = QPushButton(
            "Create Backup"
        )

        backup_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        backup_button.clicked.connect(
            self.create_backup
        )

        top_bar.addWidget(
            backup_button
        )

        # ========================================================
        # RESET BUTTON
        # ========================================================

        reset_button = QPushButton(
            "Reset All"
        )

        reset_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        reset_button.clicked.connect(
            self.reset_everything
        )

        top_bar.addWidget(
            reset_button
        )

        main_layout.addLayout(
            top_bar
        )

        main_layout.addSpacing(
            24
        )

        # ========================================================
        # SCROLL AREA
        # ========================================================

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.content_widget = QWidget()

        self.content_widget.setObjectName(
            "ContentWidget"
        )

        self.content_layout = QVBoxLayout(
            self.content_widget
        )

        self.content_layout.setContentsMargins(
            0,
            0,
            10,
            24,
        )

        self.content_layout.setSpacing(
            12
        )

        self.scroll_area.setWidget(
            self.content_widget
        )

        main_layout.addWidget(
            self.scroll_area,
            1,
        )

        root_layout.addWidget(
            self.main_area,
            1,
        )

        self.category_list.setCurrentRow(
            0
        )

    # ============================================================
    # STYLES
    # ============================================================

    def apply_styles(self):

        self.setStyleSheet(
            generate_qss()
        )

    # ============================================================
    # CATEGORY SWITCHING
    # ============================================================

    def change_category(
        self,
        index: int,
    ):

        if index < 0:

            return

        if index >= len(
            CATEGORIES
        ):

            return

        category_name = CATEGORIES[index][0]

        self.page_title.setText(
            category_name
        )

        self.page_description.setText(
            CATEGORIES[index][1]
        )

        self.clear_content()

        builders = {

            "General":
            self.build_general,

            "Voice & Audio":
            self.build_voice,

            "AI Engine":
            self.build_ai,

            "API Keys":
            self.build_api_keys,

            "Memory":
            self.build_memory,

            "Character":
            self.build_character,

            "Companion Settings":
            self.build_companion,

            "Appearance":
            self.build_appearance,

            "Privacy & Security":
            self.build_privacy,

            "Power & Automation":
            self.build_power,

            "Gmail":
            self.build_gmail,

            "Files & Computer":
            self.build_files,

            "Advanced":
            self.build_advanced,

            "Activity Awareness":
            self.build_activity,

            "Personality":
            self.build_personality,

            "Timer":
            self.build_timer,

            "System":
            self.build_system,
        }

        builder = builders.get(
            category_name
        )

        if builder:

            builder()

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

    # ============================================================
    # CONTENT HELPERS
    # ============================================================

    def clear_content(self):

        while self.content_layout.count():

            item = self.content_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget:

                widget.deleteLater()

    def add_section(
        self,
        title,
        description,
    ):

        header = SectionHeader(
            title,
            description,
        )

        self.content_layout.addWidget(
            header
        )

    def add_card(
        self,
        title,
        description,
        control,
    ):

        card = SettingCard(
            title,
            description,
            control,
        )

        self.content_layout.addWidget(
            card
        )

    def add_spacer(self):

        self.content_layout.addStretch(
            1
        )

    # ============================================================
    # SAFE SETTING READ
    # ============================================================

    def read_setting(
        self,
        path,
        default,
    ):

        try:

            return get_setting(
                path,
                default,
            )

        except Exception:

            return default

    # ============================================================
    # SWITCH
    # ============================================================

    def add_switch(
        self,
        path,
        title,
        description,
        default=True,
    ):

        switch = SettingSwitch(
            self.read_setting(
                path,
                default,
            )
        )

        switch.toggled.connect(

            lambda value,
            p=path:

            self.change_setting(
                p,
                value,
            )

        )

        self.add_card(
            title,
            description,
            switch,
        )

    # ============================================================
    # COMBO
    # ============================================================

    def add_combo(
        self,
        path,
        title,
        description,
        values,
        labels=None,
    ):

        combo = QComboBox()

        if not values:

            return

        if labels is None:

            labels = values

        for value, label in zip(
            values,
            labels,
        ):

            combo.addItem(
                label,
                value,
            )

        current_value = self.read_setting(
            path,
            values[0],
        )

        index = combo.findData(
            current_value
        )

        if index >= 0:

            combo.setCurrentIndex(
                index
            )

        combo.currentIndexChanged.connect(

            lambda index,
            c=combo,
            p=path:

            self.change_setting(
                p,
                c.itemData(index),
            )

        )

        self.add_card(
            title,
            description,
            combo,
        )

    # ============================================================
    # SLIDER
    # ============================================================

    def add_slider(
        self,
        path,
        title,
        description,
        minimum,
        maximum,
        default,
        decimals=0,
    ):

        slider = QSlider(
            Qt.Orientation.Horizontal
        )

        scale = 10 if decimals else 1

        slider.setMinimum(
            int(
                minimum
                * scale
            )
        )

        slider.setMaximum(
            int(
                maximum
                * scale
            )
        )

        current = self.read_setting(
            path,
            default,
        )

        try:

            current = float(
                current
            )

        except (
            TypeError,
            ValueError,
        ):

            current = float(
                default
            )

        current = max(
            minimum,
            min(
                maximum,
                current,
            )
        )

        slider.setValue(
            int(
                current
                * scale
            )
        )

        slider.setFixedWidth(
            180
        )

        slider.valueChanged.connect(

            lambda value,
            p=path,
            s=scale:

            self.change_setting(
                p,
                value / s,
            )

        )

        self.add_card(
            title,
            description,
            slider,
        )

    # ============================================================
    # SETTING UPDATE
    # ============================================================

    def change_setting(
        self,
        path,
        value,
    ):

        try:

            success = set_setting(
                path,
                value,
            )

            if success:

                self.settings_changed.emit(
                    path,
                    value,
                )

        except Exception as error:

            print(
                f"[SETTINGS ERROR] "
                f"{path}: {error}"
            )

    # ============================================================
    # GENERAL
    # ============================================================

    def build_general(self):

        self.add_section(
            "General",
            "Control how AI Friend behaves when you start and use the application.",
        )

        self.add_switch(
            "general.startup_enabled",
            "Start with Windows",
            "Launch AI Friend automatically when your computer starts.",
        )

        self.add_switch(
            "general.start_minimized",
            "Start Minimized",
            "Start the application quietly in the background.",
        )

        self.add_switch(
            "general.check_for_updates",
            "Check for Updates",
            "Automatically check for new application updates.",
        )

        self.add_combo(
            "general.language",
            "Application Language",
            "Choose the language used by the application.",
            ["en"],
            ["English"],
        )

        self.add_spacer()

        # ============================================================
        # SCREEN AWARENESS
        # ============================================================

        self.add_section(
            "Screen Awareness",
            "Control how AVORA understands what is happening on your screen.",
        )

        self.add_switch(
            "screen_awareness.enabled",
            "Enable Screen Awareness",
            "When enabled, AVORA periodically understands what is happening on your screen to provide smarter suggestions and conversations.",
        )

        self.add_combo(
            "screen_awareness.analysis_interval_seconds",
            "Screen Analysis Frequency",
            "How often AVORA analyzes your screen. Lower values are more responsive but use more resources.",
            [2, 5, 10, 30],
            ["2 seconds", "5 seconds (Default)", "10 seconds", "30 seconds"],
        )

        self.add_switch(
            "screen_awareness.only_active_window",
            "Only analyze active window",
            "Only analyze the currently active window for better performance and privacy.",
        )

        self.add_switch(
            "screen_awareness.pause_while_gaming",
            "Pause while gaming",
            "Temporarily pause screen awareness while you are gaming.",
        )

        self.add_spacer()

    # ============================================================
    # VOICE
    # ============================================================

    def build_voice(self):

        self.add_section(
            "Voice & Audio",
            "Customize how your AI Friend speaks and sounds.",
        )

        self.add_switch(
            "voice.enabled",
            "Enable Voice",
            "Allow AI Friend to speak responses aloud.",
        )

        self.add_slider(
            "voice.volume",
            "Voice Volume",
            "Control the volume of spoken responses.",
            0,
            1,
            1.0,
            1,
        )

        self.add_slider(
            "voice.speed",
            "Speech Speed",
            "Control how quickly AI Friend speaks.",
            0.5,
            2.0,
            1.0,
            1,
        )

        self.add_combo(
            "voice.voice_name",
            "Voice",
            "Choose the voice used for speech.",
            [
                "default",
                "en-US-AriaNeural",
                "en-US-JennyNeural",
                "en-US-GuyNeural",
                "en-US-ChristopherNeural",
                "en-GB-SoniaNeural",
                "en-GB-RyanNeural",
                "en-IN-NeerjaNeural",
                "en-IN-PrabhatNeural",
            ],
            [
                "Default",
                "Aria",
                "Jenny",
                "Guy",
                "Christopher",
                "Sonia",
                "Ryan",
                "Neerja",
                "Prabhat",
            ],
        )

        self.add_switch(
            "voice.speak_after_response",
            "Speak After Response",
            "Start speaking after the AI has finished generating its response.",
        )

        self.add_switch(
            "voice.auto_stop_previous",
            "Stop Previous Speech",
            "Automatically stop the previous voice when a new response starts.",
        )

        self.add_spacer()

    # ============================================================
    # AI
    # ============================================================

    def build_ai(self):

        self.add_section(
            "AI Engine",
            "Control AI providers, response style, and performance.",
        )

        self.add_combo(
            "ai.primary_provider",
            "Primary AI Provider",
            "Choose the first AI provider used for responses.",
            [
                "gemini",
                "groq",
                "automatic",
            ],
            [
                "Google Gemini",
                "Groq",
                "Automatic",
            ],
        )

        self.add_combo(
            "ai.fallback_provider",
            "Fallback Provider",
            "Provider used when the primary provider fails.",
            [
                "gemini",
                "groq",
                "automatic",
            ],
            [
                "Google Gemini",
                "Groq",
                "Automatic",
            ],
        )

        self.add_switch(
            "ai.automatic_fallback",
            "Automatic Fallback",
            "Automatically switch to another provider if the current provider fails.",
        )

        self.add_combo(
            "ai.response_length",
            "Response Length",
            "Choose how detailed AI responses should be.",
            [
                "short",
                "balanced",
                "detailed",
            ],
            [
                "Short",
                "Balanced",
                "Detailed",
            ],
        )

        self.add_combo(
            "ai.response_style",
            "Response Style",
            "Choose the personality style of AI responses.",
            [
                "friendly",
                "professional",
                "casual",
                "creative",
            ],
            [
                "Friendly",
                "Professional",
                "Casual",
                "Creative",
            ],
        )

        self.add_switch(
            "ai.command_understanding",
            "Command Understanding",
            "Allow AI Friend to understand natural language commands.",
        )

        self.add_switch(
            "ai.show_processing_status",
            "Show Processing Status",
            "Show when AI Friend is thinking or processing a request.",
        )

        self.add_spacer()

    # ============================================================
    # MEMORY
    # ============================================================

    def build_memory(self):

        self.add_section(
            "Memory",
            "Control what AI Friend remembers between conversations.",
        )

        self.add_switch(
            "memory.enabled",
            "Enable Long-Term Memory",
            "Allow AI Friend to use stored memories.",
        )

        self.add_switch(
            "memory.auto_save",
            "Automatic Memory Saving",
            "Automatically save useful information for future conversations.",
        )

        self.add_switch(
            "memory.ask_before_saving",
            "Ask Before Saving",
            "Ask for permission before creating a new memory.",
        )

        self.add_switch(
            "memory.save_preferences",
            "Save Preferences",
            "Remember your preferences and personal choices.",
        )

        self.add_switch(
            "memory.save_projects",
            "Save Project Information",
            "Remember important information about your projects.",
        )

        self.add_switch(
            "memory.save_goals",
            "Save Goals",
            "Remember your goals and plans.",
        )

        self.add_action_button(
            "View Stored Memories",
            "See all information currently stored in long-term memory.",
            self.view_stored_memories,
        )

        self.add_action_button(
            "Clear All Memories",
            "Delete all stored memories from long-term memory.",
            self.clear_all_memories_ui,
        )

        self.add_spacer()

    # ============================================================
    # CHARACTER
    # ============================================================

    def build_character(self):

        self.add_section(
            "Character",
            "Customize the behavior and animation of your AI Friend.",
        )

        self.add_switch(
            "character.enabled",
            "Enable Character",
            "Show the animated AI Friend character.",
        )

        self.add_slider(
            "character.size",
            "Character Size",
            "Control the size of the character.",
            0.5,
            3.0,
            1.0,
            1,
        )

        self.add_switch(
            "character.eye_tracking",
            "Eye Tracking",
            "Allow the character to follow the cursor with its eyes.",
        )

        self.add_switch(
            "character.blinking",
            "Blinking",
            "Allow natural blinking animations.",
        )

        self.add_switch(
            "character.head_movement",
            "Head Movement",
            "Enable subtle head movement animations.",
        )

        self.add_switch(
            "character.emotions",
            "Emotions",
            "Allow the character to react emotionally to conversations.",
        )

        self.add_switch(
            "character.idle_animation",
            "Idle Animation",
            "Enable animations when the character is idle.",
        )

        self.add_switch(
            "character.talking_animation",
            "Talking Animation",
            "Animate the character while voice is playing.",
        )

        self.add_spacer()

    # ============================================================
    # COMPANION SETTINGS
    # ============================================================

    def build_companion(self):

        self.add_section(
            "Companion Settings",
            "Customize the floating companion appearance and behavior.",
        )

        self.add_switch(
            "companion_widget.enabled",
            "Enable Companion",
            "Show the floating Avora companion on your desktop.",
        )

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(8)

        preview_header = QLabel("Live Preview")
        preview_header.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 13px;
            font-weight: 600;
            background: transparent;
            """
        )
        preview_layout.addWidget(preview_header)

        preview_frame = QFrame()
        preview_frame.setObjectName("CompanionPreviewFrame")
        preview_frame.setFixedHeight(220)
        preview_frame.setStyleSheet(
            f"""
            QFrame#CompanionPreviewFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            """
        )
        preview_inner = QHBoxLayout(preview_frame)
        preview_inner.setContentsMargins(16, 16, 16, 16)
        preview_inner.setSpacing(12)

        try:
            from character import Character
            self.preview_character = Character(preview_frame)
            self.preview_character.set_scale_factor(0.6)
            preview_inner.addWidget(self.preview_character, 0, Qt.AlignmentFlag.AlignCenter)
        except Exception as e:
            print("[PREVIEW] Failed to create preview character:", e)
            self.preview_character = None
            placeholder = QLabel("Preview unavailable")
            placeholder.setStyleSheet(f"color: {MUTED}; background: transparent;")
            preview_inner.addWidget(placeholder, 0, Qt.AlignmentFlag.AlignCenter)

        preview_layout.addWidget(preview_frame)
        self.content_layout.addWidget(preview_container)

        self.add_slider(
            "companion_widget.size",
            "Size",
            "Control the size of the floating companion.",
            0.5,
            2.0,
            1.0,
            1,
        )

        self.add_slider(
            "companion_widget.glow_intensity",
            "Glow Intensity",
            "Control the brightness of the companion glow effect.",
            0.0,
            1.0,
            0.5,
            1,
        )

        glow_color_row = QWidget()
        glow_color_layout = QHBoxLayout(glow_color_row)
        glow_color_layout.setContentsMargins(0, 0, 0, 0)
        glow_color_layout.setSpacing(8)

        glow_color_label = QLabel("Glow Color")
        glow_color_label.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            """
        )
        glow_color_layout.addWidget(glow_color_label)

        glow_color_presets = QWidget()
        glow_color_presets_layout = QHBoxLayout(glow_color_presets)
        glow_color_presets_layout.setContentsMargins(0, 0, 0, 0)
        glow_color_presets_layout.setSpacing(6)

        self.glow_color_buttons = []
        preset_colors = [
            ("Green", "#00FF88"),
            ("Cyan", "#00B4D8"),
            ("Purple", "#9B5CFF"),
            ("Blue", "#3B82F6"),
            ("Pink", "#EC4899"),
        ]

        for label, color in preset_colors:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(label)
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {color};
                    border: 2px solid transparent;
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border: 2px solid {TEXT};
                }}
                QPushButton:checked {{
                    border: 2px solid {TEXT};
                }}
                """
            )
            btn.setCheckable(True)
            btn.clicked.connect(
                lambda _, c=color, b=btn: self._set_glow_color(c, b)
            )
            glow_color_presets_layout.addWidget(btn)
            self.glow_color_buttons.append(btn)

        self.custom_color_btn = QPushButton()
        self.custom_color_btn.setFixedSize(28, 28)
        self.custom_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.custom_color_btn.setToolTip("Custom")
        self.custom_color_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: #FFFFFF;
                border: 2px dashed {BORDER};
                border-radius: 14px;
            }}
            QPushButton:hover {{
                border: 2px solid {TEXT};
            }}
            """
            f"""
            QPushButton::menu-indicator {{
                width: 0;
                height: 0;
            }}
            """
        )
        self.custom_color_btn.clicked.connect(self._pick_custom_glow_color)
        glow_color_presets_layout.addWidget(self.custom_color_btn)

        glow_color_layout.addWidget(glow_color_presets)
        self.content_layout.addWidget(glow_color_row)

        self._update_glow_color_buttons()

        self.add_combo(
            "companion_widget.animation",
            "Animation",
            "Choose the idle animation style for the companion.",
            [
                "none",
                "gentle_float",
                "pulse",
                "bounce",
                "breathing",
                "glow_pulse",
            ],
            [
                "None",
                "Gentle Float",
                "Pulse",
                "Bounce",
                "Breathing",
                "Glow Pulse",
            ],
        )

        reset_button = QPushButton(
            "Reset to Default"
        )
        reset_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        reset_button.clicked.connect(
            self._reset_companion_settings
        )
        self.content_layout.addWidget(reset_button)

        self.settings_changed.connect(
            self._on_companion_setting_changed
        )

    def _update_glow_color_buttons(self):
        try:
            from settings import get_setting
            current_color = get_setting("companion_widget.glow_color", "#00FF88")
        except Exception:
            current_color = "#00FF88"

        preset_colors = ["#00FF88", "#00B4D8", "#9B5CFF", "#3B82F6", "#EC4899"]
        for i, btn in enumerate(self.glow_color_buttons):
            btn.setChecked(current_color == preset_colors[i])

    def _set_glow_color(self, color, button):
        try:
            from settings import set_setting
            set_setting("companion_widget.glow_color", color)
        except Exception:
            pass
        for btn in self.glow_color_buttons:
            btn.setChecked(False)
        button.setChecked(True)
        self._update_preview_character()

    def _pick_custom_glow_color(self):
        try:
            from settings import get_setting
            current = get_setting("companion_widget.glow_color", "#00FF88")
        except Exception:
            current = "#00FF88"

        color = QColorDialog.getColor(QColor(current), self, "Select Glow Color")
        if color.isValid():
            hex_color = color.name().upper()
            try:
                from settings import set_setting
                set_setting("companion_widget.glow_color", hex_color)
            except Exception:
                pass
            for btn in self.glow_color_buttons:
                btn.setChecked(False)
            self._update_preview_character()

    def _on_companion_setting_changed(self, path, value):
        if path and path.startswith("companion_widget."):
            self._update_preview_character()
            self._update_glow_color_buttons()

    def _update_preview_character(self):
        if hasattr(self, 'preview_character') and self.preview_character is not None:
            try:
                self.preview_character.apply_companion_settings()
            except Exception:
                pass

    def _reset_companion_settings(self):
        try:
            from settings import set_setting
            set_setting("companion_widget.enabled", True)
            set_setting("companion_widget.size", 1.0)
            set_setting("companion_widget.glow_intensity", 0.5)
            set_setting("companion_widget.glow_color", "#00FF88")
            set_setting("companion_widget.animation", "gentle_float")
            set_setting("companion_widget.position_x", -1)
            set_setting("companion_widget.position_y", -1)
        except Exception:
            pass
        self._update_glow_color_buttons()
        self._update_preview_character()

    # ============================================================
    # APPEARANCE
    # ============================================================

    def build_appearance(self):

        self.add_section(
            "Appearance",
            "Customize the visual appearance of AI Friend.",
        )

        self.add_combo(
            "appearance.theme",
            "Theme",
            "Choose the visual theme of the application.",
            [
                "dark",
                "light",
                "system",
            ],
            [
                "Dark Mode",
                "Light Mode",
                "System Mode",
            ],
        )

        self.add_combo(
            "appearance.animation_intensity",
            "Animation Intensity",
            "Control the amount of visual animation.",
            [
                "low",
                "medium",
                "high",
            ],
            [
                "Low",
                "Medium",
                "High",
            ],
        )

        self.add_switch(
            "appearance.glass_effect",
            "Glass Effect",
            "Enable glass-style visual panels.",
        )

        self.add_switch(
            "appearance.compact_mode",
            "Compact Mode",
            "Use a more compact interface layout.",
        )

        self.add_switch(
            "appearance.show_timestamps",
            "Show Timestamps",
            "Display timestamps on chat messages.",
        )

        self.add_switch(
            "appearance.show_message_animations",
            "Message Animations",
            "Animate new chat messages.",
        )

        self.add_switch(
            "appearance.rounded_corners",
            "Rounded Corners",
            "Use rounded corners throughout the interface.",
        )

        self.add_spacer()

    # ============================================================
    # PRIVACY
    # ============================================================

    def build_privacy(self):

        self.add_section(
            "Privacy & Security",
            "Control confirmations, permissions, and AI access.",
        )

        self.add_switch(
            "privacy.confirm_power_actions",
            "Confirm Power Actions",
            "Ask before shutdown, restart, sleep, or similar actions.",
        )

        self.add_switch(
            "privacy.confirm_file_deletion",
            "Confirm File Deletion",
            "Ask before deleting files.",
        )

        self.add_switch(
            "privacy.confirm_email_sending",
            "Confirm Email Sending",
            "Ask before sending emails.",
        )

        self.add_switch(
            "privacy.confirm_email_deletion",
            "Confirm Email Deletion",
            "Ask before deleting emails.",
        )

        self.add_switch(
            "privacy.confirm_system_changes",
            "Confirm System Changes",
            "Ask before making important system changes.",
        )

        self.add_switch(
            "privacy.allow_ai_file_creation",
            "Allow AI File Creation",
            "Allow AI Friend to create files.",
        )

        self.add_switch(
            "privacy.allow_ai_file_opening",
            "Allow AI File Opening",
            "Allow AI Friend to open files.",
        )

        self.add_switch(
            "privacy.allow_ai_file_deletion",
            "Allow AI File Deletion",
            "Allow AI Friend to delete files.",
        )

        self.add_switch(
            "privacy.allow_ai_system_commands",
            "Allow System Commands",
            "Allow AI Friend to perform system commands.",
        )

        self.add_switch(
            "privacy.store_conversation_history",
            "Store Conversation History",
            "Allow conversations to be stored locally.",
        )

        # Analytics & Data Section
        self.add_section(
            "Analytics & Data",
            "Help improve AVORA by sharing anonymous usage data.",
        )

        self.add_switch(
            "analytics.enabled",
            "Enable Analytics",
            "Allow anonymous usage analytics to help improve the application.",
        )

        self.add_switch(
            "analytics.anonymous_usage_data",
            "Anonymous Usage Data",
            "Share anonymous usage statistics. No personal information is collected.",
        )

        self.add_switch(
            "analytics.update_checks",
            "Automatic Update Checks",
            "Periodically check for new versions in the background.",
        )

        self.add_spacer()

    # ============================================================
    # POWER
    # ============================================================

    def build_power(self):

        self.add_section(
            "Power & Automation",
            "Control computer power and automation features.",
        )

        self.add_switch(
            "power.allow_shutdown",
            "Allow Shutdown",
            "Allow AI Friend to shut down the computer.",
        )

        self.add_switch(
            "power.allow_restart",
            "Allow Restart",
            "Allow AI Friend to restart the computer.",
        )

        self.add_switch(
            "power.allow_sleep",
            "Allow Sleep",
            "Allow AI Friend to put the computer to sleep.",
        )

        self.add_switch(
            "power.allow_hibernate",
            "Allow Hibernate",
            "Allow AI Friend to hibernate the computer.",
        )

        self.add_switch(
            "power.allow_lock",
            "Allow Lock",
            "Allow AI Friend to lock the computer.",
        )

        self.add_switch(
            "power.allow_scheduled_actions",
            "Scheduled Actions",
            "Allow scheduled power actions.",
        )

        self.add_spacer()

    # ============================================================
    # GMAIL
    # ============================================================

    def build_gmail(self):

        self.add_section(
            "Gmail",
            "Control Gmail integration and email behavior.",
        )

        self.add_switch(
            "gmail.enabled",
            "Enable Gmail Integration",
            "Allow AI Friend to interact with Gmail. When disabled, all Gmail features are turned off.",
        )

        self.add_action_button(
            "Connect Gmail Account",
            "Sign in with Google to connect your Gmail account. Opens a browser for OAuth login.",
            self.connect_gmail_account,
        )

        self.add_switch(
            "gmail.auto_check",
            "Automatic Email Checking",
            "Automatically check for new emails.",
        )

        self.add_switch(
            "gmail.confirm_send",
            "Confirm Before Sending",
            "Ask before sending an email.",
        )

        self.add_switch(
            "gmail.confirm_delete",
            "Confirm Before Deleting",
            "Ask before deleting an email.",
        )

        self.add_switch(
            "gmail.mark_as_read_after_reading",
            "Mark Read Emails",
            "Mark emails as read after AI Friend reads them.",
        )

        self.add_spacer()

    # ============================================================
    # FILES
    # ============================================================

    def build_files(self):

        self.add_section(
            "Files & Computer",
            "Control AI Friend's access to your files.",
        )

        self.add_switch(
            "files.enabled",
            "Enable File Skills",
            "Allow AI Friend to use file-related skills.",
        )

        self.add_switch(
            "files.allow_create",
            "Allow File Creation",
            "Allow AI Friend to create files.",
        )

        self.add_switch(
            "files.allow_open",
            "Allow File Opening",
            "Allow AI Friend to open files.",
        )

        self.add_switch(
            "files.allow_delete",
            "Allow File Deletion",
            "Allow AI Friend to delete files.",
        )

        self.add_switch(
            "files.allow_move",
            "Allow File Moving",
            "Allow AI Friend to move files.",
        )

        self.add_switch(
            "files.allow_rename",
            "Allow File Renaming",
            "Allow AI Friend to rename files.",
        )

        self.add_switch(
            "files.show_hidden_files",
            "Show Hidden Files",
            "Allow hidden files to be shown.",
        )

        self.add_spacer()

    # ============================================================
    # ADVANCED
    # ============================================================

    def build_advanced(self):

        self.add_switch(
            "advanced.debug_mode",
            "Debug Mode",
            "Enable additional debugging information.",
        )

        self.add_switch(
            "advanced.show_api_errors",
            "Show API Errors",
            "Display detailed API errors.",
        )

        self.add_switch(
            "advanced.show_internal_errors",
            "Show Internal Errors",
            "Display internal application errors.",
        )

        self.add_switch(
            "advanced.enable_logging",
            "Enable Logging",
            "Save application logs for troubleshooting.",
        )

        self.add_switch(
            "advanced.enable_crash_recovery",
            "Crash Recovery",
            "Enable recovery systems after application crashes.",
        )

        self.add_switch(
            "advanced.developer_mode",
            "Developer Mode",
            "Enable experimental developer features.",
        )

        self.add_action_button(
            "Export Settings",
            "Save all your settings to a JSON file.",
            self.export_settings_file,
        )

        self.add_action_button(
            "Import Settings",
            "Load settings from a previously exported JSON file.",
            self.import_settings_file,
        )

        self.add_spacer()

    # ============================================================
    # API KEYS
    # ============================================================

    def build_api_keys(self):

        self.add_section(
            "API Keys",
            "Manage your AI provider API keys. Keys are stored securely on your device.",
        )

        # Info text
        info_label = QLabel(
            "API keys are required for AI functionality. "
            "Keys are never shared and are stored encrypted on your device. "
            "Only masked versions are visible in logs."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"""
            color: {MUTED};
            font-size: 13px;
            padding: 10px;
            background: {CARD};
            border-radius: 8px;
            border: 1px solid {BORDER};
        """)
        self.content_layout.addWidget(info_label)

        self.content_layout.addSpacing(20)

        # Gemini API Key
        self.add_api_key_card(
            "gemini",
            "Gemini API Key",
            "Google Gemini (Primary AI Provider)",
            "Get your key at https://makersuite.google.com/app/apikey",
            "AI"
        )

        # Groq API Key
        self.add_api_key_card(
            "groq",
            "Groq API Key",
            "Groq (Fast AI Provider)",
            "Get your key at https://console.groq.com/keys",
            "gsk_"
        )

        # OpenAI API Key (optional)
        self.add_api_key_card(
            "openai",
            "OpenAI API Key (Optional)",
            "OpenAI GPT Models (Optional)",
            "Get your key at https://platform.openai.com/api-keys",
            "sk-"
        )

        self.content_layout.addSpacing(20)

        # Status section
        self.add_section(
            "Connection Status",
            "Current status of all configured AI providers.",
        )

        self.status_widget = QWidget()
        self.status_layout = QVBoxLayout(self.status_widget)
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setSpacing(10)
        self.content_layout.addWidget(self.status_widget)

        # Refresh button
        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_provider_status)
        self.content_layout.addWidget(refresh_btn)

        self.content_layout.addStretch(1)

        # Initial status check
        self.refresh_provider_status()

    def add_api_key_card(self, provider_id, title, subtitle, help_text, prefix=""):
        """Create a card for managing an API key."""
        card = QFrame()
        card.setObjectName("SettingCard")
        card.setMinimumHeight(120)
        card.setStyleSheet(f"""
            QFrame#SettingCard {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QFrame#SettingCard:hover {{
                background: {CARD_HOVER};
                border: 1px solid #35466A;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Title row
        title_row = QHBoxLayout()
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setStyleSheet(f"color: {TEXT}; font-size: 14px;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"color: {MUTED}; font-size: 11px;")

        title_row.addWidget(title_label)
        title_row.addWidget(subtitle_label, 1, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(title_row)

        # Help text
        help_label = QLabel(help_text)
        help_label.setWordWrap(True)
        help_label.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        layout.addWidget(help_label)

        # Input row
        input_row = QHBoxLayout()

        # Get current masked key
        storage = get_secure_storage()
        stored_key = storage.get_key(provider_id)
        masked = mask_key(stored_key) if stored_key else "Not configured"

        self.key_inputs = getattr(self, 'key_inputs', {})
        key_input = QLineEdit()
        key_input.setPlaceholderText(f"Enter {title}...")
        key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_input.setStyleSheet(f"""
            QLineEdit {{
                background: {BACKGROUND};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT};
            }}
        """)
        key_input.setMinimumWidth(300)
        self.key_inputs[provider_id] = key_input
        input_row.addWidget(key_input)

        # Toggle visibility button
        toggle_btn = QPushButton("👁")
        toggle_btn.setFixedSize(36, 36)
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BACKGROUND};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {CARD_HOVER};
            }}
        """)

        def toggle_visibility():
            if key_input.echoMode() == QLineEdit.EchoMode.Password:
                key_input.setEchoMode(QLineEdit.EchoMode.Normal)
                toggle_btn.setText("🙈")
            else:
                key_input.setEchoMode(QLineEdit.EchoMode.Password)
                toggle_btn.setText("👁")

        toggle_btn.clicked.connect(toggle_visibility)
        input_row.addWidget(toggle_btn)

        # Save button
        save_btn = QPushButton("Save")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {ACCENT_HOVER};
            }}
        """)

        def save_key():
            key = key_input.text().strip()
            if not key:
                QMessageBox.warning(self, "Invalid Key", "Please enter a valid API key.")
                return

            # Validate format
            valid, msg = validate_key_format(provider_id, key)
            if not valid:
                reply = QMessageBox.question(
                    self,
                    "Key Format Warning",
                    f"{msg}\n\nSave anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Save to secure storage
            storage = get_secure_storage()
            if storage.set_key(provider_id, key):
                QMessageBox.information(self, "Key Saved", f"{title} saved successfully!\n\nKey is encrypted and stored securely.")
                key_input.clear()
                self.refresh_provider_status()
            else:
                QMessageBox.critical(self, "Save Failed", "Could not save the API key.")

        save_btn.clicked.connect(save_key)
        input_row.addWidget(save_btn)

        # Test button
        test_btn = QPushButton("Test")
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BACKGROUND};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {CARD_HOVER};
            }}
        """)

        def test_key():
            key = key_input.text().strip() or stored_key
            if not key:
                QMessageBox.warning(self, "No Key", "Please enter an API key to test.")
                return

            test_btn.setEnabled(False)
            test_btn.setText("Testing...")
            QApplication.processEvents()

            success, message = test_provider_connection(provider_id, key)

            test_btn.setEnabled(True)
            test_btn.setText("Test")

            if success:
                QMessageBox.information(self, "Connection Successful", f"✓ {message}")
            else:
                QMessageBox.warning(self, "Connection Failed", f"✗ {message}")

        test_btn.clicked.connect(test_key)
        input_row.addWidget(test_btn)

        layout.addLayout(input_row)

        # Current status
        status_label = QLabel(f"Current: {masked}")
        status_label.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        layout.addWidget(status_label)

        self.content_layout.addWidget(card)

    def refresh_provider_status(self):
        """Refresh the connection status for all providers."""
        try:
            # Clear existing status widgets
            while self.status_layout.count():
                item = self.status_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            providers = [
                ("gemini", "Gemini", GEMINI_KEY),
                ("groq", "Groq", GROQ_KEY),
                ("openai", "OpenAI", OPENAI_KEY),
            ]

            for provider_id, name, key in providers:
                status_row = QHBoxLayout()

                if key:
                    # Test connection
                    success, message = test_provider_connection(provider_id, key)
                    if success:
                        status_icon = QLabel("✅")
                        status_text = QLabel(f"<b>{name}</b>: {message}")
                        status_text.setStyleSheet(f"color: {SUCCESS}; font-size: 13px;")
                    else:
                        status_icon = QLabel("❌")
                        status_text = QLabel(f"<b>{name}</b>: {message}")
                        status_text.setStyleSheet(f"color: {DANGER}; font-size: 13px;")
                else:
                    status_icon = QLabel("⚪")
                    status_text = QLabel(f"<b>{name}</b>: Not configured")
                    status_text.setStyleSheet(f"color: {MUTED}; font-size: 13px;")

                status_row.addWidget(status_icon)
                status_row.addWidget(status_text, 1)
                self.status_layout.addLayout(status_row)

        except Exception as e:
            print(f"[Status Refresh Error] {e}")

    # ============================================================
    # ADVANCED
    # ============================================================

    def build_advanced(self):

        self.add_switch(
            "advanced.debug_mode",
            "Debug Mode",
            "Enable additional debugging information.",
        )

        self.add_switch(
            "advanced.show_api_errors",
            "Show API Errors",
            "Display detailed API errors.",
        )

        self.add_switch(
            "advanced.show_internal_errors",
            "Show Internal Errors",
            "Display internal application errors.",
        )

        self.add_switch(
            "advanced.enable_logging",
            "Enable Logging",
            "Save application logs for troubleshooting.",
        )

        self.add_switch(
            "advanced.enable_crash_recovery",
            "Crash Recovery",
            "Enable recovery systems after application crashes.",
        )

        self.add_switch(
            "advanced.developer_mode",
            "Developer Mode",
            "Enable experimental developer features.",
        )

        self.add_action_button(
            "Export Settings",
            "Save all your settings to a JSON file.",
            self.export_settings_file,
        )

        self.add_action_button(
            "Import Settings",
            "Load settings from a previously exported JSON file.",
            self.import_settings_file,
        )

        self.add_spacer()

    # ============================================================
    # SYSTEM
    # ============================================================

    def build_system(self):

        self.add_section(
            "System",
            "Application information and settings management.",
        )

        self.add_action_button(
            "Create Settings Backup",
            "Create a backup of your current settings.",
            self.create_backup,
        )

        self.add_action_button(
            "Reset All Settings",
            "Restore all settings to their factory defaults.",
            self.reset_everything,
        )

        backups = get_available_backups()

        if backups:

            self.add_section(
                "Available Backups",
                "Restore a previous settings configuration.",
            )

            for backup in backups[:10]:

                filename = Path(
                    backup
                ).name

                self.add_action_button(
                    filename,
                    "Restore this settings backup.",
                    lambda checked=False,
                    path=backup:

                    self.restore_backup_file(
                        path
                    ),
                )

        self.add_spacer()

    # ============================================================
    # ACTIVITY AWARENESS
    # ============================================================

    def build_activity(self):

        self.add_section(
            "Activity Awareness",
            "Control how AI Friend detects your activity and sends proactive messages.",
        )

        self.add_switch(
            "activity_awareness.enabled",
            "Enable Activity Awareness",
            "Allow AI Friend to detect your current activity.",
        )

        self.add_switch(
            "activity_awareness.proactive_notifications",
            "Proactive Notifications",
            "Show helpful messages based on what you're doing.",
        )

        self.add_switch(
            "activity_awareness.show_activity_notifications",
            "Activity Notifications",
            "Show notification when your activity changes.",
        )

        self.add_slider(
            "activity_awareness.proactive_cooldown_minutes",
            "Notification Cooldown",
            "Minimum minutes between proactive notifications.",
            5,
            60,
            15,
            0,
        )

        self.add_slider(
            "activity_awareness.long_session_warning_minutes",
            "Long Session Warning",
            "Minutes before warning about long work sessions.",
            30,
            180,
            60,
            0,
        )

        self.add_switch(
            "activity_awareness.break_reminder_enabled",
            "Break Reminders",
            "Periodically remind you to take breaks.",
        )

        self.add_slider(
            "activity_awareness.break_reminder_interval_minutes",
            "Break Interval",
            "Minutes between break reminders.",
            15,
            120,
            45,
            0,
        )

        self.add_switch(
            "activity_awareness.privacy_mode",
            "Privacy Mode",
            "Only detect activity types, not specific apps or titles.",
        )

        self.add_spacer()

    # ============================================================
    # PERSONALITY
    # ============================================================

    def build_personality(self):

        self.add_section(
            "Personality",
            "Choose and customize how AI Friend behaves.",
        )

        self.add_combo(
            "personality.current_personality",
            "Current Personality",
            "Select the active personality for AI Friend.",
            [
                "friendly_bro",
                "professional",
                "calm_companion",
                "funny_friend",
                "study_buddy",
                "coding_partner",
                "custom",
            ],
            [
                "Friendly Bro",
                "Professional",
                "Calm Companion",
                "Funny Friend",
                "Study Buddy",
                "Coding Partner",
                "Custom",
            ],
        )

        self.add_slider(
            "personality.casual_professional",
            "Casual ↔ Professional",
            "Control how casual or formal the AI sounds.",
            0,
            1,
            0.5,
            1,
        )

        self.add_slider(
            "personality.calm_energetic",
            "Calm ↔ Energetic",
            "Control the energy level of responses.",
            0,
            1,
            0.5,
            1,
        )

        self.add_slider(
            "personality.serious_funny",
            "Serious ↔ Funny",
            "Control how serious or humorous the AI is.",
            0,
            1,
            0.5,
            1,
        )

        self.add_slider(
            "personality.emoji_usage",
            "Emoji Usage",
            "How often emojis appear in responses.",
            0,
            1,
            0.7,
            1,
        )

        self.add_slider(
            "personality.slang_usage",
            "Slang Usage",
            "How much casual slang appears in responses.",
            0,
            1,
            0.3,
            1,
        )

        self.add_slider(
            "personality.proactivity",
            "Proactivity",
            "How often AI offers suggestions without being asked.",
            0,
            1,
            0.5,
            1,
        )

        self.add_spacer()

    # ============================================================
    # TIMER
    # ============================================================

    def build_timer(self):

        self.add_section(
            "Timer",
            "Control timer notifications and sounds.",
        )

        self.add_switch(
            "timer.enabled",
            "Enable Timers",
            "Allow AI Friend to create and manage timers.",
        )

        self.add_switch(
            "timer.notification_on_finish",
            "Notification on Finish",
            "Show a notification when a timer completes.",
        )

        self.add_switch(
            "timer.notification_sound",
            "Play Sound",
            "Play a sound when a timer completes.",
        )

        self.add_slider(
            "timer.notification_volume",
            "Notification Volume",
            "Volume of timer completion sound.",
            0,
            1,
            0.8,
            1,
        )

        self.add_switch(
            "timer.speak_on_finish",
            "Speak on Finish",
            "Announce timer completion with voice.",
        )

        self.add_combo(
            "timer.emotion_on_finish",
            "Emotion on Finish",
            "Character emotion when a timer completes.",
            [
                "surprised",
                "happy",
                "excited",
                "idle",
            ],
            [
                "Surprised",
                "Happy",
                "Excited",
                "None",
            ],
        )

        self.add_switch(
            "timer.auto_restart",
            "Auto Restart",
            "Automatically restart the timer after completion.",
        )

        self.add_spacer()

    # ============================================================
    # ACTION BUTTON
    # ============================================================

    def add_action_button(
        self,
        title,
        description,
        callback,
    ):

        button = QPushButton(
            "Open"
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        button.clicked.connect(
            callback
        )

        self.add_card(
            title,
            description,
            button,
        )

    # ============================================================
    # MEMORY ACTIONS
    # ============================================================

    def view_stored_memories(self):
        try:
            from memory import get_memories, get_memory_text
            mems = get_memories()
            if not mems:
                QMessageBox.information(
                    self,
                    "Stored Memories",
                    "No memories currently stored.",
                )
                return

            text = get_memory_text()
            QMessageBox.information(
                self,
                f"Stored Memories ({len(mems)})",
                text or "No memory text.",
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                "Memory Error",
                f"Could not load memories: {error}",
            )

    def clear_all_memories_ui(self):
        confirm = QMessageBox.question(
            self,
            "Clear All Memories",
            "Are you sure you want to delete all stored memories? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                from memory import clear_memories
                clear_memories()
                QMessageBox.information(
                    self,
                    "Memories Cleared",
                    "All stored memories have been cleared.",
                )
            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not clear memories: {error}",
                )

    # ============================================================
    # BACKUP
    # ============================================================

    def create_backup(self):

        try:

            result = create_settings_backup()

            if result:

                QMessageBox.information(
                    self,
                    "Backup Created",
                    "Your settings backup was created successfully.",
                )

            else:

                QMessageBox.warning(
                    self,
                    "Backup Failed",
                    "Could not create a settings backup.",
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Backup Error",
                str(error),
            )

    # ============================================================
    # EXPORT
    # ============================================================

    def export_settings_file(self):

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            "ai_friend_settings.json",
            "JSON Files (*.json)",
        )

        if not file_path:

            return

        try:

            success = export_settings(
                file_path
            )

            if success:

                QMessageBox.information(
                    self,
                    "Export Successful",
                    "Settings were exported successfully.",
                )

            else:

                QMessageBox.warning(
                    self,
                    "Export Failed",
                    "Could not export settings.",
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Export Error",
                str(error),
            )

    # ============================================================
    # IMPORT
    # ============================================================

    def import_settings_file(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Settings",
            "",
            "JSON Files (*.json)",
        )

        if not file_path:

            return

        answer = QMessageBox.question(
            self,
            "Import Settings",
            (
                "Importing settings will replace "
                "your current configuration.\n\n"
                "Continue?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:

            return

        try:

            success = import_settings(
                file_path
            )

            if success:

                QMessageBox.information(
                    self,
                    "Import Successful",
                    (
                        "Settings imported successfully.\n\n"
                        "The settings page will now refresh."
                    ),
                )

                self.change_category(
                    self.category_list.currentRow()
                )

            else:

                QMessageBox.warning(
                    self,
                    "Import Failed",
                    "Could not import the selected settings file.",
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Import Error",
                str(error),
            )

    # ============================================================
    # RESTORE BACKUP
    # ============================================================

    def restore_backup_file(
        self,
        path,
    ):

        answer = QMessageBox.question(
            self,
            "Restore Backup",
            (
                "Restore this backup?\n\n"
                "Your current settings will be backed up first."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:

            return

        try:

            success = restore_backup(
                path
            )

            if success:

                QMessageBox.information(
                    self,
                    "Backup Restored",
                    "Settings restored successfully.",
                )

                self.change_category(
                    self.category_list.currentRow()
                )

            else:

                QMessageBox.warning(
                    self,
                    "Restore Failed",
                    "Could not restore this settings backup.",
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Restore Error",
                str(error),
            )

    # ============================================================
    # RESET ALL
    # ============================================================

    def reset_everything(self):

        answer = QMessageBox.warning(
            self,
            "Reset Everything",
            (
                "This will reset ALL AI Friend settings "
                "to their factory defaults.\n\n"
                "A backup will be created first.\n\n"
                "Are you sure?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:

            return

        try:

            success = reset_all_settings(
                create_backup=True
            )

            if success:

                QMessageBox.information(
                    self,
                    "Settings Reset",
                    (
                        "All settings were restored "
                        "to factory defaults."
                    ),
                )

                self.change_category(
                    self.category_list.currentRow()
                )

            else:

                QMessageBox.warning(
                    self,
                    "Reset Failed",
                    "Could not reset settings.",
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Reset Error",
                str(error),
            )


    # ============================================================
    # GMAIL CONNECTION
    # ============================================================

    def connect_gmail_account(self):
        """
        Open Gmail OAuth flow to connect a new Gmail account.
        Shows a message box with the result.
        """
        try:
            # First ensure Gmail integration is enabled
            set_setting("gmail.enabled", True)

            result = add_gmail_account()

            if isinstance(result, dict) and "error" in result:
                QMessageBox.warning(
                    self,
                    "Gmail Connection",
                    f"Could not connect Gmail: {result['error']}",
                )
                return

            if isinstance(result, dict) and "email" in result:
                QMessageBox.information(
                    self,
                    "Gmail Connected",
                    f"Gmail account connected successfully:\n\n{result['email']}\n\nYou can now use email features.",
                )
                # Refresh the settings page to show updated state
                self.change_category(
                    self.category_list.currentRow()
                )
                return

            QMessageBox.information(
                self,
                "Gmail Connected",
                "Gmail account connected successfully!",
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Gmail Connection Error",
                f"Could not connect Gmail:\n\n{error}",
            )


# ================================================================
# TEST MODE
# ================================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = SettingsPage()

    window.show()

    sys.exit(
        app.exec()
    )


# Backward compatibility alias
SettingsWindow = SettingsPage
