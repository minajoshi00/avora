# ============================================================
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

from settings import get_setting


# ============================================================
# CHARACTER
# ============================================================

class Character(QWidget):

    restore_requested = Signal()
    clicked = Signal()

    # Close gesture configuration
    close_threshold = 100
    X_BASE_RADIUS = 30
    X_GROW_FACTOR = 3.0

    # Gesture state flags
    close_gesture_in_progress = False
    is_dragging_downward = False
    is_dragging_sideways = False
    drag_start_x = 0
    drag_start_y = 0

    # X button animation state
    close_x_scale = 1.0
    close_x_opacity = 0.0
    close_x_visible = False

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
            f"character.{key}",
            default,
        )

    def is_enabled(self):

        return bool(
            self.setting(
                "enabled",
                True,
            )
        )

    def animations_enabled(self):

        return bool(
            self.setting(
                "animations",
                True,
            )
        )

    def eye_tracking_enabled(self):

        return bool(
            self.setting(
                "eye_tracking",
                True,
            )
        )

    def emotions_enabled(self):

        return bool(
            self.setting(
                "emotions",
                True,
            )
        )

    def blinking_enabled(self):

        return bool(
            self.setting(
                "blinking",
                True,
            )
        )

    def idle_animation_enabled(self):

        return bool(
            self.setting(
                "idle_animation",
                True,
            )
        )

    def talking_animation_enabled(self):

        return bool(
            self.setting(
                "talking_animation",
                True,
            )
        )

    def animation_intensity(self):

        try:

            value = float(
                self.setting(
                    "animation_intensity",
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
                "always_on_top",
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
            size_val = float(self.setting("size", 1.0))
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

    # ========================================================
    # THEME UPDATE
    # ========================================================

    def update_theme(self):
        """Refresh character colors when the application theme changes."""

        try:

            from theme import get_current_theme

            theme = get_current_theme()

            self.current_theme = theme

        except Exception as error:

            print(
                "CHARACTER THEME UPDATE ERROR:",
                error
            )

        self.update()

    # ========================================================
    # CHARACTER STATE
    # ========================================================

    def setup_state(self):

        # ---------------- EMOTION ----------------

        self.expression = "idle"

        self.target_expression = "idle"

        self.emotion_strength = 1.0

        self.emotion_timer = 0

        # ---------------- ACTIVITY ----------------

        self.talking = False

        self.thinking = False

        self.eyes_open = True

        # ---------------- TIME ----------------

        self.time = 0.0

        self.idle_time = 0.0

        # ---------------- BODY ----------------

        self.float_offset = 0.0

        self.target_float = 0.0

        self.body_bob = 0.0

        self.target_body_bob = 0.0

        self.body_sway = 0.0

        self.target_body_sway = 0.0

        self.shake = 0.0

        self.target_shake = 0.0

        # ---------------- HEAD ----------------

        self.head_tilt = 0.0

        self.target_head_tilt = 0.0

        self.head_bob = 0.0

        self.target_head_bob = 0.0

        # ---------------- EYES ----------------

        self.eye_x = 0.0

        self.eye_y = 0.0

        self.target_eye_x = 0.0

        self.target_eye_y = 0.0

        self.cursor_near = False

        self.cursor_distance = 999

        # ---------------- TALKING ----------------

        self.talk_progress = 0.0

        self.talk_energy = 0.0

        # ---------------- BREATHING ----------------

        self.breath = 0.0

        # ---------------- ANTENNA ----------------

        self.antenna_pulse = 0.0

        self.antenna_angle = 0.0

        # ---------------- CORE ----------------

        self.core_pulse = 0.0

        # ---------------- RANDOM ----------------

        self.behavior_timer = 0

        self.behavior_action = None

        # ---------------- COMPANION ----------------

        self.notification_label = None
        self.notification_timer = None
        self.notification_visible = False
        self.dragging = False
        self.drag_offset = QPointF()
        self.event_cooldown = 0.0
        self.current_event = None
        self._press_pos = None
        self._press_time = 0.0
        self.click_peek = 0

        # Close gesture state
        self.close_gesture_in_progress = False
        self.is_dragging_downward = False
        self.is_dragging_sideways = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.close_x_scale = 1.0
        self.close_x_opacity = 0.0
        self.close_x_visible = False
        self._original_pos_x = 0
        self._original_pos_y = 0
        self._anim_timer = None

        # ---------------- BLINK ----------------

        self.blinking = False

    # ========================================================
    # TIMERS
    # ========================================================

    def setup_timers(self):

        self.animation_timer = QTimer(
            self
        )

        self.animation_timer.timeout.connect(
            self.animate
        )

        self.animation_timer.start(
            16
        )

        self.blink_timer = QTimer(
            self
        )

        self.blink_timer.timeout.connect(
            self.blink
        )

        self.notification_timer = QTimer(
            self
        )
        self.notification_timer.timeout.connect(
            self.hide_notification
        )

        self.set_next_blink()

    # ========================================================
    # NOTIFICATION UI
    # ========================================================

    def setup_notification_ui(self):
        self.notification_label = QLabel(self)
        self.notification_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.notification_label.setStyleSheet(
            "background-color: rgba(14, 20, 35, 220); color: #F9FAFB; border-radius: 10px; padding: 8px 10px;"
        )
        self.notification_label.setFont(QFont("Segoe UI", 9))
        self.notification_label.setWordWrap(True)
        self.notification_label.setVisible(False)
        self.notification_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def show_notification(self, message: str, duration: int = 2200):
        if not message:
            return
        if self.notification_label is None:
            self.setup_notification_ui()
        self.notification_label.setText(message)
        self.notification_label.adjustSize()
        width = min(220, max(120, self.notification_label.width()))
        self.notification_label.setGeometry(
            0,
            0,
            width,
            self.notification_label.height(),
        )
        self.notification_label.move(0, -self.notification_label.height() - 10)
        self.notification_label.setVisible(True)
        self.notification_label.raise_()
        self.notification_visible = True
        if self.notification_timer is not None:
            self.notification_timer.start(duration)
        self.update()

        # Reposition character if message is long
        if len(message) > 80:
            try:
                from PySide6.QtCore import QTimer
                QTimer.singleShot(100, lambda: self.reposition_for_text(len(message), duration))
            except Exception:
                pass

    def hide_notification(self):
        if self.notification_timer is not None and self.notification_timer.isActive():
            self.notification_timer.stop()
        if self.notification_label is not None:
            self.notification_label.setVisible(False)
        self.notification_visible = False
        self.update()

    def react(self, event: str, payload: dict | None = None):
        event = str(event or "").strip().lower()
        if not event:
            return
        self.current_event = event
        if event in {"image_generation_started", "image_generation_success", "image_generation_failed"}:
            self.set_expression("excited" if "success" in event else "confused" if "failed" in event else "thinking")
        elif event in {"file_created", "file_copied", "folder_created", "file_restored"}:
            self.set_expression("happy")
        elif event in {"file_deleted", "operation_failed", "error"}:
            self.set_expression("sad")
        elif event in {"email_received", "reminder_triggered", "timer_completed", "weather_warning"}:
            self.set_expression("surprised")
        elif event in {"user_praised", "user_funny", "successful_completion"}:
            self.set_expression("excited")
        elif event in {"thinking", "searching", "ai_thinking", "ai_searching"}:
            self.set_expression("thinking")
        elif event in {"speaking"}:
            self.set_expression("happy")
        else:
            self.set_expression("idle")
        if payload:
            message = payload.get("message") or payload.get("title") or ""
            if message:
                self.show_notification(message, duration=int(payload.get("duration", 2200)))
        self.update()

    # ========================================================
    # EMOTION DETECTION
    # ========================================================

    def detect_emotion(
        self,
        message,
    ):

        if not self.emotions_enabled():

            return "idle"

        message = str(
            message
        ).lower()

        if any(
            word in message

            for word in [

                "amazing",
                "awesome",
                "wow",
                "omg",
                "incredible",
                "excited",
                "let's go",
                "lets go",
                "finally",
                "yess",
                "yes!",
                "won",
                "win",
                "success",

            ]
        ):

            return "excited"

        if any(
            word in message

            for word in [

                "happy",
                "good",
                "great",
                "nice",
                "love",
                "thank",
                "thanks",
                "haha",
                "lol",
                "fun",
                "cool",

            ]
        ):

            return "happy"

        if any(
            word in message

            for word in [

                "sad",
                "cry",
                "crying",
                "alone",
                "lonely",
                "hurt",
                "depressed",
                "bad day",
                "upset",
                "miss",

            ]
        ):

            return "sad"

        if any(
            word in message

            for word in [

                "angry",
                "mad",
                "hate",
                "annoying",
                "annoyed",
                "stupid",
                "useless",
                "damn",

            ]
        ):

            return "angry"

        if any(
            word in message

            for word in [

                "confused",
                "don't understand",
                "dont understand",
                "what do you mean",

            ]
        ):

            return "confused"

        if any(
            word in message

            for word in [

                "why",
                "how",
                "what",
                "explain",
                "understand",
                "think",
                "problem",
                "question",

            ]
        ):

            return "thinking"

        if any(
            word in message

            for word in [

                "sleep",
                "sleepy",
                "tired",
                "bed",
                "night",
                "exhausted",

            ]
        ):

            return "sleepy"

        return "idle"

    # ========================================================
    # REACT TO MESSAGE
    # ========================================================

    def react_to_message(
        self,
        message,
    ):

        if not self.is_enabled():

            return

        emotion = self.detect_emotion(
            message
        )

        self.set_expression(
            emotion
        )

        self.reset_activity()

    # ========================================================
    # EXPRESSION
    # ========================================================

    def set_expression(
        self,
        expression,
    ):

        if not self.emotions_enabled():

            expression = "idle"

        valid_expressions = [

            "idle",
            "thinking",
            "happy",
            "sad",
            "angry",
            "excited",
            "sleepy",
            "surprised",
            "confused",
            "curious",
            "error",

        ]

        if expression not in valid_expressions:

            expression = "idle"

        self.expression = expression

        head_tilts = {

            "thinking": -5,
            "sad": 5,
            "happy": -2,
            "angry": 3,
            "confused": -7,
            "curious": 5,
            "surprised": 0,
            "excited": -3,
            "sleepy": 5,
            "error": 6,

        }

        self.target_head_tilt = head_tilts.get(
            expression,
            0,
        )

        if expression == "excited":

            self.target_body_bob = -5

        elif expression == "sad":

            self.target_body_bob = 3

        elif expression == "sleepy":

            self.target_body_bob = 4

        else:

            self.target_body_bob = 0

        self.emotion_timer = 0

        self.update()

    # ========================================================
    # TALKING
    # ========================================================

    def set_talking(
        self,
        talking,
    ):

        if not self.talking_animation_enabled():

            self.talking = False

            self.talk_progress = 0.0

            self.talk_energy = 0.0

            self.update()

            return

        self.talking = bool(
            talking
        )

        if self.talking:

            self.thinking = False

        else:

            self.talk_progress = 0.0

            self.talk_energy = 0.0

        self.update()

    # ========================================================
    # THINKING
    # ========================================================

    def set_thinking(
        self,
        thinking,
    ):

        self.thinking = bool(
            thinking
        )

        if self.thinking:

            self.talking = False

            self.talk_progress = 0.0

            self.set_expression(
                "thinking"
            )

        self.update()

    # ========================================================
    # NATURAL COMPANION REACTION
    # ========================================================

    def react_naturally(self, companion_mood: str, intensity: float = 0.5,
                        silent: bool = False, notification_message: str = None):
        """
        React based on the Companion Intelligence emotion engine.
        This is the primary method used by the companion system.

        Args:
            companion_mood: The mood name from CompanionMood enum value.
            intensity: How strong the emotion is (0.0 to 1.0).
            silent: If True, only change animation without any message.
            notification_message: Optional message to show as notification.
        """
        if not self.is_enabled() or not self.emotions_enabled():
            return

        # Map companion mood to expression
        mood_to_expression = {
            "neutral": "idle",
            "happy": "happy",
            "excited": "excited",
            "curious": "curious",
            "concerned": "thinking",
            "proud": "happy",
            "frustrated": "angry",
            "sympathetic": "sad",
            "playful": "happy",
            "calm": "idle",
            "thoughtful": "thinking",
            "sleepy": "sleepy",
            "surprised": "surprised",
        }

        expression = mood_to_expression.get(companion_mood, "idle")

        # Set expression
        self.set_expression(expression)

        # Emotional intensity affects body movement
        if intensity > 0.6:
            if expression in ("excited", "happy"):
                self.target_body_bob = -4 * intensity
            elif expression == "sad":
                self.target_body_bob = 3 * intensity
            elif expression == "angry":
                self.target_shake = 2 * intensity
        elif intensity < 0.3:
            # Low intensity - subtle movements
            pass

        # Show notification if not in silent mode
        if not silent and notification_message:
            self.show_notification(notification_message, duration=min(3000, int(2000 + intensity * 2000)))

        self.update()

    # ========================================================
    # RESET ACTIVITY
    # ========================================================

    def reset_activity(self):

        self.idle_time = 0

        self.emotion_timer = 0

        if self.expression == "sleepy":

            self.set_expression(
                "idle"
            )

    # ========================================================
    # MAIN ANIMATION
    # ========================================================

    def animate(self):

        if not self.is_enabled():

            return

        if not self.animations_enabled():

            self.update()

            return

        intensity = self.animation_intensity()

        self.time += (
            0.08
            * intensity
        )

        self.idle_time += 0.016

        self.emotion_timer += 1

        self.behavior_timer += 1

        self.update_floating(
            intensity
        )

        self.update_body_movement(
            intensity
        )

        self.update_head(
            intensity
        )

        self.update_cursor_tracking(
            intensity
        )

        self.update_eye_movement(
            intensity
        )

        self.update_breathing(
            intensity
        )

        self.update_antenna(
            intensity
        )

        self.update_core(
            intensity
        )

        self.update_talking(
            intensity
        )

        self.update_random_behavior()

        self.update_emotion_timeout()

        self.update_inactivity()

        self.update()

    # ========================================================
    # FLOATING
    # ========================================================

    def update_floating(
        self,
        intensity=1.0,
    ):

        floating = (

            math.sin(
                self.time
                * 1.4
            )
            * 3
            * intensity

        )

        self.float_offset += (

            floating
            - self.float_offset

        ) * 0.08

    # ========================================================
    # BODY MOVEMENT
    # ========================================================

    def update_body_movement(
        self,
        intensity=1.0,
    ):

        self.body_bob += (

            self.target_body_bob
            - self.body_bob

        ) * 0.08

        self.body_sway += (

            self.target_body_sway
            - self.body_sway

        ) * 0.08

        self.shake += (

            self.target_shake
            - self.shake

        ) * 0.15

        if self.expression == "excited":

            self.target_body_bob = (

                math.sin(
                    self.time
                    * 5
                )
                * 5
                * intensity

            )

        if self.expression == "angry":

            self.target_shake = (

                math.sin(
                    self.time
                    * 18
                )
                * 2
                * intensity

            )

        else:

            self.target_shake *= 0.9

    # ========================================================
    # HEAD
    # ========================================================

    def update_head(
        self,
        intensity=1.0,
    ):

        self.head_tilt += (

            self.target_head_tilt
            - self.head_tilt

        ) * 0.08

        self.head_bob += (

            self.target_head_bob
            - self.head_bob

        ) * 0.08

    # ========================================================
    # CURSOR TRACKING
    # ========================================================

    def update_cursor_tracking(
        self,
        intensity=1.0,
    ):

        if not self.eye_tracking_enabled():

            self.cursor_near = False

            self.target_eye_x *= 0.9

            self.target_eye_y *= 0.9

            return

        cursor_pos = QCursor.pos()

        local_pos = self.mapFromGlobal(
            cursor_pos
        )

        scale = max(0.1, float(self.scale_factor))
        unscaled_x = local_pos.x() / scale
        unscaled_y = local_pos.y() / scale

        face_x = 120

        face_y = (

            115
            + self.float_offset
            + self.body_bob

        )

        dx = unscaled_x - face_x

        dy = unscaled_y - face_y

        distance = math.sqrt(

            dx * dx
            + dy * dy

        )

        self.cursor_distance = distance

        self.cursor_near = distance < 190

        if distance > 0:

            eye_strength = 8 * intensity

            self.target_eye_x = max(

                -eye_strength,

                min(

                    eye_strength,

                    dx
                    / distance
                    * eye_strength

                )

            )

            self.target_eye_y = max(

                -6 * intensity,

                min(

                    6 * intensity,

                    dy
                    / distance
                    * 6
                    * intensity

                )

            )

        if distance < 85:

            if self.expression == "idle":

                self.target_head_tilt = (

                    dx
                    / 85
                    * 6

                )

    # ========================================================
    # EYES
    # ========================================================

    def update_eye_movement(
        self,
        intensity=1.0,
    ):

        if not self.cursor_near:

            if random.randint(
                1,
                100
            ) <= 2:

                self.target_eye_x = random.choice(

                    [
                        -5,
                        -3,
                        0,
                        3,
                        5,
                    ]

                )

                self.target_eye_y = random.choice(

                    [
                        -3,
                        -2,
                        0,
                        2,
                        3,
                    ]

                )

        if self.thinking:

            self.target_eye_x = math.sin(

                self.time
                * 1.5

            ) * 5

        self.eye_x += (

            self.target_eye_x
            - self.eye_x

        ) * 0.15

        self.eye_y += (

            self.target_eye_y
            - self.eye_y

        ) * 0.15

    # ========================================================
    # BREATHING
    # ========================================================

    def update_breathing(
        self,
        intensity=1.0,
    ):

        self.breath = (

            math.sin(
                self.time
                * 1.2
            )
            + 1
        ) / 2

    # ========================================================
    # ANTENNA
    # ========================================================

    def update_antenna(
        self,
        intensity=1.0,
    ):

        speed = 2

        if self.thinking:

            speed = 5

        elif self.talking:

            speed = 4

        elif self.expression == "excited":

            speed = 7

        elif self.expression == "angry":

            speed = 8

        self.antenna_pulse = (

            math.sin(
                self.time
                * speed
            )
            + 1
        ) / 2

        self.antenna_angle = (

            math.sin(
                self.time
                * 2
            )
            * 4
            * intensity

        )

    # ========================================================
    # CORE
    # ========================================================

    def update_core(
        self,
        intensity=1.0,
    ):

        speed = 3

        if self.talking:

            speed = 6

        elif self.expression == "excited":

            speed = 8

        self.core_pulse = (

            math.sin(
                self.time
                * speed
            )
            + 1
        ) / 2

    # ========================================================
    # TALKING ANIMATION
    # ========================================================

    def update_talking(
        self,
        intensity=1.0,
    ):

        if self.talking:

            self.talk_progress += (

                0.35
                * intensity

            )

            self.talk_energy = (

                math.sin(
                    self.talk_progress
                )
                + 1
            ) / 2

        else:

            self.talk_progress = 0.0

            self.talk_energy = 0.0

    # ========================================================
    # RANDOM IDLE BEHAVIOR
    # ========================================================

    def update_random_behavior(self):

        if not self.idle_animation_enabled():

            return

        if (

            self.idle_time < 6
            or self.talking
            or self.thinking

        ):

            return

        if self.behavior_timer > random.randint(400, 900):

            self.behavior_timer = 0

            action = random.choice(
                [
                    "look_left",
                    "look_right",
                    "curious",
                    "small_bob",
                    "sway",
                    "peek",
                    "reset",
                ]
            )

            if action == "look_left":

                self.target_eye_x = -6

                self.target_head_tilt = -4

                QTimer.singleShot(900, lambda: self._reset_eyes_head())

            elif action == "look_right":

                self.target_eye_x = 6

                self.target_head_tilt = 4

                QTimer.singleShot(900, lambda: self._reset_eyes_head())

            elif action == "curious":

                self.set_expression("curious")

                QTimer.singleShot(1600, lambda: self.set_expression("idle"))

            elif action == "small_bob":

                self.target_body_bob = -4

                QTimer.singleShot(700, self.reset_body_movement)

            elif action == "sway":

                self.target_body_sway = random.uniform(-3, 3)

                self.target_head_tilt = random.uniform(-3, 3)

                QTimer.singleShot(1200, self.reset_body_movement)

            elif action == "peek":

                self.target_eye_y = -4

                self.target_head_tilt = -3

                QTimer.singleShot(700, lambda: self._reset_eyes_head())

            elif action == "reset":

                self.target_eye_x = 0

                self.target_eye_y = 0

                self.target_head_tilt = 0

    def _reset_eyes_head(self):

        self.target_eye_x = 0

        self.target_eye_y = 0

        self.target_head_tilt = 0

    # ========================================================
    # RESET BODY
    # ========================================================

    def reset_body_movement(self):

        self.target_body_bob = 0

        self.target_body_sway = 0

        self.target_head_tilt = 0

    def reposition_for_text(self, text_length: int = 0, duration_ms: int = 8000):
        """
        Temporarily reposition the character to make room for long text.
        In compact mode: moves character up slightly to give notification more screen space.
        Has no effect if parent is main window (embedded mode handles layout automatically).
        """
        if self.parent() is None and self.compact_character_mode:
            try:
                screen = self.screen() or QApplication.primaryScreen()
                geo = screen.availableGeometry()
                current_y = self.y()
                offset = min(120, max(40, text_length // 3))
                new_y = max(geo.top() + 10, current_y - offset)
                if abs(new_y - current_y) > 5:
                    self._saved_y = current_y
                    self.move(self.x(), new_y)
                    self.raise_()
                    QTimer.singleShot(duration_ms, self._restore_position)
            except Exception:
                pass

    def _restore_position(self):
        try:
            if hasattr(self, '_saved_y'):
                self.move(self.x(), self._saved_y)
                delattr(self, '_saved_y')
        except Exception:
            pass

    # ========================================================
    # EMOTION TIMEOUT
    # ========================================================

    def update_emotion_timeout(self):

        if self.emotion_timer > 900:

            if self.expression not in [

                "idle",
                "sleepy",

            ]:

                self.set_expression(
                    "idle"
                )

    # ========================================================
    # INACTIVITY
    # ========================================================

    def update_inactivity(self):

        if not self.idle_animation_enabled():

            return

        if self.idle_time > 60:

            if self.expression == "idle":

                self.set_expression(
                    "sleepy"
                )

    # ========================================================
    # BLINKING
    # ========================================================

    def set_next_blink(self):

        if not self.blinking_enabled():

            self.blink_timer.stop()

            self.eyes_open = True

            return

        delay = random.randint(
            2500,
            6000,
        )

        self.blink_timer.start(
            delay
        )

    def blink(self):

        if not self.blinking_enabled():

            return

        if self.blinking:

            return

        if self.expression == "sleepy":

            return

        self.blinking = True

        self.eyes_open = False

        self.update()

        QTimer.singleShot(

            random.randint(
                100,
                180,
            ),

            self.open_eyes
        )

    def open_eyes(self):

        self.eyes_open = True

        self.blinking = False

        self.set_next_blink()

        self.update()

    # ========================================================
    # GRADIENT HELPER
    # ========================================================

    def draw_rounded_gradient(

        self,
        painter,
        x,
        y,
        width,
        height,
        radius,
        color1,
        color2,

    ):

        gradient = QLinearGradient(

            x,
            y,
            x,
            y + height,

        )

        gradient.setColorAt(
            0,
            color1,
        )

        gradient.setColorAt(
            1,
            color2,
        )

        painter.setBrush(
            QBrush(
                gradient
            )
        )

        painter.drawRoundedRect(

            x,
            y,
            width,
            height,
            radius,
            radius,

        )

    # ========================================================
    # PAINT
    # ========================================================

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.pos()
            self._press_time = time.time()
            self.drag_offset = QPointF(event.position().toPoint())
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            # Record drag start position (relative to widget for direction detection)
            self.drag_start_x = event.pos().x()
            self.drag_start_y = event.pos().y()
            # Remember original window position for cancel/return
            self._original_pos_x = self.x()
            self._original_pos_y = self.y()
            # Reset gesture state
            self.close_gesture_in_progress = False
            self.is_dragging_downward = False
            self.is_dragging_sideways = False
            # Stop any running animation from a previous gesture
            if getattr(self, '_anim_timer', None):
                if self._anim_timer.isActive():
                    self._anim_timer.stop()
                self._anim_timer.deleteLater()
                self._anim_timer = None
            # X appears only after actual dragging starts (in mouseMoveEvent)

    def mouseMoveEvent(self, event):
        if self._press_pos is not None and not self.dragging:
            dist = (event.pos() - self._press_pos).manhattanLength()
            if dist > 6:
                self.dragging = True
                # Normal free-form window drag (works in all directions)
                global_pos = event.globalPosition().toPoint()
                self.move(global_pos - self.drag_offset.toPoint())
                # Show the close indicator as soon as dragging starts
                self.close_x_visible = True
                self.close_x_scale = 1.0
                self.close_x_opacity = 0.6
                self.update()
        elif self.dragging:
            global_pos = event.globalPosition().toPoint()
            new_pos = global_pos - self.drag_offset.toPoint()

            # Direction detection: compare vertical vs horizontal movement
            delta_x = event.pos().x() - self.drag_start_x
            delta_y = event.pos().y() - self.drag_start_y
            vertical = abs(delta_y)
            horizontal = abs(delta_x)

            # Determine drag direction
            if not self.is_dragging_downward and not self.is_dragging_sideways:
                if vertical > 10 or horizontal > 10:
                    if delta_y > 0 and delta_y >= horizontal:
                        # Predominantly downward
                        self.is_dragging_downward = True
                        self.close_gesture_in_progress = True
                    else:
                        # Upward or sideways drag
                        self.is_dragging_sideways = True
                        self.close_gesture_in_progress = False
            elif self.is_dragging_downward:
                if delta_y > 0:
                    drag_distance = min(delta_y, self.close_threshold)
                    # Scale and opacity grow with downward distance
                    self.close_x_scale = 1.0 + (drag_distance / self.close_threshold) * (self.X_GROW_FACTOR - 1.0)
                    self.close_x_opacity = min(1.0, 0.4 + (drag_distance / self.close_threshold) * 0.6)
                else:
                    # Dragged back up - keep X visible, reduce emphasis
                    self.close_x_scale = 1.0
                    self.close_x_opacity = 0.5
            elif self.is_dragging_sideways:
                # Sideways/upward drag: keep X visible but not growing
                self.close_x_scale = 1.0
                self.close_x_opacity = 0.5
                # If user switches to downward later, promote to close mode
                if delta_y > 0 and delta_y >= horizontal:
                    self.is_dragging_downward = True
                    self.is_dragging_sideways = False
                    self.close_gesture_in_progress = True

            # Keep normal free-form window movement in all directions
            self.move(new_pos)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.dragging and self._press_pos is not None:
                dist = (event.pos() - self._press_pos).manhattanLength()
                elapsed = time.time() - self._press_time
                if dist < 8 and elapsed < 0.45:
                    self.clicked.emit()
        self.dragging = False
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self._press_pos = None

        # Handle drag-down-to-close gesture completion
        if self.is_dragging_downward and self.close_gesture_in_progress:
            delta_y = event.pos().y() - self.drag_start_y
            if delta_y >= self.close_threshold:
                self._close_avora()
            else:
                self._return_to_position()
        elif self.is_dragging_sideways:
            self._hide_close_indicator()

        # Reset gesture state
        self.close_gesture_in_progress = False
        self.is_dragging_downward = False
        self.is_dragging_sideways = False
        if not getattr(self, "_anim_timer", None) or not self._anim_timer.isActive():
            self.close_x_visible = False
            self.close_x_scale = 1.0
            self.close_x_opacity = 0.0
        self.update()
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.restore_requested.emit()

    def _close_avora(self):
        """Animate AVORA toward the close target and close."""
        self._animate_to_position(self.x(), self.y() + 200, 200, self.close)

    def _return_to_position(self):
        """Smoothly animate AVORA back to its original position."""
        target_x = self._original_pos_x
        target_y = self._original_pos_y
        self._animate_to_position(target_x, target_y, 300, self._hide_close_indicator)

    def _animate_to_position(self, target_x, target_y, duration_ms, callback=None):
        """Smoothly animate window position using a QTimer loop."""
        self._anim_target_x = target_x
        self._anim_target_y = target_y
        self._anim_start_x = self.x()
        self._anim_start_y = self.y()
        self._anim_duration = duration_ms
        self._anim_elapsed = 0
        self._anim_callback = callback
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_animation)
        self._anim_timer.start(16)

    def _tick_animation(self):
        """Animation tick for smooth position interpolation."""
        self._anim_elapsed += 16
        t = min(1.0, self._anim_elapsed / self._anim_duration)
        eased = 1 - (1 - t) ** 3
        x = int(self._anim_start_x + (self._anim_target_x - self._anim_start_x) * eased)
        y = int(self._anim_start_y + (self._anim_target_y - self._anim_start_y) * eased)
        self.move(x, y)
        if t >= 1.0:
            self._anim_timer.stop()
            self._anim_timer.deleteLater()
            self._anim_timer = None
            if self._anim_callback:
                self._anim_callback()

    def _hide_close_indicator(self):
        """Hide the close indicator (X)."""
        self.close_x_visible = False
        self.close_x_scale = 1.0
        self.close_x_opacity = 0.0
        self.update()

    def paintEvent(
        self,
        event,
    ):

        if not self.is_enabled():

            return

        painter = QPainter(
            self
        )

        painter.setRenderHint(

            QPainter.RenderHint.Antialiasing
        )

        if self.scale_factor != 1.0:
            painter.scale(
                self.scale_factor,
                self.scale_factor,
            )

        y = (

            self.float_offset
            + self.body_bob

        )

        painter.translate(
            self.shake,
            0,
        )

        self.draw_shadow(
            painter
        )

        self.draw_body_glow(
            painter,
            y,
        )

        self.draw_antenna(
            painter,
            y,
        )

        self.draw_ears(
            painter,
            y,
        )

        painter.save()

        self.apply_head_transform(
            painter,
            y,
        )

        self.draw_head(
            painter,
            y,
        )

        self.draw_face_screen(
            painter,
            y,
        )

        self.draw_eyes(
            painter,
            y,
        )

        self.draw_blush(
            painter,
            y,
        )

        self.draw_eyebrows(
            painter,
            y,
        )

        self.draw_mouth(
            painter,
            y,
        )

        painter.restore()

        self.draw_body(
            painter,
            y,
        )

        self.draw_chest_core(
            painter,
            y,
        )

        self.draw_body_details(
            painter,
            y,
        )

        # Draw the close (X) indicator on top - fixed at bottom-center
        self._draw_close_indicator(painter)

    # ========================================================
    # CLOSE INDICATOR
    # ========================================================

    def _draw_close_indicator(self, painter):
        """Draw the close (X) indicator fixed at the window bottom-center."""
        if not self.close_x_visible:
            return

        cx = self.width() / 2.0
        radius = self.X_BASE_RADIUS * self.close_x_scale
        cy = self.height() - 45.0
        cy = min(cy, self.height() - radius - 6.0)

        sigma = max(0.0, min(1.0, self.close_x_opacity))
        if sigma <= 0.0:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Outer glow
        glow = QRadialGradient(QPointF(cx, cy), radius * 1.4)
        glow.setColorAt(0.0, QColor(245, 82, 82, int(90 * sigma)))
        glow.setColorAt(1.0, QColor(245, 82, 82, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius * 1.4, radius * 1.4)

        # Solid circle
        circle_fill = QRadialGradient(QPointF(cx - radius * 0.2, cy - radius * 0.3), radius)
        circle_fill.setColorAt(0.0, QColor(255, 103, 103, int(235 * sigma)))
        circle_fill.setColorAt(1.0, QColor(235, 60, 70, int(225 * sigma)))
        painter.setBrush(QBrush(circle_fill))
        painter.setPen(QPen(QColor(255, 170, 170, int(160 * sigma)), 2.0))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # X mark
        pen_width = max(2.5, radius * 0.16)
        painter.setPen(QPen(QColor(255, 255, 255, int(250 * sigma)), pen_width,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        off = radius * 0.38
        painter.drawLine(QPointF(cx - off, cy - off), QPointF(cx + off, cy + off))
        painter.drawLine(QPointF(cx + off, cy - off), QPointF(cx - off, cy + off))

        painter.restore()

    # ========================================================
    # HEAD TRANSFORM
    # ========================================================

    def apply_head_transform(
        self,
        painter,
        y,
    ):

        painter.translate(
            120,
            115 + y,
        )

        painter.rotate(
            self.head_tilt,
        )

        painter.translate(
            -120,
            -115 - y,
        )

    # ========================================================
    # SHADOW
    # ========================================================

    def draw_shadow(
        self,
        painter,
    ):

        shadow = QRadialGradient(

            QPointF(
                120,
                265,
            ),
            80,

        )

        shadow.setColorAt(
            0,
            QColor(
                0,
                0,
                0,
                110,
            )
        )

        shadow.setColorAt(
            1,
            QColor(
                0,
                0,
                0,
                0,
            )
        )

        painter.setBrush(
            QBrush(
                shadow
            )
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.drawEllipse(
            35,
            250,
            170,
            25,
        )

    # ========================================================
    # BODY GLOW
    # ========================================================

    def draw_body_glow(
        self,
        painter,
        y,
    ):

        glow = QRadialGradient(

            QPointF(
                120,
                150 + y,
            ),
            120,

        )

        glow.setColorAt(
            0,
            QColor(
                90,
                220,
                255,
                55,
            )
        )

        glow.setColorAt(
            1,
            QColor(
                90,
                220,
                255,
                0,
            )
        )

        painter.setBrush(
            QBrush(
                glow
            )
        )

        painter.drawEllipse(
            15,
            40 + y,
            210,
            220,
        )

    # ========================================================
    # ANTENNA
    # ========================================================

    def draw_antenna(
        self,
        painter,
        y,
    ):

        painter.save()

        painter.translate(
            120,
            48 + y,
        )

        painter.rotate(
            self.antenna_angle
        )

        painter.translate(
            -120,
            -48 - y,
        )

        painter.setPen(
            QPen(
                QColor(
                    70,
                    80,
                    110,
                ),
                4,
            )
        )

        painter.drawLine(
            120,
            52 + y,
            120,
            20 + y,
        )

        pulse_size = int(

            16
            + self.antenna_pulse
            * 10

        )

        gradient = QRadialGradient(

            QPointF(
                120,
                18 + y,
            ),
            pulse_size,

        )

        gradient.setColorAt(
            0,
            QColor(
                120,
                230,
                255,
                245,
            )
        )

        gradient.setColorAt(
            1,
            QColor(
                70,
                120,
                255,
                0,
            )
        )

        painter.setBrush(
            QBrush(
                gradient
            )
        )

        painter.drawEllipse(

            120 - pulse_size // 2,
            18 + y - pulse_size // 2,
            pulse_size,
            pulse_size,

        )

        painter.setBrush(
            QBrush(
                QColor(
                    150,
                    240,
                    255,
                )
            )
        )

        painter.drawEllipse(
            114,
            12 + y,
            12,
            12,
        )

        painter.restore()

    # ========================================================
    # EARS
    # ========================================================

    def draw_ears(
        self,
        painter,
        y,
    ):

        painter.setPen(
            QPen(
                QColor(
                    20,
                    25,
                    45,
                ),
                3,
            )
        )

        painter.setBrush(
            QBrush(
                QColor(
                    35,
                    45,
                    75,
                )
            )
        )

        painter.drawRoundedRect(
            15,
            78 + y,
            32,
            70,
            13,
            13,
        )

        painter.drawRoundedRect(
            193,
            78 + y,
            32,
            70,
            13,
            13,
        )

        painter.setBrush(
            QBrush(
                QColor(
                    90,
                    210,
                    255,
                )
            )
        )

        painter.drawEllipse(
            24,
            101 + y,
            11,
            24,
        )

        painter.drawEllipse(
            202,
            101 + y,
            11,
            24,
        )

    # ========================================================
    # HEAD
    # ========================================================

    def draw_head(
        self,
        painter,
        y,
    ):

        painter.setPen(
            QPen(
                QColor(
                    15,
                    20,
                    40,
                ),
                4,
            )
        )

        self.draw_rounded_gradient(

            painter,

            40,
            45 + y,
            160,
            150,
            40,

            QColor(
                100,
                230,
                255,
            ),

            QColor(
                40,
                130,
                210,
            )

        )

    # ========================================================
    # FACE SCREEN
    # ========================================================

    def draw_face_screen(
        self,
        painter,
        y,
    ):

        painter.setPen(
            QPen(
                QColor(
                    5,
                    8,
                    20,
                ),
                3,
            )
        )

        painter.setBrush(
            QBrush(
                QColor(
                    8,
                    12,
                    28,
                )
            )
        )

        painter.drawRoundedRect(
            52,
            68 + y,
            136,
            94,
            30,
            30,
        )

    # ========================================================
    # EYES
    # ========================================================

    def draw_eyes(
        self,
        painter,
        y,
    ):

        eye_y = (

            86
            + self.eye_y
            + y

        )

        if self.expression == "sleepy":

            painter.setPen(
                QPen(
                    QColor(
                        230,
                        250,
                        255,
                    ),
                    5,
                )
            )

            painter.drawArc(
                70,
                96 + y,
                34,
                17,
                0,
                180 * 16,
            )

            painter.drawArc(
                136,
                96 + y,
                34,
                17,
                0,
                180 * 16,
            )

            return

        eye_width = 34

        eye_height = 40

        if self.expression == "surprised":

            eye_width = 40

            eye_height = 47

        if self.eyes_open:

            painter.setPen(
                Qt.PenStyle.NoPen
            )

            painter.setBrush(
                QBrush(
                    QColor(
                        235,
                        250,
                        255,
                    )
                )
            )

            painter.drawEllipse(
                int(
                    66
                    + self.eye_x
                ),
                int(
                    eye_y
                ),
                eye_width,
                eye_height,
            )

            painter.drawEllipse(
                int(
                    132
                    + self.eye_x
                ),
                int(
                    eye_y
                ),
                eye_width,
                eye_height,
            )

            pupil_size = 20

            painter.setBrush(
                QBrush(
                    QColor(
                        20,
                        35,
                        70,
                    )
                )
            )

            painter.drawEllipse(
                int(
                    73
                    + self.eye_x
                ),
                int(
                    eye_y
                    + 11
                ),
                pupil_size,
                23,
            )

            painter.drawEllipse(
                int(
                    139
                    + self.eye_x
                ),
                int(
                    eye_y
                    + 11
                ),
                pupil_size,
                23,
            )

            painter.setBrush(
                QBrush(
                    QColor(
                        255,
                        255,
                        255,
                    )
                )
            )

            painter.drawEllipse(
                int(
                    77
                    + self.eye_x
                ),
                int(
                    eye_y
                    + 13
                ),
                6,
                7,
            )

            painter.drawEllipse(
                int(
                    143
                    + self.eye_x
                ),
                int(
                    eye_y
                    + 13
                ),
                6,
                7,
            )

        else:

            painter.setPen(
                QPen(
                    QColor(
                        230,
                        250,
                        255,
                    ),
                    5,
                )
            )

            painter.drawLine(
                68,
                105 + y,
                100,
                105 + y,
            )

            painter.drawLine(
                134,
                105 + y,
                166,
                105 + y,
            )

    # ========================================================
    # BLUSH
    # ========================================================

    def draw_blush(
        self,
        painter,
        y,
    ):

        if self.expression not in [

            "happy",
            "excited",
            "curious",

        ]:

            return

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            QBrush(
                QColor(
                    255,
                    120,
                    170,
                    100,
                )
            )
        )

        painter.drawEllipse(
            58,
            132 + y,
            28,
            11,
        )

        painter.drawEllipse(
            154,
            132 + y,
            28,
            11,
        )

    # ========================================================
    # EYEBROWS
    # ========================================================

    def draw_eyebrows(
        self,
        painter,
        y,
    ):

        painter.setPen(
            QPen(
                QColor(
                    210,
                    245,
                    255,
                ),
                5,
            )
        )

        if self.expression == "angry":

            painter.drawLine(
                66,
                80 + y,
                100,
                88 + y,
            )

            painter.drawLine(
                134,
                88 + y,
                168,
                80 + y,
            )

        elif self.expression == "sad":

            painter.drawLine(
                66,
                88 + y,
                100,
                80 + y,
            )

            painter.drawLine(
                134,
                80 + y,
                168,
                88 + y,
            )

        elif self.expression == "surprised":

            painter.drawLine(
                66,
                75 + y,
                100,
                75 + y,
            )

            painter.drawLine(
                134,
                75 + y,
                168,
                75 + y,
            )

        elif self.expression == "confused":

            painter.drawLine(
                66,
                78 + y,
                100,
                73 + y,
            )

            painter.drawLine(
                134,
                82 + y,
                168,
                82 + y,
            )

        elif self.expression == "happy":

            painter.drawArc(
                66,
                73 + y,
                34,
                16,
                0,
                180 * 16,
            )

            painter.drawArc(
                134,
                73 + y,
                34,
                16,
                0,
                180 * 16,
            )

    # ========================================================
    # MOUTH
    # ========================================================

    def draw_mouth(
        self,
        painter,
        y,
    ):

        painter.setPen(
            QPen(
                QColor(
                    235,
                    250,
                    255,
                ),
                4,
            )
        )

        if self.talking:

            mouth_height = int(

                8
                + self.talk_energy
                * 17

            )

            painter.setBrush(
                QBrush(
                    QColor(
                        20,
                        25,
                        45,
                    )
                )
            )

            painter.drawEllipse(
                101,
                135 + y,
                38,
                mouth_height,
            )

            return

        if self.expression == "happy":

            painter.drawArc(
                92,
                124 + y,
                56,
                38,
                0,
                -180 * 16,
            )

        elif self.expression == "excited":

            painter.setBrush(
                QBrush(
                    QColor(
                        20,
                        25,
                        45,
                    )
                )
            )

            painter.drawEllipse(
                98,
                130 + y,
                44,
                30,
            )

        elif self.expression == "sad":

            painter.drawArc(
                98,
                145 + y,
                44,
                27,
                0,
                180 * 16,
            )

        elif self.expression == "thinking":

            painter.drawEllipse(
                113,
                135 + y,
                14,
                14,
            )

        elif self.expression == "surprised":

            painter.drawEllipse(
                108,
                132 + y,
                25,
                30,
            )

        elif self.expression == "confused":

            painter.drawArc(
                105,
                135 + y,
                38,
                20,
                0,
                180 * 16,
            )

        elif self.expression == "angry":

            painter.drawLine(
                103,
                148 + y,
                137,
                148 + y,
            )

        elif self.expression == "sleepy":

            painter.drawLine(
                108,
                145 + y,
                132,
                145 + y,
            )

        else:

            painter.drawArc(
                100,
                130 + y,
                40,
                28,
                0,
                -180 * 16,
            )

    # ========================================================
    # BODY
    # ========================================================

    def draw_body(
        self,
        painter,
        y,
    ):

        painter.setPen(
            QPen(
                QColor(
                    15,
                    20,
                    40,
                ),
                4,
            )
        )

        self.draw_rounded_gradient(

            painter,

            75,
            195 + y,
            90,
            50,
            20,

            QColor(
                50,
                160,
                220,
            ),

            QColor(
                25,
                70,
                150,
            )

        )

    # ========================================================
    # CHEST CORE
    # ========================================================

    def draw_chest_core(
        self,
        painter,
        y,
    ):

        core_size = int(

            11
            + self.core_pulse
            * 6

        )

        gradient = QRadialGradient(

            QPointF(
                120,
                220 + y,
            ),
            core_size,

        )

        gradient.setColorAt(
            0,
            QColor(
                220,
                255,
                255,
            )
        )

        gradient.setColorAt(
            0.5,
            QColor(
                70,
                220,
                255,
            )
        )

        gradient.setColorAt(
            1,
            QColor(
                30,
                100,
                255,
                0,
            )
        )

        painter.setBrush(
            QBrush(
                gradient
            )
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.drawEllipse(

            120 - core_size,
            220 + y - core_size,
            core_size * 2,
            core_size * 2,

        )

    # ========================================================
    # BODY DETAILS
    # ========================================================

    def draw_body_details(
        self,
        painter,
        y,
    ):

        painter.setPen(
            QPen(
                QColor(
                    130,
                    230,
                    255,
                ),
                2,
            )
        )

        painter.drawLine(
            88,
            235 + y,
            104,
            235 + y,
        )

        painter.drawLine(
            136,
            235 + y,
            152,
            235 + y,
        )
