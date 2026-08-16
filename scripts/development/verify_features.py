#!/usr/bin/env python3
with open(r'C:\Users\minaj\OneDrive\Desktop\avora\avora_desktop\main.py', 'rb') as f:
    content = f.read()

# Search for UI elements
patterns = [
    (b'New Chat', 'New Chat'),
    (b'New Conversation', 'New Conversation'),
    (b'voice_button', 'Voice button'),
    (b'mic_button', 'Mic button'),
    (b'send_btn', 'Send button'),
    (b'scroll_to_bottom', 'Auto-scroll'),
    (b'resizeEvent', 'Resize event'),
    (b'changeEvent', 'Change event'),
    (b'apply_theme_to_app()', 'Theme apply'),
]

for pattern, name in patterns:
    idx = content.find(pattern)
    status = 'OK' if idx >= 0 else 'MISSING'
    print(f'{name}: {status}')

# Also search for button texts
button_texts = [b'New Conversation', b'Settings', b'Send', b'Cancel', b'Retry']
print()
for text in button_texts:
    idx = content.find(text)
    status = 'OK' if idx >= 0 else 'MISSING'
    print(f'Button text \"{text.decode()}\": {status}')
"