#!/usr/bin/env python3
with open(r'C:\Users\minaj\OneDrive\Desktop\avora\avora_desktop\main.py', 'rb') as f:
    content = f.read()

idx = content.find(b'class AvoraDesktopWindow')
init_search = content.find(b'def __init__', idx)
remaining = content[init_search:]
import re
method_starts = [m.start() for m in re.finditer(b'def ', remaining)]
init_end = method_starts[1] if len(method_starts) > 1 else len(remaining)
init_method = remaining[:init_end]

lines = init_method.split(b'\n')[:60]
for i, line in enumerate(lines):
    try:
        text = line.decode('utf-8')[:120]
        print(f'{i+1}: {text}')
    except:
        print(f'{i+1}: [decode error]')