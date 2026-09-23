import sys
from remote_exec import run_remote_command

remote_cmd = """python3 - << 'EOF'
import subprocess
out = subprocess.check_output(["docker", "exec", "voltforge-ui", "cat", "/usr/share/nginx/html/assets/index-BKDRJYON.js"]).decode("utf-8", errors="ignore")
pos = 14500
print(out[pos:pos+1500])
EOF
"""
run_remote_command(remote_cmd)
