import shlex
cmd = 'python -c "import time; time.sleep(30)"'
print("posix=False ->", shlex.split(cmd, posix=False))
print("posix=True  ->", shlex.split(cmd, posix=True))
