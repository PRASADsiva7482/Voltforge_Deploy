#!/usr/bin/env python3
"""
=============================================================================
VoltForge Unified Azure Deployment CLI
Supports targeted, fast zero-downtime deployment for:
  • UI (React Frontend)
  • BL (Spring Boot Backend)
  • AI (Python FastAPI Microservice)
  • All services simultaneously
=============================================================================
Usage:
  python azureDeploy/scripts/deploy.py --ui          # Deploy UI changes (~10s)
  python azureDeploy/scripts/deploy.py --bl          # Deploy Backend Java changes
  python azureDeploy/scripts/deploy.py --ai          # Deploy AI Python changes (~5s)
  python azureDeploy/scripts/deploy.py --config      # Deploy config files (application.yml, ai.env, config.js)
  python azureDeploy/scripts/deploy.py --all         # Full deployment (syncs everything & rebuilds)
  python azureDeploy/scripts/deploy.py --status      # Check status of all containers
=============================================================================
"""

import os
import sys
import tarfile
import subprocess
import argparse
import paramiko

# Default connection settings
DEFAULT_HOST = os.getenv("AZURE_VM_HOST", "4.154.189.115")
DEFAULT_USER = os.getenv("AZURE_VM_USER", "azureuser")
DEFAULT_PASSWORD = os.getenv("AZURE_VM_PASSWORD", "VoltForge@2026!")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AZURE_DEPLOY_DIR = os.path.join(ROOT_DIR, "azureDeploy")
UI_DIR = os.path.join(ROOT_DIR, "Voltforge_UI")
BL_DIR = os.path.join(ROOT_DIR, "Voltforge_BL")
AI_DIR = os.path.join(ROOT_DIR, "Voltforge_AI")


