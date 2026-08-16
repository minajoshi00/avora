with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find closeEvent or is_related lines
for i, line in enumerate(lines, 1):
    lower = line.lower().strip()
    if 'closeevent' in lower or 'is_closing' in lower or 'on_closing' in lower:
        print(f'Line {i}: {line}', end='')
        for j in range(i+1, min(i+6, len(lines))):
            print(f'Line {j}: {lines[j-1]}', end='')
        print('---')