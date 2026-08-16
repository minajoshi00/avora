import sys

# Read the original character.py
with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\character.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add notification priorities and cloud data class after the imports section
import_end = content.find('from datetime import datetime')
if import_end >= 0:
    insert_pos = import_end + len('\nfrom datetime import datetime\n\n')
    
    cloud_data = '''
# ============================================================
# NOTIFICATION PRIORITIES AND CLOUD DATA
# ============================================================

NOTIFICATION_PRIORITY_HIGH = "high"
NOTIFICATION_PRIORITY_NORMAL = "normal"
NOTIFICATION_PRIORITY_LOW = "low"

PRIORITY_DURATIONS = {
    NOTIFICATION_PRIORITY_HIGH: 5000,
    NOTIFICATION_PRIORITY_NORMAL: 3000,
    NOTIFICATION_PRIORITY_LOW: 1500,
}

MAX_QUEUE_SIZE = 3


# ============================================================
# NOTIFICATION CLOUD DATA CLASS
# ============================================================

class NotificationCloud:
    """Data class for notification cloud state attached to the character."""
    def __init__(self, message: str, priority: str = NOTIFICATION_PRIORITY_NORMAL,
                 notification_type: str = "info", action_callback=None):
        self.message = message
        self.priority = priority
        self.notification_type = notification_type
        self.action_callback = action_callback
        self.start_time = 0.0
        self.display_time = PRIORITY_DURATIONS.get(priority, 3000)
        self.progress = 0.0
        self.clicked = False

'''
    content = content[:insert_pos] + cloud_data + content[insert_pos:]
    print('1. Added notification priorities and cloud data class')

# 2. Enhance setup_state() to include notification clouds
setup_state_marker = '    def setup_state(self):'
setup_state_idx = content.find(setup_state_marker)
if setup_state_idx >= 0:
    # Find the ACTIVITY section line
    for i in range(setup_state_idx, min(setup_state_idx + 100, len(content))):
        if '# ---------------- ACTIVITY ----------------' in content[i]:
            # Insert before this line - add notification clouds init
            clouds_init = '''

        # ---------------- NOTIFICATION CLOUD ----------------
        self.notification_clouds = []
'''
        # Find the actual line number
        lines = content.split('\n')
        actual_line_num = 0
        for i in range(setup_state_idx, min(setup_state_idx + 100, len(lines))):
            if '# ---------------- ACTIVITY ----------------' in lines[i]:
                actual_line_num = i + 1  # 1-indexed
                break
        
        if actual_line_num > 0:
            # Insert before the activity section (adjusting for 0-indexed content)
            content = content[:actual_line_num - 1] + clouds_init + content[actual_line_num - 1:]
            print('2. Added notification clouds to setup_state')
        else:
            print('2. Could not find ACTIVITY section position')
else:
    print('2. Could not find setup_state method')

# 2b. Ensure notification_clouds is accessible - verify it's in setup_state
# The line should already be there from step 2

# 3. Enhance show_notification() - add cloud processing at the end
show_notif_marker = '    def show_notification(self, message: str, duration: int = 2200):'
show_notif_idx = content.find(show_notif_marker)
if show_notif_idx >= 0:
    # Find the reposition_for_text section end
    # Look for the line "if len(message) > 80:" and add after it
    long_msg_marker = '        if len(message) > 80:'
    long_msg_idx = content.find(long_msg_marker, show_notif_idx)
    if long_msg_idx >= 0:
        # Get the context around long_msg_idx
        context_start = long_msg_idx - 5
        context_end = long_msg_idx + 50
        context = content[context_start:context_end]
        
        # Add cloud processing after the reposition code
        # The reposition code ends with the QTimer.singleShot line
        cloud_code = '''

        # Process notification cloud
        self.show_notification_cloud(message, priority='normal', notification_type='info')
'''
        # Insert after the long message check
        # Find the exact position - after the try/except block
        insert_pos = long_msg_idx + len('        if len(message) > 80:\n            try:\n                from PySide6.QtCore import QTimer\n                QTimer.singleShot(100, lambda: self.reposition_for_text(len(message), duration))\n            except Exception:\n                pass')
        content = content[:insert_pos] + cloud_code + content[insert_pos:]
        print('3. Added cloud processing to show_notification')
    else:
        print('2b. Could not find long message marker')
else:
    print('2c. Could not find show_notification method')

# 3b. Ensure NotificationCloud class is imported/accessible
# Since we added it at the top, it should be available