def get_ssh_client(host, user, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    return ssh


def run_remote_commands(ssh, commands, label="Remote execution"):
    print(f"[*] {label} on Azure VM...")
    stdin, stdout, stderr = ssh.exec_command(commands)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", "ignore")
    err = stderr.read().decode("utf-8", "ignore")
    if exit_status != 0:
        print(f"[!] Remote execution failed (code {exit_status}):\n{err}\n{out}")
        return False, out, err
    return True, out, err


# ── UI Deployment ─────────────────────────────────────────────────────────────
def deploy_ui(ssh, sftp, skip_build=False):
    print("\n" + "=" * 60)
    print("  [*] Deploying VoltForge UI (React)")
    print("=" * 60)

    dist_dir = os.path.join(UI_DIR, "dist")
    tar_path = os.path.join(AZURE_DEPLOY_DIR, "ui-dist.tar.gz")

    if not skip_build:
        print("[1/3] Building UI (npm run build)...")
        res = subprocess.run("npm run build", cwd=UI_DIR, shell=True)
        if res.returncode != 0:
            print("[!] UI build failed. Aborting.")
            return False
    else:
        print("[1/3] Skipping build step (using existing dist/)...")

    print("[2/3] Compressing dist package...")
    with tarfile.open(tar_path, "w:gz") as tar:
        for item in os.listdir(dist_dir):
            tar.add(os.path.join(dist_dir, item), arcname=item)
    print(f"  [+] Package size: {round(os.path.getsize(tar_path) / 1024, 1)} KB")

    print("[3/3] Uploading and hot-swapping on Azure VM...")
    sftp.put(tar_path, "/tmp/ui-dist.tar.gz")

    remote_cmds = """
set -e
rm -rf /tmp/ui-dist-unpack && mkdir -p /tmp/ui-dist-unpack
tar -xzf /tmp/ui-dist.tar.gz -C /tmp/ui-dist-unpack
rm -f /tmp/ui-dist-unpack/config.js

# Hot-swap files in container
docker cp /tmp/ui-dist-unpack/. voltforge-ui:/usr/share/nginx/html/
docker exec voltforge-ui nginx -s reload

# Persist to host
mkdir -p /opt/voltforge/Voltforge_UI/dist
cp -r /tmp/ui-dist-unpack/* /opt/voltforge/Voltforge_UI/dist/ 2>/dev/null || true
rm -rf /tmp/ui-dist-unpack /tmp/ui-dist.tar.gz
"""
    success, out, err = run_remote_commands(ssh, remote_cmds, "Updating voltforge-ui container")
    if success:
        print("[+] UI successfully deployed! URL: https://voltforge-lkc7bzuikvaz2.westus2.cloudapp.azure.com/")
    return success


# ── Backend (BL) Deployment ───────────────────────────────────────────────────
def deploy_bl(ssh, sftp):
    print("\n" + "=" * 60)
    print("  [*] Deploying VoltForge Backend (BL - Spring Boot)")
    print("=" * 60)

    tar_path = os.path.join(AZURE_DEPLOY_DIR, "bl-src.tar.gz")
    print("[1/3] Packaging Voltforge_BL source code (src + pom.xml)...")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(os.path.join(BL_DIR, "pom.xml"), arcname="pom.xml")
        tar.add(os.path.join(BL_DIR, "src"), arcname="src")
    print(f"  [+] Package size: {round(os.path.getsize(tar_path) / 1024, 1)} KB")

    print("[2/3] Uploading source to Azure VM...")
    sftp.put(tar_path, "/tmp/bl-src.tar.gz")

    # Also upload current application.yml
    app_yml = os.path.join(AZURE_DEPLOY_DIR, "config", "application.yml")
    sftp.put(app_yml, "/opt/voltforge/azureDeploy/config/application.yml")

    print("[3/3] Building and restarting voltforge-bl container on VM...")
    remote_cmds = """
set -e
mkdir -p /opt/voltforge/Voltforge_BL
tar -xzf /tmp/bl-src.tar.gz -C /opt/voltforge/Voltforge_BL/
rm -f /tmp/bl-src.tar.gz

cd /opt/voltforge/azureDeploy
docker compose build voltforge-bl
docker compose up -d voltforge-bl
"""
    success, out, err = run_remote_commands(ssh, remote_cmds, "Building and restarting voltforge-bl")
    if success:
        print("[+] Backend (BL) successfully built and deployed!")
    return success


# ── AI Deployment ─────────────────────────────────────────────────────────────
def deploy_ai(ssh, sftp):
    print("\n" + "=" * 60)
    print("  [*] Deploying VoltForge AI Microservice (Python FastAPI)")
    print("=" * 60)

    tar_path = os.path.join(AZURE_DEPLOY_DIR, "ai-src.tar.gz")
    print("[1/3] Packaging Voltforge_AI source code...")
    
    exclude_dirs = {'__pycache__', '.pytest_cache', '.venv', '.git'}
    exclude_exts = {'.npz', '.pt', '.bin', '.pyc'}

    with tarfile.open(tar_path, "w:gz") as tar:
        for root, dirs, files in os.walk(AI_DIR):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if any(f.endswith(ext) for ext in exclude_exts):
                    continue
                abs_f = os.path.join(root, f)
                rel_f = os.path.relpath(abs_f, AI_DIR)
                tar.add(abs_f, arcname=rel_f)
    print(f"  [+] Package size: {round(os.path.getsize(tar_path) / 1024, 1)} KB")

    print("[2/3] Uploading source to Azure VM...")
    sftp.put(tar_path, "/tmp/ai-src.tar.gz")

    # Also upload ai.env
    ai_env = os.path.join(AZURE_DEPLOY_DIR, "config", "ai.env")
    if os.path.exists(ai_env):
        sftp.put(ai_env, "/opt/voltforge/azureDeploy/config/ai.env")

    print("[3/3] Rebuilding and restarting voltforge-ai container on VM...")
    remote_cmds = """
set -e
mkdir -p /opt/voltforge/Voltforge_AI
tar -xzf /tmp/ai-src.tar.gz -C /opt/voltforge/Voltforge_AI/
rm -f /tmp/ai-src.tar.gz

cd /opt/voltforge/azureDeploy
docker compose build voltforge-ai
docker compose up -d voltforge-ai
"""
    success, out, err = run_remote_commands(ssh, remote_cmds, "Building and restarting voltforge-ai")
    if success:
        print("[+] AI microservice successfully built and deployed!")
    return success


# ── Configuration Only Deployment ─────────────────────────────────────────────
def deploy_config(ssh, sftp):
    print("\n" + "=" * 60)
    print("  [*] Deploying Configuration Files (application.yml, config.js, ai.env, nginx.conf)")
    print("=" * 60)

    config_dir = os.path.join(AZURE_DEPLOY_DIR, "config")
    gateway_dir = os.path.join(AZURE_DEPLOY_DIR, "gateway")

    # Upload config files
    for fname in ["application.yml", "config.js", "ai.env", "keycloak.env"]:
        fpath = os.path.join(config_dir, fname)
        if os.path.exists(fpath):
            print(f"  -> Uploading config/{fname}...")
            sftp.put(fpath, f"/opt/voltforge/azureDeploy/config/{fname}")

    nginx_conf = os.path.join(gateway_dir, "nginx.conf")
    if os.path.exists(nginx_conf):
        print("  -> Uploading gateway/nginx.conf...")
        sftp.put(nginx_conf, "/opt/voltforge/azureDeploy/gateway/nginx.conf")

    compose_file = os.path.join(AZURE_DEPLOY_DIR, "docker-compose.yml")
    if os.path.exists(compose_file):
        print("  -> Uploading docker-compose.yml...")
        sftp.put(compose_file, "/opt/voltforge/azureDeploy/docker-compose.yml")

    print("[*] Applying configuration changes to containers...")
    remote_cmds = """
# 1. Update UI config.js live in container
docker cp /opt/voltforge/azureDeploy/config/config.js voltforge-ui:/usr/share/nginx/html/config.js

# 2. Reload Gateway Nginx
docker exec voltforge-gateway nginx -s reload

# 3. Restart BL and AI to pick up new application.yml and ai.env
docker restart voltforge-bl voltforge-ai
"""
    success, out, err = run_remote_commands(ssh, remote_cmds, "Applying configuration updates")
    if success:
        print("[+] All configurations applied and services restarted!")
    return success


# ── Container Status ──────────────────────────────────────────────────────────
def check_status(ssh):
    print("\n" + "=" * 60)
    print("  [*] VoltForge Production Container Status")
    print("=" * 60)
    cmd = 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
    success, out, err = run_remote_commands(ssh, cmd, "Querying container status")
    print(out)


# ── Tag Pull & Instant Rollback Deployment ───────────────────────────────────
def deploy_pull_tag(ssh, tag, service="all"):
    print("\n" + "=" * 60)
    print(f"  [*] Deploying GHCR Image Tag '{tag}' for Service: {service}")
    print("=" * 60)

    registry = "ghcr.io/prasadsiva7482"
    services_map = {
        "ui": ("voltforge-ui", "UI_IMAGE"),
        "bl": ("voltforge-bl", "BL_IMAGE"),
        "ai": ("voltforge-ai", "AI_IMAGE"),
    }

    if service == "all":
        targets = list(services_map.items())
    elif service in services_map:
        targets = [(service, services_map[service])]
    else:
        print(f"[!] Unknown service: {service}. Allowed: ui, bl, ai, all")
        return False

    remote_cmds = "set -e\ncd /opt/voltforge/azureDeploy\n"
    for s_name, (c_name, env_var) in targets:
        img = f"{registry}/{c_name}:{tag}"
        remote_cmds += f"""
echo "[*] Pulling {img}..."
docker pull {img}
export {env_var}="{img}"
docker compose up -d --no-deps {c_name}
"""
    success, out, err = run_remote_commands(ssh, remote_cmds, f"Deploying GHCR tag {tag}")
    if success:
        print(f"[+] Successfully deployed tag '{tag}' ({service}) to Azure VM!")
    return success


# ── Main CLI ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="VoltForge Unified Deployment Tool for Azure")
    parser.add_argument("--ui", action="store_true", help="Deploy Voltforge_UI (React SPA)")
    parser.add_argument("--skip-build", action="store_true", help="Skip npm build for UI (use existing dist)")
    parser.add_argument("--bl", action="store_true", help="Deploy Voltforge_BL (Spring Boot)")
    parser.add_argument("--ai", action="store_true", help="Deploy Voltforge_AI (Python FastAPI)")
    parser.add_argument("--config", action="store_true", help="Deploy configuration files only")
    parser.add_argument("--all", action="store_true", help="Deploy all services (UI, BL, AI, Config)")
    parser.add_argument("--status", action="store_true", help="Check status of all production containers")
    parser.add_argument("--pull-tag", type=str, help="Deploy/pull a pre-built image tag from GHCR (e.g. v1.0.0 or latest)")
    parser.add_argument("--rollback", type=str, help="Instant rollback to an earlier GHCR image tag (e.g. v1.0.0)")
    parser.add_argument("--tag-service", default="all", choices=["ui", "bl", "ai", "all"], help="Target service for --pull-tag or --rollback (default: all)")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Azure VM public IP / host")
    parser.add_argument("--user", default=DEFAULT_USER, help="SSH user")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="SSH password")

    args = parser.parse_args()

    # If no flags passed, show help
    if not (args.ui or args.bl or args.ai or args.config or args.all or args.status or args.pull_tag or args.rollback):
        parser.print_help()
        sys.exit(0)

    print(f"Connecting to Azure VM: {args.host} as {args.user}...")
    try:
        ssh = get_ssh_client(args.host, args.user, args.password)
        sftp = ssh.open_sftp()
    except Exception as e:
        print(f"[!] Failed to connect to Azure VM: {e}")
        sys.exit(1)

    try:
        if args.status:
            check_status(ssh)
        if args.pull_tag:
            deploy_pull_tag(ssh, args.pull_tag, service=args.tag_service)
        if args.rollback:
            deploy_pull_tag(ssh, args.rollback, service=args.tag_service)
        if args.all or args.config:
            deploy_config(ssh, sftp)
        if args.all or args.ui:
            deploy_ui(ssh, sftp, skip_build=args.skip_build)
        if args.all or args.ai:
            deploy_ai(ssh, sftp)
        if args.all or args.bl:
            deploy_bl(ssh, sftp)

        print("\n" + "=" * 60)
        print("  [+] Deployment completed successfully!")
        print("  -> Web App:        https://voltforge-lkc7bzuikvaz2.westus2.cloudapp.azure.com/")
        print("  -> Admin Console:  https://voltforge-lkc7bzuikvaz2.westus2.cloudapp.azure.com/admin/master/console/")
        print("=" * 60 + "\n")
    finally:
        sftp.close()
        ssh.close()


if __name__ == "__main__":
    main()
