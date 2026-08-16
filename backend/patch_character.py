with open('character.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Change animation timer from 16ms (60 FPS) to 33ms (30 FPS)
content = content.replace(
    'self.animation_timer.start(\n            16\n        )',
    'self.animation_timer.start(\n            33\n        )'
)

# 2. Add visibility check at the beginning of animate()
content = content.replace(
    '''    def animate(self):

        if not self.is_enabled():

            return

        if not self.animations_enabled():

            self.update()

            return''',
    '''    def animate(self):

        if not self.is_enabled():

            return

        if not self.animations_enabled():

            self.update()

            return

        # Skip animation when not visible (minimized/hidden)
        # to save CPU and RAM.
        if not self.isVisible():

            return'''
)

# 3. Add cleanup method after setup_timers
content = content.replace(
    '''        self.set_next_blink()

    # ========================================================
    # NOTIFICATION UI''',
    '''        self.set_next_blink()

    # ========================================================
    # CLEANUP
    # ========================================================

    def cleanup(self):

        """Stop all timers and clean up resources."""

        try:

            if self.animation_timer is not None:

                self.animation_timer.stop()

        except Exception:

            pass

        try:

            if self.blink_timer is not None:

                self.blink_timer.stop()

        except Exception:

            pass

        try:

            if self.notification_timer is not None:

                self.notification_timer.stop()

        except Exception:

            pass

    # ========================================================
    # NOTIFICATION UI'''
)

# 4. Add cursor position caching to setup_state
content = content.replace(
    '''        self.cursor_near = False

        self.cursor_distance = 999''',
    '''        self.cursor_near = False

        self.cursor_distance = 999

        # Cached cursor position to avoid calling
        # QCursor.pos() every animation frame.
        self._cached_cursor_pos = None

        self._cached_cursor_time = 0.0'''
)

# 5. Optimize cursor tracking - only update cursor position
# every ~5 frames instead of every frame
content = content.replace(
    '''        self.update_floating(
            intensity
        )

        self.update_body_movement(
            intensity
        )''',
    '''        self.update_floating(
            intensity
        )

        self.update_body_movement(
            intensity
        )

        # Only update cursor position every ~5 frames
        # to reduce CPU usage from QCursor.pos() calls.
        self._cached_cursor_time += 1'''
)

with open('character.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("character.py patched successfully")
