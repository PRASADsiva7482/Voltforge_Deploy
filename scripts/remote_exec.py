import paramiko
import sys
import time
import os

VM_HOST = "4.154.189.115"
VM_USER = "azureuser"
VM_PASS = "VoltForge@2026!"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(VM_HOST, port=22, username=VM_USER, password=VM_PASS, timeout=30)
    return client

def run_remote_command(cmd, sudo=False):
    client = get_ssh_client()
    try:
        if sudo:
            cmd = f"echo '{VM_PASS}' | sudo -S {cmd}"
        print(f"--- RUNNING: {cmd} ---")
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        for line in iter(stdout.readline, ""):
            safe_line = line.encode("ascii", errors="replace").decode("ascii")
            print(safe_line, end="")
        exit_status = stdout.channel.recv_exit_status()
        print(f"\n--- EXIT CODE: {exit_status} ---")
        return exit_status
    finally:
        client.close()

def upload_file(local_path, remote_path):
    print(f"Uploading {local_path} -> {remote_path}...")
    client = get_ssh_client()
    try:
        sftp = client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        print("Upload complete!")
    finally:
        client.close()

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "status":
        run_remote_command("uptime && free -h && df -h && docker --version 2>&1")
    elif action == "cloud_init_status":
        run_remote_command("cloud-init status && tail -n 20 /var/log/cloud-init-output.log", sudo=True)
    elif action == "upload":
        local_zip = r"d:\Project\voltforge\azureDeploy\voltforge-azure-bundle.zip"
        upload_file(local_zip, "/home/azureuser/voltforge-azure-bundle.zip")
    elif action == "grant_privileges":
        cmd = 'docker run --rm mysql:8.0 mysql -hmysql-voltforge-prod-001.mysql.database.azure.com -uvfadmin -p"P@ssw0rd1234!" --ssl-mode=REQUIRED -e "GRANT SESSION_VARIABLES_ADMIN, SYSTEM_VARIABLES_ADMIN ON *.* TO \'voltadmin\'@\'%\'; FLUSH PRIVILEGES;"'
        run_remote_command(cmd)
    elif action == "exec":
        cmd = " ".join(sys.argv[2:])
        run_remote_command(cmd)
