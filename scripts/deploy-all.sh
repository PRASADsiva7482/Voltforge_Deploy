#!/usr/bin/env bash
# =============================================================================
# VoltForge — All Services Deployment Script
# Run inside VM in /opt/voltforge/azureDeploy
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
cd "$DEPLOY_DIR"

echo "=========================================================="
echo "          Starting VoltForge Docker Deployment            "
echo "=========================================================="

# 1. Verify Docker installation
if ! command -v docker >/dev/null 2>&1; then
    echo "[!] Docker is not installed yet. Waiting for cloud-init to finish..."
    sleep 15
fi

# 2. Build application containers in parallel
echo "[1/3] Building VoltForge application containers..."
docker compose build --parallel

# 3. Start Keycloak first (connected to Azure Database for MySQL)
echo "[2/3] Starting Keycloak Identity Server..."
docker compose up -d keycloak
echo "[*] Allowing Keycloak 15 seconds to initialize and import realm..."
sleep 15

# 4. Start all remaining services (AI, BL, UI, Gateway)
echo "[3/3] Starting AI Engine, Backend API, Frontend UI, and Gateway..."
docker compose up -d

# 5. Display status
echo ""
echo "=========================================================="
echo "          VoltForge Container Status                      "
echo "=========================================================="
docker compose ps

# 6. Verify HTTP endpoints
echo ""
echo "=========================================================="
echo "          Performing Endpoint Health Checks               "
echo "=========================================================="
for i in {1..12}; do
    if curl -sf http://127.0.0.1:80/healthz > /dev/null 2>&1; then
        echo "[+] Gateway is healthy (http://127.0.0.1:80/healthz)"
        break
    fi
    echo "[*] Waiting for gateway to respond... ($i/12)"
    sleep 5
done

echo ""
echo "=========================================================="
echo "          VoltForge Deployment Ready!                     "
echo "=========================================================="
echo "Access points (via Gateway port 80):"
echo "  • Frontend UI:    http://<VM_IP_OR_DOMAIN>/"
echo "  • Backend Health: http://<VM_IP_OR_DOMAIN>/voltForge-app/actuator/health"
echo "  • AI Health:      http://<VM_IP_OR_DOMAIN>/voltForge-ai/health"
echo "  • Keycloak:       http://<VM_IP_OR_DOMAIN>/realms/voltforge-realm/"
echo "  • Keycloak Admin: http://<VM_IP_OR_DOMAIN>/admin/ (admin / Admin@123!)"
echo "=========================================================="
