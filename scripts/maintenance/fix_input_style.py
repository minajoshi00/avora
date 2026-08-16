#!/usr/bin/env python3
import sys

filepath = r"C:\Users\minaj\OneDrive\Desktop\avora\avora_desktop\main.py"
with open(filepath, "rb") as f:
    content = f.read()

# Replace the input field stylesheet to use theme colors
old_input_style = b'QLineEdit {\r\n                background: rgba(255,255,255,0.08);\r\n                border: 1px solid rgba(255,255,255,0.15);\r\n                border-radius: 12px;\r\n                padding: 10px 14px;\r\n                color: #e5e5e5;\r\n            }'

new_input_style = b'QLineEdit {\r\n                background: rgba(255,255,255,0.05);\r\n                border: 1px solid rgba(255,255,255,0.1);\r\n                border-radius: 12px;\r\n                padding: 10px 14px;\r\n                color: #e5e5e5;\r\n                selection-background-color: rgba(139,122,255,0.3);\r\n                selection-color: #6366f1;\r\n            }\r\n            QLineEdit:focus {\r\n                border-color: rgba(99, 102, 241, 0.5);\r\n            }'

if old_input_style in content:
    content = content.replace(old_input_style, new_input_style)
    with open(filepath, "wb") as f:
        f.write(content)
    print("Input field stylesheet updated")
else:
    print("Old input style not found")