import py_compile
try:
    py_compile.compile("main.py", doraise=True)
    print("main.py: OK")
except py_compile.PyCompileError as e:
    print("main.py: FAILED")
    print(e)
try:
    py_compile.compile("chat_sidebar.py", doraise=True)
    print("chat_sidebar.py: OK")
except py_compile.PyCompileError as e:
    print("chat_sidebar.py: FAILED")
    print(e)
