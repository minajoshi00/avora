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
        self.start_time = 0.0  # Set when shown
        self.display_time = PRIORITY_DURATIONS.get(priority, 3000)
        self.progress = 0.0  # 0.0 to 1.0 for fade out animation
        self.clicked = False


# ============================================================
# CHARACTER CLASS - INCREMENTAL ENHANCEMENTS
# ============================================================

# The rest of the character.py file remains unchanged below this line.
# The following enhancements will be added as insertions.

# After setup_state(), add notification clouds initialization:
# (This will be inserted in the setup_state method)

# After setup_timers(), add cloud timer setup:
# (This will be added to setup_timers)

# After show_notification(), add cloud processing:
# (This will be added to show_notification)

# After hide_notification(), add cloud cleanup:
# (This will be added to hide_notification)

# After paintEvent, add _draw_notification_cloud:
# (This will be added to paintEvent)