with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\settings.py', 'r', encoding='utf-8') as f:
    content = f.read()
    # Find notifications section
    idx = content.find('"notifications"')
    if idx >= 0:
        # Print the notifications section
        section = content[idx:idx+800]
        print(section[:800])
    else:
        print('notifications section not found')