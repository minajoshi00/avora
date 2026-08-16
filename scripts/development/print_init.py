with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Show the __init__ method - lines 243-380
for i in range(242, min(380, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')