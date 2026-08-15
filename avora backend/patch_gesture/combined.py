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
# 4. mouseMoveEvent
replace_once(
    """    def mouseMoveEvent(self, event):
        if self._press_pos is not None and not self.dragging:
            dist = (event.pos() - self._press_pos).manhattanLength()
            if dist > 6:
                self.dragging = True
                global_pos = event.globalPosition().toPoint()
                self.move(global_pos - self.drag_offset.toPoint())
        elif self.dragging:
            global_pos = event.globalPosition().toPoint()
            self.move(global_pos - self.drag_offset.toPoint())
        super().mouseMoveEvent(event)""",
    """    def mouseMoveEvent(self, event):
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
        super().mouseMoveEvent(event)""",
    "mouseMoveEvent",
)
# 5. mouseReleaseEvent + helpers
replace_once(
    """    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.dragging and self._press_pos is not None:
                dist = (event.pos() - self._press_pos).manhattanLength()
                elapsed = time.time() - self._press_time
                if dist < 8 and elapsed < 0.45:
                    self.clicked.emit()
        self.dragging = False
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self._press_pos = None
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.restore_requested.emit()""",
    '    def mouseReleaseEvent(self, event):\n'
    '        if event.button() == Qt.MouseButton.LeftButton:\n'
    '            if not self.dragging and self._press_pos is not None:\n'
    '                dist = (event.pos() - self._press_pos).manhattanLength()\n'
    '                elapsed = time.time() - self._press_time\n'
    '                if dist < 8 and elapsed < 0.45:\n'
    '                    self.clicked.emit()\n'
    '        self.dragging = False\n'
    '        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))\n'
    '        self._press_pos = None\n'
    '\n'
    '        # Handle drag-down-to-close gesture completion\n'
    '        if self.is_dragging_downward and self.close_gesture_in_progress:\n'
    '            delta_y = event.pos().y() - self.drag_start_y\n'
    '            if delta_y >= self.close_threshold:\n'
    '                self._close_avora()\n'
    '            else:\n'
    '                self._return_to_position()\n'
    '        elif self.is_dragging_sideways:\n'
    '            self._hide_close_indicator()\n'
    '\n'
    '        # Reset gesture state\n'
    '        self.close_gesture_in_progress = False\n'
    '        self.is_dragging_downward = False\n'
    '        self.is_dragging_sideways = False\n'
    '        if not getattr(self, "_anim_timer", None) or not self._anim_timer.isActive():\n'
    '            self.close_x_visible = False\n'
    '            self.close_x_scale = 1.0\n'
    '            self.close_x_opacity = 0.0\n'
    '        self.update()\n'
    '        super().mouseReleaseEvent(event)\n'
    '        if event.button() == Qt.MouseButton.LeftButton:\n'
    '            self.restore_requested.emit()\n'
    '\n'
    '    def _close_avora(self):\n'
    '        """Animate AVORA toward the close target and close."""\n'
    '        self._animate_to_position(self.x(), self.y() + 200, 200, self.close)\n'
    '\n'
    '    def _return_to_position(self):\n'
    '        """Smoothly animate AVORA back to its original position."""\n'
    '        target_x = self._original_pos_x\n'
    '        target_y = self._original_pos_y\n'
    '        self._animate_to_position(target_x, target_y, 300, self._hide_close_indicator)\n'
    '\n'
    '    def _animate_to_position(self, target_x, target_y, duration_ms, callback=None):\n'
    '        """Smoothly animate window position using a QTimer loop."""\n'
    '        self._anim_target_x = target_x\n'
    '        self._anim_target_y = target_y\n'
    '        self._anim_start_x = self.x()\n'
    '        self._anim_start_y = self.y()\n'
    '        self._anim_duration = duration_ms\n'
    '        self._anim_elapsed = 0\n'
    '        self._anim_callback = callback\n'
    '        self._anim_timer = QTimer(self)\n'
    '        self._anim_timer.timeout.connect(self._tick_animation)\n'
    '        self._anim_timer.start(16)\n'
    '\n'
    '    def _tick_animation(self):\n'
    '        """Animation tick for smooth position interpolation."""\n'
    '        self._anim_elapsed += 16\n'
    '        t = min(1.0, self._anim_elapsed / self._anim_duration)\n'
    '        eased = 1 - (1 - t) ** 3\n'
    '        x = int(self._anim_start_x + (self._anim_target_x - self._anim_start_x) * eased)\n'
    '        y = int(self._anim_start_y + (self._anim_target_y - self._anim_start_y) * eased)\n'
    '        self.move(x, y)\n'
    '        if t >= 1.0:\n'
    '            self._anim_timer.stop()\n'
    '            self._anim_timer.deleteLater()\n'
    '            self._anim_timer = None\n'
    '            if self._anim_callback:\n'
    '                self._anim_callback()\n'
    '\n'
    '    def _hide_close_indicator(self):\n'
    '        """Hide the close indicator (X)."""\n'
    '        self.close_x_visible = False\n'
    '        self.close_x_scale = 1.0\n'
    '        self.close_x_opacity = 0.0\n'
    '        self.update()',
    "mouseReleaseEvent_and_helpers",
)
# 6. paintEvent - add close indicator call at the end
replace_once(
    """        self.draw_body_details(
            painter,
            y,
        )

    # ========================================================
    # HEAD TRANSFORM
    # ========================================================""",
    '        self.draw_body_details(\n'
    '            painter,\n'
    '            y,\n'
    '        )\n'
    '\n'
    '        # Draw the close (X) indicator on top - fixed at bottom-center\n'
    '        self._draw_close_indicator(painter)\n'
    '\n'
    '    # ========================================================\n'
    '    # CLOSE INDICATOR\n'
    '    # ========================================================\n'
    '\n'
    '    def _draw_close_indicator(self, painter):\n'
    '        """Draw the close (X) indicator fixed at the window bottom-center."""\n'
    '        if not self.close_x_visible:\n'
    '            return\n'
    '\n'
    '        cx = self.width() / 2.0\n'
    '        radius = self.X_BASE_RADIUS * self.close_x_scale\n'
    '        cy = self.height() - 45.0\n'
    '        cy = min(cy, self.height() - radius - 6.0)\n'
    '\n'
    '        sigma = max(0.0, min(1.0, self.close_x_opacity))\n'
    '        if sigma <= 0.0:\n'
    '            return\n'
    '\n'
    '        painter.save()\n'
    '        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)\n'
    '\n'
    '        # Outer glow\n'
    '        glow = QRadialGradient(QPointF(cx, cy), radius * 1.4)\n'
    '        glow.setColorAt(0.0, QColor(245, 82, 82, int(90 * sigma)))\n'
    '        glow.setColorAt(1.0, QColor(245, 82, 82, 0))\n'
    '        painter.setBrush(QBrush(glow))\n'
    '        painter.setPen(Qt.PenStyle.NoPen)\n'
    '        painter.drawEllipse(QPointF(cx, cy), radius * 1.4, radius * 1.4)\n'
    '\n'
    '        # Solid circle\n'
    '        circle_fill = QRadialGradient(QPointF(cx - radius * 0.2, cy - radius * 0.3), radius)\n'
    '        circle_fill.setColorAt(0.0, QColor(255, 103, 103, int(235 * sigma)))\n'
    '        circle_fill.setColorAt(1.0, QColor(235, 60, 70, int(225 * sigma)))\n'
    '        painter.setBrush(QBrush(circle_fill))\n'
    '        painter.setPen(QPen(QColor(255, 170, 170, int(160 * sigma)), 2.0))\n'
    '        painter.drawEllipse(QPointF(cx, cy), radius, radius)\n'
    '\n'
    '        # X mark\n'
    '        pen_width = max(2.5, radius * 0.16)\n'
    '        painter.setPen(QPen(QColor(255, 255, 255, int(250 * sigma)), pen_width,\n'
    '                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))\n'
    '        off = radius * 0.38\n'
    '        painter.drawLine(QPointF(cx - off, cy - off), QPointF(cx + off, cy + off))\n'
    '        painter.drawLine(QPointF(cx + off, cy - off), QPointF(cx - off, cy + off))\n'
    '\n'
    '        painter.restore()\n'
    '\n'
    '    # ========================================================\n'
    '    # HEAD TRANSFORM\n'
    '    # ========================================================',
    "paintEvent",
)

# Fix: filter out count entries before validation
status_entries = [r for r in report if 'count=' not in r]

# Write back
if all('OK' in r for r in status_entries):
    with open(PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print("ALL EDITS APPLIED SUCCESSFULLY")
else:
    print("SOME EDITS FAILED:")
    for r in report:
        print("  -", r)
    sys.exit(1)
