# ⚡ VoltForge — Azure Docker Deployment Guide

This directory contains the self-contained deployment bundle for deploying the complete VoltForge platform to **Microsoft Azure** in the **`Voltforge`** resource group (`centralindia`).

---

## 🏗️ Architecture Overview

All services run inside a dedicated Azure Virtual Machine via Docker Compose, isolated inside an internal Docker network, and exposed through a single high-performance **Nginx Reverse Proxy Gateway** on port 80:

```
                      ┌────────────────────────────────────────┐
                      │    Internet (Public IP / Azure DNS)    │
                      └──────────────────┬─────────────────────┘
                                         │ Port 80
                                         ▼
                      ┌────────────────────────────────────────┐
                      │      Gateway (Nginx Reverse Proxy)     │
                      └────┬─────────────┬─────────────┬───────┘
                           │             │             │
        ┌──────────────────┼─────────────┼─────────────┼──────────────────┐
        │ /                │ /voltForge-app/           │ /voltForge-ai/   │ /(realms|admin)/
        ▼                  ▼                           ▼                  ▼
┌───────────────┐  ┌───────────────┐           ┌───────────────┐  ┌───────────────┐
│ Voltforge_UI  │  │ Voltforge_BL  │           │ Voltforge_AI  │  │   Keycloak    │
│ (React/Vite)  │  │ (Spring Boot) │           │   (FastAPI)   │  │  (Identity)   │
└───────────────┘  └───────┬───────┘           └───────────────┘  └───────┬───────┘
                           │                                              │
                           ▼                                              ▼
                 [ Aiven MySQL Cloud ]                           [ Postgres Container ]
```

---

## 🚀 Quick Deployment Guide (Using Azure Cloud Shell)

Because your Azure account is already logged in inside the browser, you can deploy in **3 quick steps**:

### Step 1: Open Azure Cloud Shell
1. Go to your active [Azure Portal](https://portal.azure.com).
2. Click the **Cloud Shell (`>_`)** icon in the top right navigation bar.
3. Select **Bash** if prompted.

### Step 2: Run the VM Provisioning Script
In the Cloud Shell terminal, paste and run:

```bash
# Download and execute the provisioning script
curl -sSL -o provision-azure-vm.sh https://raw.githubusercontent.com/PRASADsiva7482/Voltforge_BL/feature/ai/azureDeploy/scripts/provision-azure-vm.sh 2>/dev/null || cat << 'EOF' > provision-azure-vm.sh
EOF
```

*(Alternatively, upload `azureDeploy/scripts/provision-azure-vm.sh` directly using the Cloud Shell Upload button `[↑]`)*

Then run:
```bash
chmod +x provision-azure-vm.sh
./provision-azure-vm.sh
```

**What this does automatically:**
- Verifies resource group `Voltforge` in `centralindia`
- Configures Network Security Group (`voltforge-nsg`) with firewall rules (ports 80, 443, 22)
- Allocates a static Public IP with a global Azure DNS domain (`http://voltforge-<id>.centralindia.cloudapp.azure.com`)
- Provisions an Ubuntu 22.04 VM (`Standard_B2ms`)
- Automatically installs Docker Engine and Docker Compose via Cloud-Init

---

### Step 3: Deploy the Container Stack
Once the VM finishes provisioning (typically ~90 seconds), SSH into the VM:

```bash
ssh azureuser@<YOUR_VM_PUBLIC_IP>
```

On your local machine, run the bundle script to create `voltforge-azure-bundle.zip`:
```powershell
powershell -ExecutionPolicy Bypass -File .\azureDeploy\scripts\bundle-for-azure.ps1
```

Copy the bundle to your VM:
```powershell
scp .\azureDeploy\voltforge-azure-bundle.zip azureuser@<YOUR_VM_PUBLIC_IP>:/opt/voltforge/
```

Inside the VM, unzip and launch:
```bash
cd /opt/voltforge
unzip -q voltforge-azure-bundle.zip
cd azureDeploy
chmod +x scripts/*.sh
./scripts/deploy-all.sh
```

---

## 🌐 Deployed Endpoints & Access

| Service | Access Path | Description |
| :--- | :--- | :--- |
| **Frontend Web App** | `http://<YOUR_DOMAIN_OR_IP>/` | VoltForge Canvas, Editor, Simulator |
| **Backend API Health** | `http://<YOUR_DOMAIN_OR_IP>/voltForge-app/actuator/health` | Spring Boot actuator status |
| **AI Microservice** | `http://<YOUR_DOMAIN_OR_IP>/voltForge-ai/health` | FastAPI healthcheck |
| **Keycloak Realm** | `http://<YOUR_DOMAIN_OR_IP>/realms/voltforge-realm/` | OIDC configuration endpoint |
| **Keycloak Admin** | `http://<YOUR_DOMAIN_OR_IP>/admin/` | Admin Console (`admin` / `Admin@123!`) |

---

## 🛠️ Deploying Changes to Azure (UI, Backend, AI, Config)

You can re-deploy any individual service or all services directly from your laptop using the unified deployment tool:

### 1. Unified Deployment CLI (Fastest & Automated)

| Service to Update | PowerShell Command | Python Command | What It Does |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | `.\azureDeploy\scripts\deploy.ps1 -UI` | `python azureDeploy/scripts/deploy.py --ui` | Builds UI locally, uploads ~470 KB bundle, hot-swaps assets in Nginx container with **zero downtime (~10s)** |
| **Backend (BL)** | `.\azureDeploy\scripts\deploy.ps1 -BL` | `python azureDeploy/scripts/deploy.py --bl` | Packages `Voltforge_BL/src` & `pom.xml`, uploads, builds inside Maven container on VM, and restarts |
| **AI Microservice** | `.\azureDeploy\scripts\deploy.ps1 -AI` | `python azureDeploy/scripts/deploy.py --ai` | Syncs `Voltforge_AI` python code, rebuilds Docker container on VM (**~5s**) |
| **Configuration Only** | `.\azureDeploy\scripts\deploy.ps1 -Config` | `python azureDeploy/scripts/deploy.py --config` | Uploads `application.yml`, `config.js`, `ai.env`, `nginx.conf` and reloads services |
| **All Services** | `.\azureDeploy\scripts\deploy.ps1 -All` | `python azureDeploy/scripts/deploy.py --all` | Syncs and updates all services simultaneously |
| **Check Status** | `.\azureDeploy\scripts\deploy.ps1 -Status` | `python azureDeploy/scripts/deploy.py --status` | Queries the health and container statuses of all services |

---

### 2. Manual Step-by-Step Instructions (SSH / Docker)

If you prefer to perform deployments manually via SSH:

#### 🔹 Updating Backend (BL - Spring Boot)
1. **For configuration changes only (`application.yml`):**
   ```powershell
   scp azureDeploy/config/application.yml azureuser@4.154.189.115:/opt/voltforge/azureDeploy/config/
   ssh azureuser@4.154.189.115 "docker restart voltforge-bl"
   ```
2. **For Java source code changes (`src/` or `pom.xml`):**
   ```bash
   ssh azureuser@4.154.189.115
   cd /opt/voltforge/azureDeploy
   docker compose build voltforge-bl
   docker compose up -d voltforge-bl
   docker logs -f voltforge-bl
   ```

#### 🔹 Updating AI Microservice (Python FastAPI)
1. **For environment variable changes (`ai.env`):**
   ```powershell
   scp azureDeploy/config/ai.env azureuser@4.154.189.115:/opt/voltforge/azureDeploy/config/
   ssh azureuser@4.154.189.115 "docker restart voltforge-ai"
   ```
2. **For Python code changes (`Voltforge_AI/`):**
   ```bash
   ssh azureuser@4.154.189.115
   cd /opt/voltforge/azureDeploy
   docker compose build voltforge-ai
   docker compose up -d voltforge-ai
   docker logs -f voltforge-ai
   ```

#### 🔹 Updating Frontend UI (React / Vite)
1. **Build locally and hot-swap:**
   ```powershell
   cd Voltforge_UI
   npm run build
   cd dist
   tar -czf ..\..\azureDeploy\ui-dist.tar.gz .
   scp ..\..\azureDeploy\ui-dist.tar.gz azureuser@4.154.189.115:/tmp/
   ```
2. **Apply in container on VM:**
   ```bash
   ssh azureuser@4.154.189.115
   rm -rf /tmp/ui-dist && mkdir -p /tmp/ui-dist
   tar -xzf /tmp/ui-dist.tar.gz -C /tmp/ui-dist
   rm -f /tmp/ui-dist/config.js
   docker cp /tmp/ui-dist/. voltforge-ui:/usr/share/nginx/html/
   docker exec voltforge-ui nginx -s reload
   ```

---

## 🛠️ Operations & Troubleshooting

Inside the VM in `/opt/voltforge/azureDeploy`:
- **Check Status**: `docker compose ps`
- **View All Logs**: `docker compose logs -f`
- **View Backend Logs**: `docker compose logs -f voltforge-bl`
- **View AI Logs**: `docker compose logs -f voltforge-ai`
- **View Keycloak Logs**: `docker compose logs -f keycloak`
- **View Gateway Logs**: `docker compose logs -f gateway`
- **Restart All**: `docker compose restart`
- **Stop All**: `docker compose down`

