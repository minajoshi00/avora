with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'r', encoding='utf-8') as f:
    content = f.read()

# completely fix the is_speaking function and reposition the interrupt functions
# Find and replace the broken is_speaking + nested functions

# Find where is_speaking starts and where it should end
is_speaking_start = content.find('def is_speaking():')
if is_speaking_start >= 0:
    # Find the return _is_speaking line
    return_line = content.find('return _is_speaking', is_speaking_start)
    if return_line >= 0:
        # Find what's between the function def and the return
        # This includes the broken resume_listening function
        # We want to replace everything from 'def is_speaking():' to 'return _is_speaking'
        # with just the fixed function: 'def is_speaking():\n    global _is_speaking\n    return _is_speaking'
        
        # First, let me find what comes after return _is_speaking
        after_return = content[return_line + len('return _is_speaking'):]
        # Find the next top-level function or section
        # Look for a new def or major section header
        next_section = content.find('\n\n#', return_line)
        if next_section >= 0:
            # Keep content from next_section onward
            after_section = content[next_section:]
            # Now replace the broken part
            fixed_func = 'def is_speaking():\n    global _is_speaking\n    return _is_speaking\n'
            content = content[:is_speaking_start] + fixed_func + after_section
            print('Fixed is_speaking function structure')
        else:
            print('Could not find next section')
    else:
        print('Could not find return line')
else:
    print('is_speaking start not found')

# Now make sure interrupt_speaking and resume_listening are at module level
# They should be after the STATUS section and before CALLBACK
# Check if they already exist at the right place
if 'def interrupt_speaking()' in content:
    # Check if they're at module level (not nested inside is_speaking)
    # They should be after line 554 (after the STATUS section)
    lines = content.split('\n')
    interrupt_line_idx = None
    for i, line in enumerate(lines):
        if 'def interrupt_speaking()' in line:
            interrupt_line_idx = i
            break
    
    if interrupt_line_idx is not None and interrupt_line_idx < 550:
        # They're too early - move them after the STATUS section
        # Find the STATUS section end
        status_end = None
        for i, line in enumerate(lines[:30]):
            if '# ========================================================' in line and '# STATUS' in line:
                status_end = i
                break
        
        if status_end and status_end > 0 and status_end < interrupt_line_idx:
            # Move the interrupt functions after line status_end
            # Get the interrupt function text
            interrupt_func_start = content.find('def interrupt_speaking()')
            interrupt_func_end = content.find('\n\ndef ', interrupt_func_start)
            if interrupt_func_end >= 0:
                interrupt_text = content[interrupt_func_start:interrupt_func_end]
                # Remove from current position
                content = content[:interrupt_func_start] + content[interrupt_func_end:]
                # Insert after status_end
                # Find the actual line position
                lines = content.split('\n')
                # Insert after the STATUS section header line
                insert_pos = 0
                for i, line in enumerate(lines):
                    if i > status_end and i < len(lines) - 1:
                        # Find a good insertion point - after blank lines following STATUS
                        if line.strip() == '' and i > 0 and lines[i-1].strip() == '# STATUS':
                            insert_pos = i
                            break
                
                if insert_pos > 0:
                    content = content[:insert_pos] + '\n' + interrupt_text + content[insert_pos:]
                    print('Moved interrupt functions to module level')
                else:
                    print('Could not find insertion point')
            else:
                print('Could not find interrupt function end')
    else:
        print('interrupt functions already at module level')
else:
    print('interrupt_speaking function not found')

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')