import os

filepath = r'avora backend/settings.py'

with open(filepath, 'r') as f:
    content = f.read()

# Add desktop_notifications setting under the notifications category
old_notif = """    "notifications": {
        "enabled": True,

        "email_notifications": True,

        "reminder_notifications": True,

        "automation_notifications": True,

        "weather_notifications": True,

        "do_not_disturb": False,

        "quiet_hours_start": "22:00",

        "quiet_hours_end": "08:00",

        "notification_sound": True,

        "notification_position": "bottom_right",
    },"""

new_notif = """    "notifications": {
        "enabled": True,

        "email_notifications": True,

        "reminder_notifications": True,

        "automation_notifications": True,

        "weather_notifications": True,

        "do_not_disturb": False,

        "quiet_hours_start": "22:00",

        "quiet_hours_end": "08:00",

        "notification_sound": True,

        "notification_position": "bottom_right",

        "desktop_notifications": True,
    },"""

if old_notif in content:
    content = content.replace(old_notif, new_notif)
    print('Added desktop_notifications setting')
else:
    print('Old notifications pattern not found')

with open(filepath, 'w') as f:
    f.write(content)

print("Done")