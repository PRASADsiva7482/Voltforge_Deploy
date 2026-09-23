#!/usr/bin/env bash
# =============================================================================
# VoltForge — Status and Health Check Script
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
cd "$DEPLOY_DIR"

echo "=========================================================="
echo "          VoltForge Stack Status                          "
echo "=========================================================="
docker compose ps

echo ""
echo "=========================================================="
echo "          Container Resource Usage                        "
echo "=========================================================="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo ""
echo "=========================================================="
echo "          Endpoint Checks                                 "
echo "=========================================================="
check_endpoint() {
    local name="$1"
    local url="$2"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "FAILED")
    if [[ "$code" == "200" || "$code" == "302" || "$code" == "204" ]]; then
        echo "[+] $name: HTTP $code ($url)"
    else
        echo "[-] $name: HTTP $code ($url)"
    fi
}

check_endpoint "Gateway Health"    "http://127.0.0.1:80/healthz"
check_endpoint "Frontend UI"       "http://127.0.0.1:80/"
check_endpoint "Backend Health"    "http://127.0.0.1:80/voltForge-app/actuator/health"
check_endpoint "AI Microservice"   "http://127.0.0.1:80/voltForge-ai/health"
check_endpoint "Keycloak Realm"    "http://127.0.0.1:80/realms/voltforge-realm/"
