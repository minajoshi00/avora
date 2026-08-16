#!/usr/bin/env python3
import sys

filepath = r"C:\Users\minaj\OneDrive\Desktop\avora\avora_desktop\main.py"
with open(filepath, "rb") as f:
    content = f.read()

# Update Stop button style - add hover state
old_stop_btn = b'QPushButton {\r\n                background: rgba(239, 68, 68, 0.2);\r\n                border: 1px solid rgba(239, 68, 68, 0.4);\r\n                color: #ef4444;\r\n                padding: 8px 16px;\r\n                border-radius: 6px;\r\n            }\r\n            QPushButton:disabled {'

new_stop_btn = b'QPushButton {\r\n                background: rgba(239, 68, 68, 0.2);\r\n                border: 1px solid rgba(239, 68, 68, 0.4);\r\n                color: #ef4444;\r\n                padding: 8px 16px;\r\n                border-radius: 8px;\r\n            }\r\n            QPushButton:hover {\r\n                background: rgba(251, 115, 26, 0.3);\r\n            }\r\n            QPushButton:disabled {'

if old_stop_btn in content:
    content = content.replace(old_stop_btn, new_stop_btn)
    print("Stop button style updated")
else:
    print("Stop button style not found - searching alternative")

# Find and update the actual stop button style (there may be two occurrences)
# Let me search for the one in AvoraDesktopWindow class
import re
# Find all QPushButton definitions with the specific stop button pattern
matches = list(re.finditer(b'QPushButton \\{\\r\\n                background: rgba\\(239, 68, 68, 0.2\\);', content))
print(f"Found {len(matches)} stop button styles")

# Update retry button style - add hover state
old_retry_btn = b'QPushButton {\\r\\n                background: rgba\\(59, 130, 246, 0.2\\);\\r\\n                border: 1px solid rgba\\(59, 130, 246, 0.4\\);\\r\\n                color: #3b82f6;\\r\\n                padding: 8px 16px;\\r\\n                border-radius: 6px;\\r\\n                margin-right: 8px;\\r\\n            \\}\\r\\n            QPushButton:disabled'

# Let me just do simple replacements one at a time
# Update the first stop button style found
stop_match = matches[0] if matches else None
if stop_match:
    pos = stop_match.start()
    # Get the full button style section
    section_start = content.rfind(b'QPushButton {', pos - 500) if pos > 500 else 0
    # Actually, let me just replace the specific known pattern
    
    # Find the exact stop button in the UI setup area
    # The stop button is defined around line 422-437 originally
    # Let me search for the specific context
    context_marker = b'_onStop'
    ctx_idx = content.find(context_marker)
    if ctx_idx >= 0:
        # Print surrounding context
        print(f"Found _onStop at {ctx_idx}")
        # The stop btn style should be nearby in the file
"