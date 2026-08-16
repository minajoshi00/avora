#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [r"C:\Users\minaj\AppData\Local\Programs\Python\Python314\python.exe", 
     r"C:\Users\minaj\OneDrive\Desktop\avora\avora backend\main.py"],
    capture_output=True,
    text=True,
    cwd=r"C:\Users\minaj\OneDrive\Desktop\avora"
)
print("=" * 60)
print("STDOUT:", result.stdout[:500] if result.stdout else "empty")
print("STDERR:", result.stderr[:500] if result.stderr else "empty")
print("Return code:", result.returncode)
print("=" * 60)
EOF