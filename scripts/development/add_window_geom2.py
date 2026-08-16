with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add the save_window_geometry and restore_window_geometry methods after closeEvent
# Find the closeEvent method and add after its body

# The closeEvent ends with the microphone stop code. Let me find where the 
# next method starts after closeEvent.

# I'll search for the next 'def ' after line 3850
# First, let me find a good insertion point

# Let me just append the methods at the end of the MainWindow class
# I'll find where the MainWindow class ends (before other modules/classes)

# Alternative: insert the methods right after the closeEvent block
# I'll find the closeEvent and add methods after its trailing whitespace/newlines

# Let me locate the exact position to insert
# Look for the closeEvent definition and its body
close_event_pattern = """    def closeEvent(
        self,
        event,
    ):

        self.is_closing = True

        # Save window geometry to settings
        self.save_window_geometry()

        # Stop microphone if recording
        if is_recording():
"""

# Find this pattern
idx = content.find(close_event_pattern)
if idx >= 0:
    # Find the end of this block - look for the next major section
    # The closeEvent body ends and then there might be more methods or the class ends
    # Let me find where to insert - after the is_recording() block
    
    # Let me search for the next 'def ' after the closeEvent
    search_area = content[idx + len(close_event_pattern):]
    next_def = search_area.find('\n\ndef ')
    if next_def >= 0:
        # Insert the methods before the next def
        methods = '''
    def save_window_geometry(self):
        """Save window geometry and position to settings."""
        try:
            geometry = self.saveGeometry()
            # Convert QByteArray to string for JSON storage
            geometry_str = geometry.toBase64().data().decode('utf-8') if geometry else ""
            settings = get_setting("window_geometry", {})
            settings["geometry"] = geometry_str
            set_setting("window_geometry", settings)
        except Exception as e:
            print("Save window geometry error:", e)

    def restore_window_geometry(self):
        """Restore window geometry and position from settings, with multi-monitor handling."""
        try:
            settings = get_setting("window_geometry", {})
            geometry_str = settings.get("geometry", "")
            if geometry_str:
                # Restore from base64-encoded QByteArray
                geometry = Qt.QByteArray.fromBase64(geometry_str.encode('utf-8'))
                if geometry.isValid():
                    self.restoreGeometry(geometry)
                else:
                    # Position outside current monitor - use center screen
                    available = self.screen().availableGeometry()
                    self.resize(1200, 800)
                    self.move(
                        (available.width() - 1200) // 2,
                        (available.height() - 800) // 2
                    )
            else:
                # No saved geometry - center on current screen
                available = self.screen().availableGeometry()
                self.resize(1200, 800)
                self.move(
                    (available.width() - 1200) // 2,
                    (available.height() - 800) // 2
                )
        except Exception as e:
            print("Restore window geometry error:", e)
            # Fallback: center on screen
            available = self.screen().availableGeometry()
            self.resize(1200, 800)
            self.move(
                (available.width() - 1200) // 2,
                (available.height() - 800) // 2
            )'''

        # Insert before the next def
        insert_pos = idx + len(close_event_pattern) + next_def
        # Actually, let me calculate properly
        # The insert position is: idx + length of pattern + the position of next_def within search_area
        # But easier: just find the absolute position
        
        # Let me take a simpler approach - find the absolute line number
        abs_insert_pos = idx + next_def
        content = content[:insert_pos] + methods + content[insert_pos:]
        print('Added window geometry methods before next function')
    else:
        print('Could not find next def after closeEvent')
        # Fallback: append at the end of the file
        methods = '''

    def save_window_geometry(self):
        """Save window geometry and position to settings."""
        try:
            geometry = self.saveGeometry()
            geometry_str = geometry.toBase64().data().decode('utf-8') if geometry else ""
            settings = get_setting("window_geometry", {})
            settings["geometry"] = geometry_str
            set_setting("window_geometry", settings)
        except Exception as e:
            print("Save window geometry error:", e)

    def restore_window_geometry(self):
        """Restore window geometry and position from settings, with multi-monitor handling."""
        try:
            settings = get_setting("window_geometry", {})
            geometry_str = settings.get("geometry", "")
            if geometry_str:
                geometry = Qt.QByteArray.fromBase64(geometry_str.encode('utf-8'))
                if geometry.isValid():
                    self.restoreGeometry(geometry)
                else:
                    available = self.screen().availableGeometry()
                    self.resize(1200, 800)
                    self.move(
                        (available.width() - 1200) // 2,
                        (available.height() - 800) // 2
                    )
            else:
                available = self.screen().availableGeometry()
                self.resize(1200, 800)
                self.move(
                    (available.width() - 1200) // 2,
                    (available.height() - 800) // 2
                )
        except Exception as e:
            print("Restore window geometry error:", e)
            available = self.screen().availableGeometry()
            self.resize(1200, 800)
            self.move(
                (available.width() - 1200) // 2,
                (available.height() - 800) // 2
            )'''
        content += methods
        print('Added window geometry methods at end of MainWindow')
else:
    print('closeEvent pattern not found')

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')