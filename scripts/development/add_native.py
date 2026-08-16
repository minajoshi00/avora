with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\character.py', 'r', encoding='utf-8') as f:
    content = f.read()

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

    def show_native_notification(self, message, duration=2200):
        # Show native system notification
        try:
            from PySide6.QtWidgets import QSystemTrayIcon
            tray = QSystemTrayIcon()
            tray.showMessage("AVORA", message, None, duration)
        except Exception as e:
            print("Native notification error:", e)"""

if old_hide in content:
    content = content.replace(old_hide, new_hide)
    print("Added show_native_notification method")
else:
    print("hide_notification pattern not found")

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\character.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")