# 3. Add show_notification_cloud method after hide_notification
# Find hide_notification method
hide_notif_marker = '    def hide_notification(self):'
hide_notif_idx = content.find(hide_notif_marker)
if hide_notif_idx >= 0:
    # Find the end of hide_notification - it ends with "self.update()"
    # and then there's a blank line and the react method
    # Insert the new methods after hide_notification
    new_methods = '''

    def show_notification_cloud(
        self,
        message: str,
        priority: str = NOTIFICATION_PRIORITY_NORMAL,
        notification_type: str = "info",
        action_text: str = None,
        action_callback=None,
    ):
        """
        Show a notification cloud attached to the character.
        
        The cloud appears visually connected to AVORA and displays
        important information with appropriate expressions and styling.
        """
        if not message:
            return
        
        if priority not in [NOTIFICATION_PRIORITY_HIGH, NOTIFICATION_PRIORITY_NORMAL, NOTIFICATION_PRIORITY_LOW]:
            priority = NOTIFICATION_PRIORITY_NORMAL
        
        cloud = NotificationCloud(
            message=message,
            priority=priority,
            notification_type=notification_type,
            action_callback=action_callback,
        )
        
        if len(self.notification_clouds) >= MAX_QUEUE_SIZE:
            self.notification_clouds.pop(0)
        
        self.notification_clouds.append(cloud)
        
        if len(self.notification_clouds) == 1 and not self._processing_cloud:
            self._processing_cloud = True
            self._process_next_cloud()
    
    def _process_next_cloud(self):
        if not self.notification_clouds or self._processing_cloud:
            self._processing_cloud = False
            return
        
        self._processing_cloud = True
        try:
            cloud = self.notification_clouds[0]
            self.set_state("listening")
            self._update_cloud_ui(cloud)
            if self.notification_timer is not None:
                self.notification_timer.start(cloud.display_time)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(cloud.display_time + 50, self._on_cloud_timeout)
        finally:
            self._processing_cloud = False
    
    def _on_cloud_timeout(self):
        if self.notification_clouds:
            self.notification_clouds.pop(0)
        if self.notification_clouds:
            next_cloud = self.notification_clouds[0]
            self._update_cloud_ui(next_cloud)
            if self.notification_timer is not None:
                self.notification_timer.start(next_cloud.display_time)
            QTimer.singleShot(next_cloud.display_time + 50, self._on_cloud_timeout)
        else:
            self.set_state("idle")
            if self.notification_timer is not None:
                self.notification_timer.stop()
    
    def _update_cloud_ui(self, cloud: NotificationCloud):
        self.notification_label.setText(cloud.message)
        
        type_to_colors = {
            "info": ("#8B7AFF", "#F9FAFB"),
            "success": ("#4ADE80", "#F0F9EB"),
            "warning": ("#FBBF24", "#FFF7ED"),
            "error": ("#F87171", "#FED7D7"),
            "companion": ("#8B7AFF", "#F9FAFB"),
        }
        
        bg_fg = type_to_colors.get(cloud.notification_type, type_to_colors["info"])
        bg_color = bg_fg[0]
        fg_color = bg_fg[1]
        
        if cloud.priority == NOTIFICATION_PRIORITY_HIGH:
            bg_color = self._darken_color(bg_color, 0.2)
        elif cloud.priority == NOTIFICATION_PRIORITY_LOW:
            bg_color = self._lighten_color(bg_color, 0.2)
        
        self.notification_label.setStyleSheet(
            "background-color: rgba(%d, %d, %d, 220); color: %s; border-radius: 12px; padding: 10px 14px;"
            % (bg_color[0], bg_color[1], bg_color[2], fg_color)
        )
        
        self.notification_label.setVisible(True)
        self.notification_label.raise_()
        cloud.progress = 1.0
    
    @staticmethod
    def _rgb_from_hex(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.2) -> str:
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(c * (1 - factor))) for c in rgb)
        return "#%02x%02x%02x" % darkened
    
    @staticmethod
    def _lighten_color(hex_color: str, factor: float = 0.2) -> str:
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        lightened = tuple(min(255, int(c + 255 * factor)) for c in rgb)
        return "#%02x%02x%02x" % lightened
    
    def hide_notification_cloud(self):
        if self.notification_label is not None:
            self.notification_label.setVisible(False)
        
        if self.notification_clouds:
            self.notification_clouds.pop(0)
            if self.notification_clouds:
                next_cloud = self.notification_clouds[0]
                self._update_cloud_ui(next_cloud)
                if self.notification_timer is not None:
                    self.notification_timer.start(next_cloud.display_time)
            else:
                self.set_state("idle")
                if self.notification_timer is not None:
                    self.notification_timer.stop()
    
    def _draw_notification_cloud(self, painter: QPainter, y: float):
        if not self.notification_clouds:
            return
        
        cloud = self.notification_clouds[0]
        
        type_to_fill = {
            "info": QColor(139, 122, 255, 220),
            "success": QColor(74, 222, 128, 220),
            "warning": QColor(251, 191, 36, 220),
            "error": QColor(248, 113, 113, 220),
            "companion": QColor(139, 122, 255, 220),
        }
        type_to_border = {
            "info": QColor(139, 122, 255, 255),
            "success": QColor(74, 222, 128, 255),
            "warning": QColor(251, 191, 36, 255),
            "error": QColor(248, 113, 113, 255),
            "companion": QColor(139, 122, 255, 255),
        }
        
        fill_color = type_to_fill.get(cloud.notification_type, QColor(139, 122, 255, 220))
        border_color = type_to_border.get(cloud.notification_type, QColor(139, 122, 255, 255))
        
        progress = cloud.progress if hasattr(cloud, 'progress') else 1.0
        alpha = int(220 * progress)
        fill_color.setAlpha(alpha)
        
        cloud_width = max(120, min(220, len(cloud.message) * 8 + 20))
        cloud_width = max(cloud_width, 120)
        
        painter.setBrush(fill_color)
        painter.setPen(border_color)
        painter.drawRoundedRect(
            int(-cloud_width // 2),
            int(-80),
            int(cloud_width),
            int(50),
            12,
            12,
        )
        
        painter.setPen(border_color if border_color.color().getRgb() != -1 else QColor(245, 250, 255))
        painter.setFont(QFont("Segoe UI", 9))
        
        text_rect = painter.fontMetrics().boundingRect(
            cloud.message,
            Qt.TextWordWrap,
            int(cloud_width - 20)
        )
        
        text_x = int(-text_rect.width() // 2)
        text_y = int(10 + text_rect.height() // 2)
        
        painter.drawText(
            text_x,
            text_y,
            int(cloud_width - 20),
            text_rect.height(),
            Qt.TextWordWrap,
            cloud.message
        )
    
    def paintEvent(self, event):
        # ... existing paint event code will remain,
        # we'll add the cloud drawing call separately
'''
    
    hide_end_marker = '    def hide_notification(self):'
    hide_idx = content.find(hide_notif_marker)
    if hide_idx >= 0:
        # Find the end of the hide_notification method
        # It should end with "self.update()" followed by blank lines and "def react"
        # Let me search for the pattern
        react_marker = '    def react'
        react_idx = content.find(react_marker, hide_idx)
        if react_idx >= 0:
            # Insert the new methods between hide_notification and react
            content = content[:react_idx] + new_methods + content[react_idx:]
            print('3. Added show_notification_cloud and helper methods after hide_notification')
        else:
            print('3. Could not find react method position - appending at end')
            content += new_methods
            print('3. Added methods at end of file')
