#!/usr/bin/env python3
import sys

filepath = r"C:\Users\minaj\OneDrive\Desktop\avora\avora_desktop\main.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the font
old = 'self.setFont(QFont("Arial", 28))'
new = 'self.setFont(QFont("Segoe UI", 28))'
if old in content:
    content = content.replace(old, new)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Font replaced")
else:
    print("Pattern not found")