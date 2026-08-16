with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\backend\\character.py', 'r') as f:
    content = f.read()

# Add Character class at the beginning
class_def = '''# ============================================================
# character.py
# AI Friend - Advanced Animated Character
# ============================================================

import math
import random
import time

from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtGui import (
    QPainter,
    QBrush,
    QPen,
    QColor,
    QLinearGradient,
    QRadialGradient,
    QCursor,
    QFont,
)
from PySide6.QtCore import (
    Qt,
    QTimer,
    QPointF,
    Signal,
    QRect,
)


# ============================================================
# CHARACTER CLASS
# ============================================================

class Character(QWidget):

    restore_requested = Signal()
    clicked = Signal()

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self, parent=None):

        super().__init__(parent)

        self.scale_factor = 1.0
        self.base_width = 240
        self.base_height = 290

        self.setup_window()
        self.setup_state()
        self.setup_timers()
        self.setup_notification_ui()

    # ========================================================
    # SETTINGS
    # ========================================================

    def setting(
        self,
        key,
        default,
    ):

        return get_setting(
            f\"character.{key}\",
            default,
        )

    def is_enabled(self):

        return bool(
            self.setting(
                \"enabled\",
                True,
            )
        )

    def animations_enabled(self):

        return bool(
            self.setting(
                \"animations\",
                True,
            )
        )

    def eye_tracking_enabled(self):

        return bool(
            self.setting(
                \"eye_tracking\",
                True,
            )
        )

    def emotions_enabled(self):

        return bool(
            self.setting(
                \"emotions\",
                True,
            )
        )

    def blinking_enabled(self):

        return bool(
            self.setting(
                \"blinking\",
                True,
            )
        )

    def idle_animation_enabled(self):

        return bool(
            self.setting(
                \"idle_animation\",
                True,
            )
        )

    def talking_animation_enabled(self):

        return bool(
            self.setting(
                \"talking_animation\",
                True,
            )
        )

    def animation_intensity(self):

        try:

            value = float(
                self.setting(
                    \"animation_intensity\",
                    1.0,
                )
            )

            return max(
                0.1,
                min(
                    2.0,
                    value,
                ),
            )

        except (
            TypeError,
            ValueError,
        ):

            return 1.0

        # ========================================================
        # WINDOW
        # ========================================================

    def setup_window(self):

        self.setFixedSize(
            self.base_width,
            self.base_height,
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setMouseTracking(
            True
        )

        self.setWindowFlag(
            Qt.WindowType.FramelessWindowHint
        )

        self.update_window_settings()

    # ========================================================
    # APPLY SETTINGS
    # ========================================================

    def update_window_settings(self):

        always_on_top = bool(
            self.setting(
                \"always_on_top\",
                False,
            )
        )

        if always_on_top:

            self.setWindowFlag(
                Qt.WindowType.WindowStaysOnTopHint,
                True,
            )

        else:

            self.setWindowFlag(
                Qt.WindowType.WindowStaysOnTopHint,
                False,
            )

        self.update()

    def set_scale_factor(self, factor: float):

        try:
            factor = max(0.3, min(3.0, float(factor)))
        except (TypeError, ValueError):
            factor = 1.0

        if abs(self.scale_factor - factor) < 1e-6:
            return

        self.scale_factor = factor

        scaled_width = max(1, int(self.base_width * factor))
        scaled_height = max(1, int(self.base_height * factor))

        self.setFixedSize(scaled_width, scaled_height)
        self.update()

    def set_character_size(self, size: float):
        self.set_scale_factor(size)

    def refresh_settings(self):

        self.update_window_settings()

        try:
            size_val = float(self.setting(\"size\", 1.0))
            self.set_scale_factor(size_val)
        except Exception:
            pass

        if not self.blinking_enabled():

            self.blink_timer.stop()

            self.eyes_open = True

            self.blinking = False

        else:

            if not self.blink_timer.isActive():

                self.set_next_blink()

        self.update()

        if not self.idle_animation_enabled():

            return

        # Update idle timer based on setting
        idle_setting = get_setting(\"activity_awareness.idle_threshold_minutes\", 3)
        self.idle_idle_threshold = idle_setting * 60 * 1000  # convert to ms

    # ========================================================
    # THEME UPDATE
    # ========================================================

    def update_theme(self):

        \"\"\"Refresh character colors when the application theme changes.\"\"\"

        try:

            from theme import get_current_theme

            theme = get_current_theme()

            self.current_theme = theme

        except Exception as error:

            print(
                \"CHARACTER THEME UPDATE ERROR:\",
                error
            )

        self.update()

    # ========================================================
    # CHARACTER STATE
    # ========================================================

    def setup_state(self):

        # CHARACTER STATE
        self.state = \"idle\"  # idle, thinking, working, success, error, listening, speaking, sleepy

        # CHARACTER EXPRESSION
        self.expression = \"idle\"

        self.target_expression = \"idle\"

        self.emotion_strength = 1.0

        self.emotion_timer = 0

        # ACTIVITY
        self.talking = False

        self.thinking = False

        self.eyes_open = True

        # TIME
        self.time = 0.0

        self.idle_time = 0.0

        # BODY
        self.float_offset = 0.0

        self.target_float = 0.0

        self.body_bob = 0.0

        self.target_body_bob = 0.0

        self.body_sway = 0.0

        self.target_body_sway = 0.0

        self.shake = 0.0

        self.target_shake = 0.0

        # HEAD
        self.head_tilt = 0.0

        self.target_head_tilt = 0.0

        self.head_bob = 0.0

        self.target_head_bob = 0.0

        # EYES
        self.eye_x = 0.0

        self.eye_y = 0.0

        self.target_eye_x = 0.0

        self.target_eye_y = 0.0

        self.cursor_near = False

        self.cursor_distance = 999

        # TALKING
        self.talk_progress = 0.0

        self.talk_energy = 0.0

        # BREATHING
        self.breath = 0.0

        # ANTENNA
        self.antenna_pulse = 0.0

        self.antenna_angle = 0.0

        # CORE
        self.core_pulse = 0.0

        # RANDOM
        self.behavior_timer = 0

        self.behavior_action = None

        # COMPANION
        self.notification_clouds = []
        self.notification_label = None
        self.notification_timer = None
        self.dragging = False
        self.drag_offset = QPointF()
        self.event_cooldown = 0.0
        self.current_event = None
        self._press_pos = None
        self._press_time = 0.0
        self.click_peek = 0

        # BLINK
        self.blinking = False

'''
# Prepend the class definition
new_content = class_def + content

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\character.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Added Character class definition')
"