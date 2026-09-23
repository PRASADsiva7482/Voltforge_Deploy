#!/usr/bin/env python3
"""
VoltForge UI — Fast Deployment Script
Builds the UI locally (or uses existing dist) and deploys directly to the Azure VM in ~10 seconds.
"""

import os
import sys
import tarfile
import subprocess
import argparse
import paramiko

# Default connection settings (externalized/configurable)
DEFAULT_HOST = os.getenv("AZURE_VM_HOST", "4.154.189.115")
DEFAULT_USER = os.getenv("AZURE_VM_USER", "azureuser")
DEFAULT_PASSWORD = os.getenv("AZURE_VM_PASSWORD", "VoltForge@2026!")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UI_DIR = os.path.join(ROOT_DIR, "Voltforge_UI")
DIST_DIR = os.path.join(UI_DIR, "dist")
TAR_PATH = os.path.join(ROOT_DIR, "azureDeploy", "ui-dist.tar.gz")


def build_ui():
    print("[1/4] Building VoltForge UI (npm run build)...")
    cmd = "npm run build"
    result = subprocess.run(cmd, cwd=UI_DIR, shell=True)
    if result.returncode != 0:
        print("[!] Error: UI build failed. Aborting deployment.")
        sys.exit(1)
    print("  [+] UI build completed successfully.")


def package_dist():
    print(f"[2/4] Packaging {DIST_DIR} into {TAR_PATH}...")
    if not os.path.exists(DIST_DIR):
        print(f"[!] Error: {DIST_DIR} does not exist. Run build first.")
        sys.exit(1)

    with tarfile.open(TAR_PATH, "w:gz") as tar:
        for item in os.listdir(DIST_DIR):
            item_path = os.path.join(DIST_DIR, item)
            tar.add(item_path, arcname=item)
    
    size_kb = round(os.path.getsize(TAR_PATH) / 1024, 1)
    print(f"  [+] Compressed bundle created: {size_kb} KB")


def deploy_to_azure(host, user, password):
    print(f"[3/4] Uploading to Azure VM ({host})...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    sftp = ssh.open_sftp()
    remote_tar = "/tmp/ui-dist.tar.gz"
    sftp.put(TAR_PATH, remote_tar)
    sftp.close()
    print("  [+] Upload complete.")

    print("[4/4] Updating running UI container on Azure VM...")
    remote_cmds = """
set -e
rm -rf /tmp/ui-dist-unpack && mkdir -p /tmp/ui-dist-unpack
tar -xzf /tmp/ui-dist.tar.gz -C /tmp/ui-dist-unpack

# 1. Update running container (exclude config.js as it is bind-mounted)
rm -f /tmp/ui-dist-unpack/config.js
docker cp /tmp/ui-dist-unpack/. voltforge-ui:/usr/share/nginx/html/

# 3. Reload Nginx without downtime
docker exec voltforge-ui nginx -s reload

# 4. Also update host files for persistence
mkdir -p /opt/voltforge/Voltforge_UI/dist
cp -r /tmp/ui-dist-unpack/* /opt/voltforge/Voltforge_UI/dist/ 2>/dev/null || true

rm -rf /tmp/ui-dist-unpack /tmp/ui-dist.tar.gz
echo "SUCCESS"
"""
    stdin, stdout, stderr = ssh.exec_command(remote_cmds)
    output = stdout.read().decode("utf-8", "ignore")
    errors = stderr.read().decode("utf-8", "ignore")
    ssh.close()

    if "SUCCESS" in output:
        print("\n" + "=" * 60)
        print("  [+] VoltForge UI deployed successfully to Azure!")
        print("  -> Live URL: https://voltforge-lkc7bzuikvaz2.westus2.cloudapp.azure.com/")
        print("=" * 60 + "\n")
    else:
        print(f"[!] Deployment encountered issues:\n{errors}\n{output}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Deploy VoltForge UI to Azure VM")
    parser.add_argument("--skip-build", action="store_true", help="Skip npm run build and use existing dist")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Azure VM public IP / host")
    parser.add_argument("--user", default=DEFAULT_USER, help="SSH user")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="SSH password")
    args = parser.parse_args()

    if not args.skip_build:
        build_ui()
    else:
        print("[*] Skipping build step (using existing dist folder)...")

    package_dist()
    deploy_to_azure(args.host, args.user, args.password)


if __name__ == "__main__":
    main()
