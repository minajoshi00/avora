#!/usr/bin/env python3
with open(r'C:\Users\minaj\OneDrive\Desktop\avora\avora_desktop\main.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Check for padding values
import re
paddings = re.findall(r'padding:\s*([^;\)]+)', content)
print('Padding values found:')
for p in set(paddings):
    print(f'  {p.strip()}')

print()

# Find all margins
margins = re.findall(r'margin:\s*([^;\)]+)', content)
print('Margin values found:')
for m in set(margins):
    print(f'  {m.strip()}')

print()

# Check font family consistency
fonts = re.findall(r'font-family:[^\"]*\"', content)
print('Font families found:')
for f in set(fonts):
    print(f'  {f.strip()}')