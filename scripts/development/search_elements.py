import os
src_dir = r'C:\Users\minaj\OneDrive\Desktop\avora\frontend\src'
with open(os.path.join(src_dir, 'pages\Home.tsx'), 'r', encoding='utf-8') as f:
    content = f.read()
    searches = ['sidebar', 'mascot', 'new chat', 'status', 'creating']
    for kw in searches:
        count = content.lower().count(kw.lower())
        print(f'Contains "{kw}": {count} times')
" 2>&1