import sys

PATH = r'c:\Users\HP\OneDrive\Desktop\avora\avora backend\character.py'

with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

report = []

def replace_once(old, new, name):
    global content
    count = content.count(old)
    report.append(f"{name}: count={count}")
    if count == 1:
        content = content.replace(old, new)
        report.append(f"{name}: OK")
    elif count == 0:
        report.append(f"{name}: NOT FOUND")
    else:
        report.append(f"{name}: MULTIPLE ({count})")

# 1. Class-level variables
replace_once(
    """    restore_requested = Signal()
    clicked = Signal()

    # ========================================================
    # INITIALIZATION
    # ========================================================""",
    """    restore_requested = Signal()
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
    # ========================================================""",
    "class_vars",
)

# 2. setup_state instance vars
replace_once(
    """        self.dragging = False
        self.drag_offset = QPointF()
        self.event_cooldown = 0.0
        self.current_event = None
        self._press_pos = None
        self._press_time = 0.0
        self.click_peek = 0""",
    """        self.dragging = False
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
        self._anim_timer = None""",
    "setup_state",
)

# 3. mousePressEvent
replace_once(
    """    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.pos()
            self._press_time = time.time()
            self.drag_offset = QPointF(event.position().toPoint())
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))""",
    """    def mousePressEvent(self, event):
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
            # X appears only after actual dragging starts (in mouseMoveEvent)""",
    "mousePressEvent",
)