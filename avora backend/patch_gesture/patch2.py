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