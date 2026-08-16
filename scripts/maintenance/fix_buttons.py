#!/usr/bin/env python3
import sys
import re

filepath = r"C:\Users\minaj\OneDrive\Desktop\avora\desktop\main.py"
with open(filepath, "rb") as f:
    content = f.read()

# Update Stop button - change border-radius to 8px and add hover state
# The stop button stylesheet is set at the "Stop / Cancel" button definition
# Find the exact stop button style section
stop_pattern = b'QPushButton \\{\\r\\n                background: rgba\\(239, 68, 68, 0.2\\);\\r\\n                border: 1px solid rgba\\(239, 68, 68, 0.4\\);\\r\\n                color: #ef4444;\\r\\n                padding: 8px 16px;\\r\\n                border-radius: 8px;'

# Actually, looking at the output, the stop button at 14720-14803 has border-radius that needs updating
# Let me just replace the specific stop button style that has 6px radius
old_stop_style = b'QPushButton {\\r\\n                background: rgba\\(239, 68, 68, 0.2\\);\\r\\n                border: 1px solid rgba\\(239, 68, 68, 0.4\\);\\r\\n                color: #ef4444;\\r\\n                padding: 8px 16px;\\r\\n                border-radius: 6px;'

new_stop_style = b'QPushButton {\\r\\n                background: rgba\\(239, 68, 68, 0.2\\);\\r\\n                border: 1px solid rgba\\(239, 68, 68, 0.4\\);\\r\\n                color: #ef4444;\\r\\n                padding: 8px 16px;\\r\\n                border-radius: 8px;\\r\\n            }\\r\\n            QPushButton:hover {\\r\\n                background: rgba\\(251, 115, 26, 0.3\\);\\r\\n            }'

if old_stop_style in content:
    content = content.replace(old_stop_style, new_stop_style)
    print("Stop button style updated (6px -> 8px radius, added hover)")
else:
    print("Stop button style not found with exact match, trying alternative...")
    # Try without the \r\n
    old_stop_style2 = b'QPushButton {\n                background: rgba(239, 68, 68, 0.2);\n                border: 1px solid rgba(239, 68, 68, 0.4);\n                color: #ef4444;\n                padding: 8px 16px;\n                border-radius: 6px;\n'
    if old_stop_style2 in content:
        new_stop_style2 = b'QPushButton {\n                background: rgba(239, 68, 68, 0.2);\n                border: 1px solid rgba(239, 68, 68, 0.4);\n                color: #ef4444;\n                padding: 8px 16px;\n                border-radius: 8px;\n            }\n            QPushButton:hover {\n                background: rgba(251, 115, 26, 0.3);\n            }'
        if old_stop_style2 in content:
            content = content.replace(old_stop_style2, new_stop_style2)
            print("Stop button style updated (alternative match)")
        else:
            print("Alternative stop button pattern not found either")
    else:
        print("No alternative stop button pattern found")

# Update Retry button - change border-radius to 8px and add hover state
old_retry_style = b'QPushButton {\\r\\n                background: rgba\\(59, 130, 246, 0.2\\);\\r\\n                border: 1px solid rgba\\(59, 130, 246, 0.4\\);\\r\\n                color: #3b82f6;\\r\\n                padding: 8px 16px;\\r\\n                border-radius: 6px;\\r\\n                margin-right: 8px;'

new_retry_style = b'QPushButton {\\r\\n                background: rgba\\(59, 130, 246, 0.2\\);\\r\\n                border: 1px solid rgba\\(59, 130, 246, 0.4\\);\\r\\n                color: #3b82f6;\\r\\n                padding: 8px 16px;\\r\\n                border-radius: 8px;\\r\\n                margin-right: 8px;\\r\\n}\\r\\n            QPushButton:hover {\\r\\n                background: rgba\\(96, 165, 251, 0.3\\);\\r\\n            }'

if old_retry_style in content:
    content = content.replace(old_retry_style, new_retry_style)
    print("Retry button style updated (6px -> 8px radius, added hover)")
else:
    print("Retry button style not found with exact match, trying alternative...")
    old_retry_style2 = b'QPushButton {\n                background: rgba(59, 130, 246, 0.2);\n                border: 1px solid rgba(59, 130, 246, 0.4);\n                color: #3b82f6;\n                padding: 8px 16px;\n                border-radius: 6px;\n                margin-right: 8px;\n'
    if old_retry_style2 in content:
        new_retry_style2 = b'QPushButton {\n                background: rgba(59, 130, 246, 0.2);\n                border: 1px solid rgba(59, 130, 246, 0.4);\n                color: #3b82f6;\n                padding: 8px 16px;\n                border-radius: 8px;\n                margin-right: 8px;\n            }\n            QPushButton:hover {\n                background: rgba(96, 165, 251, 0.3);\n            }'
        if new_retry_style2 in content or True:  # Always try the replacement
            # Actually do the replacement
            if old_retry_style2 in content:
                content = content.replace(old_retry_style2, new_retry_style2)
                print("Retry button style updated (alternative match)")
            else:
                print("Alternative retry button pattern not found")
        else:
            print("Alternative retry button pattern not found")
    else:
        print("No alternative retry button pattern found")

# Write the modified content back
with open(filepath, "wb") as f:
    f.write(content)

print("\nButton updates complete")