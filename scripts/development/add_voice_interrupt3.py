with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the is_speaking function - it's def is_speaking(): without self parameter
search_text = 'def is_speaking():'
idx = content.find(search_text)
if idx >= 0:
    # Find end of this function definition (next double newline or end)
    idx_end = content.find('\n\n', idx)
    if idx_end >= 0:
        interrupt_func = '\n\n# ========================================================\n# VOICE INTERRUPTION\n# ========================================================\n\ndef interrupt_speaking():\n    global _is_speaking, _user_speaking\n    _user_speaking = False\n    stop_speaking()\n    _is_speaking = False\n\ndef resume_listening():\n    global _is_speaking, _user_speaking\n    _user_speaking = False\n    _is_speaking = False\n'
        content = content[:idx_end] + interrupt_func + content[idx_end:]
        print('Added interrupt_speaking function after is_speaking')
    else:
        print('Could not find end of is_speaking function')
else:
    print('is_speaking function not found')

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')