import py_compile
import sys

files = [
    r"C:\Users\minaj\OneDrive\Desktop\avora\avora backend\main.py",
    r"C:\Users\minaj\OneDrive\Desktop\avora\avora backend\voice.py",
]

all_ok = True
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"{f}: SYNTAX OK")
    except py_compile.PyCompileError as e:
        print(f"{f}: SYNTAX ERROR - {e}")
        all_ok = False

sys.exit(0 if all_ok else 1)