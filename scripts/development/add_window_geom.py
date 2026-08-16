with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add geometry restore in __init__ after the resize line (after line 335)
# The resize is at: self.resize(1200, 800) at approximately line 332-335
# I need to insert after self.setMinimumSize and before the UI section

# Find the exact location - after self.setMinimumSize(950, 700)
old_resize = '''        self.setMinimumSize(
            950,
            700
        )

        # ===================================================='''

new_resize = '''        self.setMinimumSize(
            950,
            700
        )

        # Restore window geometry from settings
        self.restore_window_geometry()

        # ===================================================='''

if old_resize in content:
    content = content.replace(old_resize, new_resize)
    print('Added restore_window_geometry call in __init__')
else:
    print('resize pattern not found')

# 2. Add the restore_window_geometry method - add after the __init__ method
# Find the end of __init__ and add the new method
# The __init__ ends around line 380 (before the SIGNALS section)

# Actually, let me add the method somewhere logical - after the closeEvent or at the class level
# Let me find the closeEvent and add the save/read methods near it

# 3. Add geometry save in closeEvent
# Find closeEvent
old_closeevent = '''    def closeEvent(
        self,
        event,
    ):

        self.is_closing = True

        # Stop microphone if recording
        if is_recording():'''

new_closeevent = '''    def closeEvent(
        self,
        event,
    ):

        self.is_closing = True

        # Save window geometry to settings
        self.save_window_geometry()

        # Stop microphone if recording
        if is_recording():'''

if old_closeevent in content:
    content = content.replace(old_closeevent, new_closeevent)
    print('Added save_window_geometry call in closeEvent')
else:
    print('closeEvent pattern not found')

# 4. Add the save_window_geometry and restore_window_geometry methods
# Add them after the closeEvent method
# Find the end of closeEvent
lines = content.split('\n')
# Find closeEvent end - it should be followed by other methods
# Let me just append the methods at the class level, before the very end

# First, let me find a good insertion point - after the closeEvent
# The closeEvent ends and then there's probably more code

# Let me search for where closeEvent ends
content_after_close = content[content.find('def closeEvent'):]
# Find the next major section

# Actually, let me just add the methods at the end of the MainWindow class
# I'll find where the MainWindow class ends

# Alternative approach: add the methods right after closeEvent
# Let me find where closeEvent's body ends

# Count braces to find the end of closeEvent
search_text = '''    def closeEvent(
        self,
        event,
    ):
        self.is_closing = True

        # Save window geometry to settings
        self.save_window_geometry()

        # Stop microphone if recording'''

# Let me just add the two methods after the closeEvent
# I'll insert them after the line 'self.is_closing = True' and the microphone stop code

# Actually, let me take a different approach - add the methods as standalone methods 
# after the closeEvent by finding the right location

# Find position after closeEvent body
idx = content.find('self.is_closing = True\n\n        # Stop microphone')
if idx >= 0:
    # Find the end of that line block
    idx_end = content.find('\n\n#', idx)
    if idx_end >= 0:
        methods_text = '''
    
    def save_window_geometry(self):
        """Save window geometry and position to settings."""
        try:
            geometry = self.saveGeometry()
            settings = get_setting("window_geometry", {})
            settings["geometry"] = geometry.saveGeometry().data().decode('utf-8') if geometry else ""
            set_setting("window_geometry", settings)
        except Exception as e:
            print("Save window geometry error:", e)

    def restore_window_geometry(self):
        """Restore window geometry and position from settings, with multi-monitor handling."""
        try:
            settings = get_setting("window_geometry", {})
            geometry_str = settings.get("geometry", "")
            if geometry_str:
                geometry = Qt.QByteArray().fromBase64(geometry_str.encode('utf-8'))
                if geometry.isValid():
                    self.restoreGeometry(geometry)
                else:
                    # Position outside current monitor - use center
                    self.resize(1200, 800)
                    self.move(
                        (self.screen().availableGeometry().width() - 1200) // 2,
                        (self.screen().availableGeometry().height() - 800) // 2
                    )
            else:
                self.resize(1200, 800)
                self.move(
                    (self.screen().availableGeometry().width() - 1200) // 2,
                    (self.screen().availableGeometry().height() - 800) // 2
                )
        except Exception as e:
            print("Restore window geometry error:", e)
            self.resize(1200, 800)
            self.move(
                (self.screen().availableGeometry().width() - 1200) // 2,
                (self.screen().availableGeometry().height() - 800) // 2
            )'''
        
        content = content[:idx_end] + methods_text + content[idx_end:]
        print('Added save_window_geometry and restore_window_geometry methods')
    else:
        print('Could not find closeEvent body position')
else:
    print('Could not find save geometry call pattern')

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')