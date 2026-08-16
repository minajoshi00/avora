import subprocess, os, sys
exe_path = r'C:\Users\minaj\OneDrive\Desktop\avora\avora backend\dist\AVORA\AVORA.exe'
print('Executable exists:', os.path.exists(exe_path))
proc = subprocess.Popen([exe_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
try:
    proc.wait(timeout=10)
except subprocess.TimeoutExpired:
    proc.kill()
print('return code:', proc.returncode)