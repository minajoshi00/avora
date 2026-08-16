import sys
sys.path.insert(0, r'C:\Users\minaj\OneDrive\Desktop\avora\avora backend')

from character import Character
from settings import get_setting, set_setting

print('Character module imported successfully')
print('Settings module imported successfully')

# Test that the Character class has the new methods
c = Character()
print('Character created: state=%s, expression=%s' % (c.state, c.expression))
print('show_notification_cloud method exists: %s' % str(hasattr(c, 'show_notification_cloud')))
print('hide_notification_cloud method exists: %s' % str(hasattr(c, 'hide_notification_cloud')))
print('set_state method exists: %s' % str(hasattr(c, 'set_state')))
print('Notification clouds list initialized: %s' % str(len(c.notification_clouds) == 0))
print('Notification label initialized: %s' % str(c.notification_label is not None))

# Test show_notification_cloud
c.show_notification_cloud('Test notification', priority='normal', notification_type='success')
print('show_notification_cloud works: %s' % str(len(c.notification_clouds) == 1))
print('Cloud message: %s' % c.notification_clouds[0].message)
print('Cloud priority: %s' % c.notification_clouds[0].priority)
print('Cloud type: %s' % c.notification_clouds[0].notification_type)

# Test hide_notification_cloud
c.hide_notification_cloud()
print('hide_notification_cloud works: %s' % str(len(c.notification_clouds) == 0))
print('Character state after hide: %s' % c.state)

print()
print('All basic tests passed!')