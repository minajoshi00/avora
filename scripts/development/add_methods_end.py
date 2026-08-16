with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add the methods at the end of the file, before any trailing content
# First, check if they already exist
if 'def save_window_geometry' in content:
    print('save_window_geometry already exists')
else:
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
    content += methods
    print('Added window geometry methods at end of file')

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')