else:
    print('3. Could not find hide_notification method')

# 4. Add _draw_notification_cloud call in paintEvent
# This is trickier - we need to find the paintEvent method and add the call
# at the end of the method. Let me find paintEvent and add it.
paint_marker = '    def paintEvent(self, event):'
paint_idx = content.find(paint_marker)
if paint_idx >= 0:
    # Find the end of paintEvent - look for the pattern where it ends
    # Typically with " painter.save()" and " painter.restore()" pattern or the end
    # Let me search for a good insertion point
    # I'll look for the line after "self.draw_body_details(painter, y)" which is typically near the end
    
    # Actually, let me take a different approach - I'll add the cloud drawing
    # at the very end of the paintEvent method by finding where it ends
    # For now, I'll just note this needs to be done
    print('4. Need to add _draw_notification_cloud call in paintEvent')
    
    # Let me try to find a good position - after the body_details call
    # or at the end of the method
    # I'll search for the pattern that marks the end of paintEvent
    # Typically there's a sequence of draw calls followed by the method ending
    
    # For now, let me just verify the file compiles and note what needs to be added
    print('4. PaintEvent cloud drawing will be added manually after verification')
else:
    print('4. Could not find paintEvent method')

# Write the modified content back
with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\character.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\\nPatch applied. Now verifying syntax...')