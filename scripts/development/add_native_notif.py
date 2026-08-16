import sys
sys.path.insert(0, 'avora/backend')

with open('avora/backend/character.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find hide_notification method and add show_native_notification after it
old_hide = """    def hide_notification(self):
        if self.notification_timer is not None and self.notification_timer.isActive():
            self.notification_timer.stop()
        if self.notification_label is not None:
            self.notification_label.setVisible(False)
        self.notification_visible = False
        self.update()"""

new_hide = """    def hide_notification(self):
        if self.notification_timer is not None and self.notification_timer.isActive():
            self.notification_timer.stop()
        if self.notification_label is not None:
            self.notification_label.setVisible(False)
        self.notification_visible = False
        self.update()

    def show_native_notification(self, message: str, duration: int = 2200):
        """Show a native system desktop notification."""
        try:
            tray = QSystemTrayIcon(self)
            tray.setVisible(False)
            tray.showMessage(
                "AVORA",
                message,
                None,
                duration
            )
        except Exception as e:
            print("Native notification error:", e)"""

if old_hide in content:
    content = content.replace(old_hide, new_hide)
    print("Added show_native_notification method")
else:
    print("hide_notification pattern not found")

with open('avora/backend/character.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")